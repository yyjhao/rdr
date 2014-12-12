from base.models import UserClassifier, Article
from base.database import db_session

from skynet.nlp_util import gen_feature
from skynet.config import SCORE_DICT, MAX_SCORE
from skynet.classifiers import NaiveBayesClassifier, SVMClassifier
import cPickle

class Scorer():
    def __init__(self, user_id):
        self.user_id = user_id
        # self.classifier = NaiveBayesClassifier.loads(
        self.classifier = SVMClassifier.loads(
            db_session.query(UserClassifier).filter_by(user_id=user_id).first().classifier
        )
        assert self.classifier, 'fail to load for user %s' % user_id

    def score_all(self):
        articles = db_session.query(Article).filter_by(user_id=self.user_id, last_action=None).all()
        for a in articles:
            self.score(a)
            db_session.add(a)
        db_session.commit()

    def score_new(self):
        articles = db_session.query(Article).filter_by(user_id=self.user_id, last_action=None, score=None).all()
        for a in articles:
            self.score(a)
            db_session.add(a)
        db_session.commit()

    def score(self, article):
        ml_score = self.gen_predictive_score(self.classifier.prob_classify(article))
        article.score = int(ml_score * MAX_SCORE)

    def gen_predictive_score(self, prob_dist):
        return sum(
            p * SCORE_DICT[s] for s, p in prob_dist.items()
        )