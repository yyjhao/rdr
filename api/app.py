from datetime import datetime
from flask import Flask, abort, request, redirect, jsonify
from flask.ext import restful
from flask.ext.login import LoginManager, login_required, current_user

from api.model.user_auth import UserAuth
from api.util import crossdomain

from base.types.sources import WrappedSource
from base.types.user_url import WrappedUserUrl
from base.database.models import ALL_ACTIONS
from base.database.session import db_session, init_db
from skynet.user_status import UserStatus
from api.tasks import user_add_rss, user_add_twitter, import_opml_url
from worker.async_task import async, query_task

import base.config as config

app = Flask(__name__)
api = restful.Api(app)
user_auth = UserAuth(app)

# db

init_db()


@app.teardown_appcontext
def shutdown_session(exception=None):
    db_session.remove()

# auth

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify(error='unauthorized')


class FakeUser():
    def __init__(self):
        self.id = 1

    def is_authenticated(self):
        return True

dummy = FakeUser()


@login_manager.request_loader
def load_user_from_request(request):
    return dummy
    token = request.values.get('token')
    if token:
        user = user_auth.verify_auth_token(token)
        if user:
            return user
    # finally, return None if both methods did not login the user
    return None


# routes
@app.route('/import_opml', methods=['POST', 'OPTIONS'])
@crossdomain(origin=config.FRONTEND_SERVER)
@login_required
def import_opml():
    url = request.values.get('url')

    if not url:
        abort(422)

    return async(import_opml_url, (url,))


class AsyncTaskQuery(restful.Resource):
    @login_required
    @crossdomain(origin=config.FRONTEND_SERVER)
    def get(self):
        tid = request.values.get('task')
        status, result = query_task(tid)
        if status != b'done':
            return jsonify(working=True)
        elif result[0]:
            if current_user.id != result[0]:
                return jsonify(working=True)
            else:
                return jsonify(result=result[1])


class SourceResource(restful.Resource):
    @login_required
    @crossdomain(origin=config.FRONTEND_SERVER)
    def get(self):
        sources = WrappedSource.get_for_user(current_user.id)
        return jsonify(sources=[s.to_dict() for s in sources])

    @login_required
    @crossdomain(origin=config.FRONTEND_SERVER)
    def post(self):
        source_type = request.form['source_type']
        source = None
        if source_type == 'twitter':
            return jsonify(task=async(user_add_twitter, (current_user.id, request.form['token'], request.form['token_secret'])))
        elif source_type == 'rss':
            source = WrappedSource.get_with_ext_id(request.form['url'])
            if not source:
                return jsonify(task=async(user_add_rss, (current_user.id, request.form['url'])))
            else:
                source.add_to_user(current_user.id)
                return jsonify(error=False)

    def options(self):
        return {'Allow': 'POST'}, 200, {
            'Access-Control-Allow-Origin': config.FRONTEND_SERVER,
            'Access-Control-Allow-Methods': 'POST,GET',
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept',
        }


class ArticleResource(restful.Resource):
    @login_required
    @crossdomain(origin=config.FRONTEND_SERVER)
    def get(self):
        action_type = request.values.get('action_type')
        assert (action_type is None) or action_type in ALL_ACTIONS
        if action_type == 'defer':
            uus = WrappedUserUrl.get_for_user(user_id=current_user.id, action_type=action_type, order_by='time')
        else:
            uus = WrappedUserUrl.get_for_user(user_id=current_user.id, action_type=action_type, limit=5, order_by='score')
        return jsonify({
            'items': [uu.to_dict() for uu in uus]
        })

    @login_required
    @crossdomain(origin=config.FRONTEND_SERVER)
    def post(self):
        article_id = request.form['article_id']
        action = request.form['action']
        if action not in ALL_ACTIONS:
            abort(400)
        uu = WrappedUserUrl.get(article_id)
        if not uu or uu.user_id != current_user.user_id:
            abort(400)
        if uu.last_action in ['like', 'dislike', 'pass']:
            abort(400)
        uu.last_action = action
        uu.last_action_timestamp = datetime.now()
        uu.save()

        UserStatus(current_user.id).notify_user_action()

        return jsonify(error=False)

    def options(self):
        return {'Allow': 'POST'}, 200, {
            'Access-Control-Allow-Origin': config.FRONTEND_SERVER,
            'Access-Control-Allow-Methods': 'POST,GET',
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept',
        }

# auth
@app.route('/auth', methods=['GET', 'OPTIONS'])
@login_required
@crossdomain(origin=config.FRONTEND_SERVER)
def auth():
    return jsonify({
        'user': current_user.serialize,
        'error': 0
    })

def load_user_from_dropbox(request):
    token = request.form['token']
    if not token:
        return None
    user = user_auth.auth_with_ext_token(token)
    if user:
        return user
    else:
        return None

@app.route('/auth_with_dropbox', methods=['POST'])
def auth_with_dropbox():
    user = load_user_from_dropbox(request)
    if user:
        return user_auth.generate_auth_token(user)
    else:
        return unauthorized()

api.add_resource(SourceResource, '/source')
api.add_resource(ArticleResource, '/article')
api.add_resource(AsyncTaskQuery, '/task')

