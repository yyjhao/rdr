from skynet.learner import Learner
from base.database import db_session

Learner(1).learn()
db_session.commit()