from skynet.scorer import Scorer
from base.database import db_session

Scorer(1).score_all()
db_session.commit()