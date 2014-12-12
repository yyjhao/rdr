# -*- coding: utf-8 -*-

from sqlalchemy.exc import IntegrityError

from base.database import db_session
from base.models import Article, Origin, Url
from crawler.url_util import normalize_url


def process(article_proto):
    article_proto.url = normalize_url(article_proto.url)


def to_db_entry(article_proto):
    article = Article()

    article.title = article_proto.title
    article.timestamp = article_proto.timestamp
    article.summary = article_proto.summary

    return article


def update_relation(article, article_proto):
    origin = get_or_create_origin(article_proto.origin)
    origin.image_url = article_proto.origin_img
    origin.display_name = article_proto.origin_display_name

    url_row = get_or_create_url(article_proto.url)
    article.url = url_row
    article.origin = origin


def process_and_add(article_proto):
    process(article_proto)
    article = to_db_entry(article_proto)

    update_relation(article, article_proto)
    db_session.add(article)

    # shouldn't need to update the relation for more than 3 times
    # as only origin and url are involved
    for i in range(3):
        try:
            db_session.commit()
            return
        except IntegrityError as e:
            db_session.rollback()
            update_relation(article, article_proto)
            db_session.add(article)

    raise Exception("Failed to add article_proto: " + str(article_proto))


def get_or_create_origin(orig_id):
    origin = db_session.query(Origin).filter_by(identifier=orig_id).first()
    if not origin:
        origin = Origin()
        origin.identifier = orig_id
    return origin


def get_or_create_url(url):
    url_row = db_session.query(Url).filter_by(url=url).first()
    if not url_row:
        url_row = Url()
        url_row.url = url
    return url
