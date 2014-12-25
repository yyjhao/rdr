from base.database.models import UserUrl, UserClassifier
from base.database.session import db_session
from base.types.user_url import WrappedUserUrl
from skynet.classifiers import SVMClassifier


class Learner():
    def __init__(self, user_id):
        self.user_id = user_id

    def get_training_set(self, action_type, num):
        return (
            db_session
            .query(UserUrl)
            .filter_by(user_id=self.user_id, last_action=action_type)
            .order_by(UserUrl.last_action_timestamp.desc())
            .limit(num)
            .all()
        )

    def learn(self):
        total_num = 2000

        training_set = []
        for t in ('like', 'dislike', 'defer', 'pass'):
            cur_set = self.get_training_set(t, int(total_num / 4) if t != 'pass' else (total_num - len(training_set)))
            for uu in cur_set:
                training_set.append(WrappedUserUrl(uu))

        if not training_set:
            return

        classifier = SVMClassifier()
        classifier.train(training_set)

        store = db_session.query(UserClassifier).filter_by(user_id=self.user_id).first()
        if not store:
            store = UserClassifier()
            store.user_id = self.user_id

        store.classifier = classifier.dumps()
        db_session.add(store)
