from base.models import Article, UserClassifier
from base.database import db_session

from skynet.nlp_util import gen_feature
from skynet.config import SCORE_DICT

import nltk

import cPickle

class Learner():
    def __init__(self, user_id):
        self.user_id = user_id

    def learn(self):
        last_1k_articles = (
            db_session
            .query(Article)
            .filter(Article.last_action != None)
            .filter_by(user_id=self.user_id)
            .order_by(Article.last_action_timestamp.desc())
            .limit(1250)
            .all()
        )

        if not last_1k_articles:
            return

        article_features = [
            (gen_feature(a), a.last_action) for a in last_1k_articles
        ]

        classifier = nltk.NaiveBayesClassifier.train(article_features)

        store = db_session.query(UserClassifier).filter_by(user_id=self.user_id).first()
        if not store:
            store = UserClassifier()
            store.user_id = self.user_id

        store.classifier = cPickle.dumps(classifier)
        db_session.add(store)

    def gen_priorscore(self, article):
        return SCORE_DICT[article.last_action]
