import json
import datetime
from namedlist import namedlist
from sqlalchemy.exc import IntegrityError

from base.database.session import db_session
from base.database.models import Article
from base.database.util import get_or_create_origin, get_or_create_url
import base.log as log
from crawler.url_util import normalize_url
from base.types.cachable import Cachable
from base.types.exceptions import DuplicatedEntryException

_ArticleProto = namedlist(
    '_ArticleProto',
    ['id', 'title', 'summary', 'url', 'timestamp', 'origin', 'image_url', 'source_id', 'origin_img', 'origin_display_name', 'time_unknown', 'origin_id', 'url_id'],
)

logger = log.get_logger('article processor')


class WrappedArticle(_ArticleProto, Cachable):
    cache_on_save = False

    @classmethod
    def get_key(cls, id):
        return "article:" + str(id)

    def serialize(self):
        return json.dumps({
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "url": self.url,
            "timestamp": self.timestamp.isoformat(),
            "origin": self.origin,
            "image_url": self.image_url,
            "source_id": self.source_id,
            "origin_img": self.origin_img,
            "origin_display_name": self.origin_display_name,
            "time_unknown": self.time_unknown,
            "origin_id": self.origin_id,
            "url_id": self.url_id,
        })

    @classmethod
    def deserialize(cls, string):
        d = json.loads(string)
        return cls(
            id=d["id"],
            title=d["title"],
            summary=d["summary"],
            url=d["url"],
            timestamp=datetime.datetime.strptime(d["timestamp"], "%Y-%m-%dT%H:%M:%S"),
            origin=d["origin"],
            image_url=d["image_url"],
            source_id=d["source_id"],
            origin_img=d["origin_img"],
            origin_display_name=d["origin_display_name"],
            time_unknown=False,
            origin_id=d["origin_id"],
            url_id=d["url_id"],
        )

    @classmethod
    def get_fresh_multiple(cls, ids):
        articles = db_session.query(Article).filter(Article.id.in_(ids)).all()
        id_article = {
            a.id: a for a in articles
        }
        return [
            None if i not in id_article else cls.from_db_entry(id_article[i])
            for i in ids
        ]

    def save_fresh(self):
        article = self._to_db_entry()

        try:
            self._update_relation(article)
        except DuplicatedEntryException as e:
            logger.warning("article {0} from {1} duplocated, igored".format(self.title, self.source_id))
            return

        # shouldn't need to update the relation for more than 3 times
        # as only origin and url are involved
        for i in range(3):
            try:
                db_session.add(article)
                db_session.commit()
                self.id = article.id
                self.origin_id = article.origin_id
                self.url_id = article.url_id
                return
            except IntegrityError as e:
                logger.warning("Race condition detected with origin {0} and url {1}".format(self.origin, self.url))
                db_session.rollback()
                try:
                    self._update_relation(article)
                except DuplicatedEntryException as e:
                    logger.warning("article {0} from {1} duplocated, igored".format(self.title, self.source_id))
                    return

        raise Exception("Failed to add article_proto: " + str(self))

    def normalize(self):
        self.url = normalize_url(self.url)

    @classmethod
    def from_db_entry(cls, article):
        return cls(
            id=article.id,
            title=article.title,
            summary=article.summary,
            url=article.url.url,
            timestamp=article.timestamp,
            origin=article.origin.identifier,
            image_url=article.image_url,
            source_id=article.source_id,
            origin_img=article.origin.image_url,
            origin_display_name=article.origin.display_name,
            time_unknown=False,
            origin_id=article.origin.id,
            url_id=article.url.id,
        )

    def _to_db_entry(self):
        article = Article()

        article.title = self.title
        article.timestamp = self.timestamp
        article.summary = self.summary
        article.source_id = self.source_id
        article.image_url = self.image_url

        return article

    def _update_relation(self, article):
        origin = get_or_create_origin(self.origin)
        origin.image_url = self.origin_img
        origin.display_name = self.origin_display_name

        url_row = get_or_create_url(self.url)

        article.url = url_row
        article.origin = origin

        # TODO: this doesn't guarantee no duplicate but the chance should be low for now
        if origin.id and url_row.id:
            exist = (
                db_session
                .query(Article)
                .filter_by(url_id=url_row.id, origin_id=origin.id)
                .first()
            )
            if exist and exist.title == article.title:
                raise DuplicatedEntryException("article is duplicated: " + str(self))
