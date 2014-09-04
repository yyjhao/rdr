from datetime import datetime
import urllib2
import listparser
from flask import Flask, abort, request, redirect, jsonify
from base.database import db_session, init_db
from flask.ext import restful
from flask.ext.login import LoginManager, login_required, current_user
from dropbox.client import DropboxOAuth2Flow, DropboxClient

from api.model.user_auth import UserAuth
from base.sources import TwitterSource, RssSource
from api.util import crossdomain

from base.models import Source, Article, ALL_ACTIONS
from crawler.crawlers import Crawler

import base.config as config

from skynet.updater import Updater

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
    return jsonify(dict(error='unauthorized'))

@login_manager.request_loader
def load_user_from_request(request):
    token = request.values.get('token')
    if token:
        user = user_auth.verify_auth_token(token)
        if user:
            return user
    # finally, return None if both methods did not login the user
    return None

# routes

@app.route('/iframe_ok', methods=['GET', 'OPTIONS'])
@crossdomain(origin=config.FRONTEND_SERVER)
@login_required
def iframe_ok():
    url = request.values.get('url')
    print url
    if not url:
        return {}
    exrequest = urllib2.Request(url)  
    exrequest.add_header("Referer", "http://example.com") # you should put your real URL here  
    try:
        opener = urllib2.urlopen(exrequest)  
        # returns True if ANY x-frame-options header is present  
        # the only options at present are DENY and SAMEORIGIN, either of which means you can't frame  
        return jsonify({
            'iframe_ok': "x-frame-options" not in opener.headers.dict,
        })
    except:
        return jsonify({
            'iframe_ok': False,    
        })

@app.route('/import_opml', methods=['POST', 'OPTIONS'])
@crossdomain(origin=config.FRONTEND_SERVER)
@login_required
def import_opml():
    url = request.values.get('url')
    if not url:
        return {}
    d = listparser.parse(str(url))
    print d
    sources = []
    for f in d.feeds:
        source = RssSource.create_or_update(current_user, f.url)
        sources.append(source)
    for s in sources:
        if s:
            Crawler.crawl_for_source(s)
    sources = (
        db_session
        .query(Source)
        .filter_by(user_id=current_user.id)
        .all()
    )
    return jsonify({
        'sources': [s.serialize for s in sources]
    })

class SourceResource(restful.Resource):
    @login_required
    @crossdomain(origin=config.FRONTEND_SERVER)
    def get(self):
        sources = (
            db_session
            .query(Source)
            .filter_by(user_id=current_user.id)
            .all()
        )
        return jsonify({
            'sources': [s.serialize for s in sources]
        })

    @login_required
    @crossdomain(origin=config.FRONTEND_SERVER)
    def post(self):
        source_type = request.form['source_type']
        source = None
        if source_type == 'twitter':
            source = TwitterSource.create_or_update(current_user, request.form['token_json'])
        elif source_type == 'rss':
            source = RssSource.create_or_update(current_user, request.form['url'])

        if source:
            Crawler.crawl_for_source(source)
            sources = (
                db_session
                .query(Source)
                .filter_by(user_id=current_user.id)
                .all()
            )
            return jsonify({
                'sources': [s.serialize for s in sources]
            })
        else:
            return jsonify({
                'error': True
            })

    def options (self):
        return {'Allow' : 'POST' }, 200, {
            'Access-Control-Allow-Origin': config.FRONTEND_SERVER,
            'Access-Control-Allow-Methods' : 'POST,GET',
            'Access-Control-Allow-Headers': 'Origin, X-Requested-With, Content-Type, Accept',
        }


class ArticleResource(restful.Resource):
    @login_required
    @crossdomain(origin=config.FRONTEND_SERVER)
    def get(self):
        article_type = request.values.get('article_type')
        assert (article_type is None) or article_type in ALL_ACTIONS
        order = Article.score.desc()
        limit = 5
        if article_type == 'defer':
            order = Article.last_action_timestamp
            limit = None
        articles = (
            db_session
                .query(Article)
                .filter_by(user_id=current_user.id, last_action=article_type)
                .order_by(order)
                .limit(limit)
                .all()
            )
        return jsonify({
            'articles': [a.serialize for a in articles]
        })

    @login_required
    @crossdomain(origin=config.FRONTEND_SERVER)
    def post(self):
        article_id = request.form['article_id']
        action = request.form['action']
        print action, article_id
        if action not in ALL_ACTIONS:
            abort(400)
        article = (
            db_session
                .query(Article)
                .filter_by(id=article_id, user_id=current_user.id)
                .first()
            )
        if not article:
            abort(400)
        if article.last_action in ['like', 'dislike', 'pass']:
            abort(400)
        article.last_action = action
        article.last_action_timestamp = datetime.now()
        db_session.add(article)
        db_session.commit()

        updater = Updater(current_user.id)
        import thread
        def try_update():
            updater.update()
        thread.start_new_thread(try_update, ())

        return jsonify({
            'error': False
        })

    def options (self):
        return {'Allow' : 'POST' }, 200, {
            'Access-Control-Allow-Origin': config.FRONTEND_SERVER,
            'Access-Control-Allow-Methods' : 'POST,GET',
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
        return user;
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

