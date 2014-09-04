from sqlalchemy.exc import IntegrityError

from base.database import db_session
from base.models import Article
from crawler.url_util import normalize_url

articles = db_session.query(Article).filter(Article.id > 960)

for article in articles:
    url = article.url
    print article.id
    print url
    article.url = normalize_url(url)
    print article.url
    try:
        db_session.commit()
    except IntegrityError as e:
        db_session.rollback()
        db_session.delete(article)
        db_session.commit()
