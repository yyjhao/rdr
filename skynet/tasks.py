from base.types.user_url import WrappedUserUrl
from base.database.session import db_session
from base.database.models import UserSource, Article
from skynet.scorer import Scorer
from skynet.learner import Learner
from skynet.user_status import UserStatus
import base.log as log

logger = log.get_logger("ai_task")

def add_articles(user_ids, article_id, url_id, scorer=None):
    for u in user_ids:
        userurl = WrappedUserUrl.get_or_create(user_id=u, url_id=url_id)
        userurl.add_article(article_id)
        if scorer:
            scorer.score(userurl)
        userurl.save()


def add_articles_from_source(user_id, source_id, last_append_id, scorer=None):
    if not last_append_id:
        last_append_id = 0
    last_article = 0
    for i, url_id in (db_session.query(Article.id, Article.url_id)
                        .filter(Article.source_id==source_id)
                        .filter(Article.id>last_append_id)
                        .limit(300)
                        .all()):
        last_article = max(last_article, i)
        add_articles([user_id], i, url_id, scorer)
    return last_article


def add_articles_for_user(user_id):
    scorer = Scorer(user_id)
    for row in (db_session.query(UserSource)
                        .filter_by(user_id=user_id)
                        .all()):
                            last = add_articles_from_source(user_id, row.source_id, row.last_append_id, scorer)
                            row.last_append_id = last
                            db_session.add(row)
    db_session.commit()


def score_articles(user_id):
    Scorer(user_id).score_all()
    db_session.commit()


def score_new_articles(user_id):
    Scorer(user_id).score_new()
    db_session.commit()


def train(user_id):
    Learner(user_id).learn()
    db_session.commit()
    score_articles(user_id)


def serve_user(user_id):
    userstatus = UserStatus(user_id)
    status = userstatus.get_current_status()
    logger.info("User {0} is in status {1}".format(user_id, status))
    if status == 'train':
        userstatus.notify_training()
        train(user_id)
        return True
    elif status in ('idle', 'incoming'):
        userstatus.notify_scoring()
        add_articles_for_user(user_id)
        return True
    return False
