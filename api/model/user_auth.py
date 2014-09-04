from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired, BadSignature
import dropbox
from dropbox.rest import ErrorResponse

from base.models import User
from base.database import db_session
import base.config as config

class UserAuth():

    def __init__(self, app):
        self.app = app

    def create_or_update_user_info(self, info, token):
        ext_uid = info[u'uid']
        user = db_session.query(User).filter_by(ext_uid=ext_uid).first()
        if not user:
            print 'creating user'
            user = User()
            user.ext_uid = info[u'uid']
        user.name = info[u'display_name']
        user.email = info[u'email']
        user.auth_token = token
        db_session.add(user)
        db_session.commit()
        return user

    def generate_auth_token(self, user, expiration=1000000):
        s = Serializer(config.SECRET_KEY, expires_in = expiration)
        return s.dumps({ 'id': user.id })

    def auth_with_ext_token(self, token):
        client = dropbox.client.DropboxClient(token)
        try:
            info = client.account_info()
            return self.create_or_update_user_info(info, token)
        except ErrorResponse as e:
            print e
            return None

    def verify_auth_token(self, token):
        s = Serializer(config.SECRET_KEY)
        data = None
        try:
            data = s.loads(token)
        except (SignatureExpired, BadSignature):
            return None # invalid token
        user = db_session.query(User).filter_by(id=data['id']).first()
        return user
