from base.database.models import UserClassifier
from base.types.user_url import WrappedUserUrl
from base.database.session import db_session

from skynet.config import SCORE_DICT, MAX_SCORE
from skynet.classifiers import SVMClassifier

import random
import base.log as log

logger = log.get_logger('scorer')


class Scorer():
    def __init__(self, user_id):
        self.user_id = user_id
        db_entry = db_session.query(UserClassifier).filter_by(user_id=user_id).first()
        if db_entry and db_entry.classifier:
            self.classifier = SVMClassifier.loads(
                db_session.query(UserClassifier).filter_by(user_id=user_id).first().classifier
            )
        else:
            logger.info("User {0} does not have trained classifier.".format(user_id))
            self.classifier = None

    def score_all(self):
        for uu in WrappedUserUrl.get_for_user(self.user_id):
            self.score(uu)

    def score_new(self):
        for uu in WrappedUserUrl.get_for_user(self.user_id, only_unscored=True):
            self.score(uu)

    def score(self, user_url):
        if self.classifier:
            ml_score = self.gen_predictive_score(self.classifier.prob_classify(user_url))
            user_url.score = int(ml_score * MAX_SCORE)
        else:
            user_url.score = int(random.uniform(-1, 1) * MAX_SCORE)

    def gen_predictive_score(self, prob_dist):
        return sum(
            p * SCORE_DICT[s] for s, p in prob_dist.items()
        )
