from base.types.user_url import WrappedUserUrl
from base.database.session import db_session
from base.database.models import user_source, Article
from worker.task_queue import get_queue
from skynet.scorer import Scorer


# def add_articles(user_id):
#     for row in db_session.query(user_source).filter(user_id==user_id).all():
#         add_articles_from_source(user_id, row.source_id, row.last_append_id)
#     get_queue().add_task(add_articles, (user_id,), delay=900, renew=True)

def add_articles(user_ids, article_id, url_id):
    for u in user_ids:
        userurl = WrappedUserUrl.get_or_create(user_id=u, url_id=url_id)
        userurl.add_article(article_id)
        userurl.save()


def add_articles_from_source(user_id, source_id, last_append_id):
    if not last_append_id:
        last_append_id = 0
    for i, url_id in (db_session.query(Article.id, Article.url_id)
                        .filter(Article.source_id==source_id)
                        .filter(Article.id>last_append_id)
                        .all()):
        userurl = WrappedUserUrl.get_or_create(user_id=user_id, url_id=url_id)
        userurl.add_article(i)
        userurl.save()


def score_articles(user_id):
    Scorer(user_id).score_all()


def train(user_id):
    pass