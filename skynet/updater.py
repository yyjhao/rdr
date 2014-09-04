from datetime import datetime, timedelta

from base.models import UserClassifier
from base.database import db_session
from skynet.learner import Learner
from skynet.scorer import Scorer


class Updater():
    def __init__(self, user_id):
        self.user_id = user_id

    def get_locked(self):
        latest = datetime.now() - timedelta(minutes=5)

        result = (
            db_session.query(UserClassifier)
            .filter(UserClassifier.locked < latest)
            .filter_by(user_id=self.user_id)
            .update({'locked': datetime.now()})
        )
        db_session.commit()

        return result

    def update(self):
        if self.get_locked():
            print 'updating skynet for {0}'.format(self.user_id)
            Learner(self.user_id).learn()
            Scorer(self.user_id).score_all()
            print 'skynet for {0} updated'.format(self.user_id)
        else:
            print 'skynet for {0} locked'.format(self.user_id)
