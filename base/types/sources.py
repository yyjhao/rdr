from twitter import Twitter, OAuth
import json
import feedparser
from sqlalchemy.exc import IntegrityError

from base.database.models import Source, user_source
from base.database.session import db_session
import base.config as config


class WrappedSource(object):

    def __init__(self, db_entry):
        self._source = db_entry
        super(WrappedSource, self).__init__()

    @staticmethod
    def get(id):
        return WrappedSource.init_with_entry(db_session.query(Source).filter_by(id=id).first())

    @staticmethod
    def get_all():
        for entry in db_session.query(Source).all():
            yield WrappedSource.init_with_entry(entry)

    @staticmethod
    def init_with_entry(entry):
        if entry.type == 'twitter':
            return TwitterSource(entry)
        elif entry.type == 'rss':
            return RssSource(entry)

    @classmethod
    def get_or_create(cls, source):
        db_session.add(source)
        try:
            db_session.commit()
            return cls(source)
        except IntegrityError as e:
            db_session.rollback()
            return cls(
                db_session
                .query(Source)
                .filter_by(ext_uid=source.ext_uid, type=cls.get_type())
                .first()
            )

    @classmethod
    def get_type(cls):
        raise NotImplementedError()

    @classmethod
    def create_or_update(cls, *args):
        raise NotImplementedError()

    @property
    def user_id(self):
        return self._source.user_id

    @property
    def id(self):
        return self._source.id

    @property
    def last_retrive(self):
        return self._source.last_retrive

    @last_retrive.setter
    def last_retrive(self, val):
        self._source.last_retrive = val

    def should_add_article(self, article):
        if not article:
            return False
        if not self._source.last_retrive:
            return True
        return self._source.last_retrive < article.timestamp

    def add_to_user(self, user):
        db_session.execute(user_source.insert(), user_id=user.id, source_id=self.id)


class TwitterSource(WrappedSource):

    def __init__(self, db_entry):
        self.token = db_entry.info['token']
        self.token_secret = db_entry.info['token_secret']
        super(TwitterSource, self).__init__(db_entry)

    @classmethod
    def get_type(cls):
        return 'twitter'

    @classmethod
    def create_or_update(cls, token, token_secret):
        t = Twitter(
            auth=OAuth(token, token_secret,
                       config.TWITTER_KEY, config.TWITTER_SECRET)
        )
        info = t.account.verify_credentials()
        source = db_session.query(Source).filter_by(ext_uid=info[u'id_str'], type='twitter').first()
        if not source:
            source = Source()
            source.ext_uid = info['id_str']
            source.is_private = True
        source.info = {}
        source.info['name'] = info[u'screen_name']
        source.info['token'] = token
        source.info['token_secret'] = token_secret
        source.type = 'twitter'
        
        return cls.get_or_create(source)

    @property
    def since_id(self):
        return self._source.info['since_id']

    @since_id.setter
    def since_id(self, value):
        self._source.info['since_id'] = value
        db_session.add(self._source)


class RssSource(WrappedSource):

    def __init__(self, db_entry):
        super(RssSource, self).__init__(db_entry)

    @classmethod
    def get_type(cls):
        return 'rss'

    @classmethod
    def create_or_update(cls, url):
        source = (
            db_session
            .query(Source)
            .filter_by(ext_uid=url, type='rss')
            .first()
        )
        if not source:
            d = feedparser.parse(url)
            if not d.feed or not d.feed.get('title'):
                return None
            source = Source()
            source.ext_uid = url
            source.is_private = False
            source.info = {}
            source.info['url'] = url
            source.info['name'] = d.feed.title
            source.type = 'rss'
            return cls.get_or_create(source)
        return cls(source)
        

    @property
    def last_modified_indicator(self):
        return self._source.info.get('last_modified_indicator')

    @last_modified_indicator.setter
    def last_modified_indicator(self, value):
        self._source.last_indicator = value
        db_session.add(self._source)

    @property
    def url(self):
        return self._source.info['url']

    @property
    def name(self):
        return self._source.info['name']

