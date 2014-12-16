# -*- coding: utf-8 -*-

from sqlalchemy.exc import IntegrityError

from base.database.session import db_session
from base.database.models import Article, Origin, Url
from base.types.data import ArticleProto
import base.log as log
from crawler.url_util import normalize_url

from base.types.exceptions import DuplicatedEntryException

logger = log.get_logger('article processor')


def process(article_proto):
    return article_proto._replace(url=normalize_url(article_proto.url))


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

    # TODO: this doesn't guarantee no duplicate but the chance should be low for now
    if origin.id and url_row.id:
        if (
            db_session
            .query(Article)
            .filter_by(url_id=url_row.id, origin_id=origin.id)
            .first().title == article.title):
                raise DuplicatedEntryException("article is duplicated: " + str(article_proto))


def process_and_add_wrap(article_dict):
    process_and_add(ArticleProto(**article_dict))


def process_and_add(article_proto):
    article_proto = process(article_proto)
    article = to_db_entry(article_proto)

    try:
        update_relation(article, article_proto)
    except DuplicatedEntryException as e:
        logger.warning("article {0} from {1} duplocated, igored".format(article_proto.title, article_proto.source_id))
        return
    db_session.add(article)

    # shouldn't need to update the relation for more than 3 times
    # as only origin and url are involved
    for i in range(3):
        try:
            db_session.commit()
            return
        except IntegrityError as e:
            logger.warning("Race condition detected with origin {0} and url {1}".format(article_proto.origin, article_proto.url))
            db_session.rollback()
            try:
                update_relation(article, article_proto)
            except DuplicatedEntryException as e:
                logger.warning("article {0} from {1} duplocated, igored".format(article_proto.title, article_proto.source_id))
                return
            db_session.add(article)

    raise Exception("Failed to add article_proto: " + str(article_proto))


def get_or_create_origin(orig_id):
    origin = db_session.query(Origin).filter_by(identifier=orig_id).first()
    if not origin:
        origin = Origin()
        origin.identifier = orig_id
        db_session.add(origin)
    return origin


def get_or_create_url(url):
    url_row = db_session.query(Url).filter_by(url=url).first()
    if not url_row:
        url_row = Url()
        url_row.url = url
        db_session.add(url_row)
    return url_row
