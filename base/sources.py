from twitter import Twitter, OAuth
import json
import feedparser

from base.models import Source
from base.database import db_session
import base.config as config

class WrappedSource(object):

    def __init__(self, db_entry):
        assert db_entry.type == self.get_type()
        self._source = db_entry
        super(WrappedSource, self).__init__()

    @staticmethod
    def get_for(model):
        if model.type == 'twitter':
            return TwitterSource(model)
        elif model.type == 'rss':
            return RssSource(model)

    @classmethod
    def get_type(cls):
        raise NotImplementedError()

    @classmethod
    def create_or_update(cls, user, token):
        raise NotImplementedError()

    @property
    def user_id(self):
        return self._source.user_id

    @property
    def id(self):
        return self._source.id

    @property
    def name(self):
        return self._source.name

class TwitterSource(WrappedSource):

    def __init__(self, db_entry):
        self.token, self.token_secret = json.loads(db_entry.token)
        super(TwitterSource, self).__init__(db_entry)

    @classmethod
    def get_type(cls):
        return 'twitter'

    @classmethod
    def create_or_update(cls, user, token_json):
        token, token_secret = json.loads(token_json)
        t = Twitter(
            auth=OAuth(token, token_secret,
                       config.TWITTER_KEY, config.TWITTER_SECRET)
        )
        info = t.account.verify_credentials()
        source = db_session.query(Source).filter_by(ext_uid=info[u'id_str'], user_id=user.id, type='twitter').first()
        if not source:
            source = Source()
            source.ext_uid = info['id_str']
            source.user_id = user.id
        source.name = info[u'screen_name']
        source.token = token_json
        source.type = 'twitter'
        db_session.add(source)
        db_session.commit()
        return source

    @property
    def since_id(self):
        return self._source.last_indicator

    @since_id.setter
    def since_id(self, value):
        self._source.last_indicator = str(value)
        db_session.add(self._source)
        db_session.commit()

class RssSource(WrappedSource):

    def __init__(self, db_entry):
        super(RssSource, self).__init__(db_entry)

    @classmethod
    def get_type(cls):
        return 'rss'

    @classmethod
    def create_or_update(cls, user, token):
        source = db_session.query(Source).filter_by(token=token, user_id=user.id, type='rss').first()
        if not source:
            d = feedparser.parse(token)
            if not d.feed or not d.feed.get('title'):
                return None
            source = Source()
            source.token = token
            source.type = 'rss'
            source.name = d.feed.title
            source.user_id = user.id
            db_session.add(source)
            db_session.commit()
        return source

    @property
    def last_modified_indicator(self):
        if self._source.last_indicator:
            return json.loads(self._source.last_indicator)
        else:
            return {}

    @last_modified_indicator.setter
    def last_modified_indicator(self, value):
        self._source.last_indicator = json.dumps(value)
        db_session.add(self._source)
        db_session.commit()

    @property
    def url(self):
        return self._source.token
    