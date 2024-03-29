from sqlalchemy.exc import IntegrityError

from base.database.models import Source, UserUrl
from base.database.session import db_session
from base.types.article import WrappedArticle


class WrappedUserUrl(object):

    def __init__(self, db_entry):
        self.db_entry = db_entry
        self.added_articles = set()
        super(WrappedUserUrl, self).__init__()

    @staticmethod
    def get_for_user(user_id, only_unscored=False, action_type=None, limit=0, order_by=None):
        query = db_session.query(UserUrl).filter_by(user_id=user_id, last_action=action_type)
        articles = []
        if only_unscored:
            query = query.filter_by(score=None)
        if order_by:
            if order_by == 'time':
                query = query.order_by(UserUrl.last_action_timestamp)
            elif order_by == 'score':
                query = query.order_by(UserUrl.score.desc())
        if limit:
            query = query.limit(limit)
        articles = query.all()
        for a in articles:
            yield WrappedUserUrl(a)

    @staticmethod
    def get(id):
        db_entry = UserUrl.get(id)
        return WrappedUserUrl(db_entry)

    @staticmethod
    def get_or_create(url_id, user_id):
        db_entry = (
            db_session.query(UserUrl)
            .filter(UserUrl.url_id==url_id)
            .filter(UserUrl.user_id==user_id)
            .first()
        )
        if not db_entry:
            db_entry = UserUrl(url_id=url_id, user_id=user_id, articles={})
            db_session.add(db_entry)
        return WrappedUserUrl(db_entry)

    def add_article(self, article_id):
        article_id = str(article_id)
        self.db_entry.articles[article_id] = ""
        self.added_articles.add(article_id)

    def save(self):
        try:
            db_session.commit()
        except IntegrityError as e:
            db_session.rollback()
            self.db_entry = db_session.query(UserUrl).filter(url_id=self.db_entry.url_id, user_id=self.db_entry.user_id).first()
            for a in self.added_articles:
                self.db_entry.articles[a] = ""
            db_session.commit()
        self.added_articles.clear()

    def get_articles(self):
        return WrappedArticle.get_multiple([int(i) for i in self.db_entry.articles.keys()])

    def to_dict(self):
        articles = self.get_articles()
        return {
            'articles': [a.to_dict() for a in articles],
            'score': self.score,
            'id': self.id,
            'url': articles[0].url,
        }

    @property
    def score(self):
        return self.db_entry.score
    @score.setter
    def score(self, value):
        self.db_entry.score = value

    @property
    def last_action(self):
        return self.db_entry.last_action
    @last_action.setter
    def last_action(self, value):
        self.db_entry.last_action = value

    @property
    def last_action_timestamp(self):
        return self.db_entry.last_action_timestamp
    @last_action_timestamp.setter
    def last_action_timestamp(self, value):
        self.db_entry.last_action_timestamp = value

    @property
    def id(self):
        return self.db_entry.id

    @property
    def user_id(self):
        return self.db_entry.user_id
    
