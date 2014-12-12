from base.models import Article, UserClassifier
from base.database import db_session

from skynet.nlp_util import gen_feature
from skynet.config import SCORE_DICT
from skynet.classifiers import NaiveBayesClassifier, SVMClassifier

import nltk

import cPickle

class Learner():
    def __init__(self, user_id):
        self.user_id = user_id


    def get_articles(self, article_type, num):
        return (
            db_session
            .query(Article)
            .filter_by(user_id=self.user_id, last_action=article_type)
            .order_by(Article.last_action_timestamp.desc())
            .limit(num)
            .all()
        )

    def learn(self):
        total_num = 2000

        training_articles = []
        for t in ('like', 'dislike', 'defer', 'pass'):
            training_articles += self.get_articles(t, int(total_num / 4) if t != 'pass' else (total_num - len(training_articles)))

        if not training_articles:
            return

        classifier = SVMClassifier()
        # classifier = NaiveBayesClassifier()
        classifier.train(training_articles)

        store = db_session.query(UserClassifier).filter_by(user_id=self.user_id).first()
        if not store:
            store = UserClassifier()
            store.user_id = self.user_id

        store.classifier = classifier.dumps()
        db_session.add(store)

