from sqlalchemy.exc import IntegrityError

from base.database.session import db_session
from base.database.models import Article
from base.database.util import get_or_create_origin, get_or_create_url
from base.types.data import ArticleProto
import base.log as log
from crawler.url_util import normalize_url

from base.types.exceptions import DuplicatedEntryException

logger = log.get_logger('article processor')


class WrappedArticle(ArticleProto):

    @classmethod
    def get(cls, id):
        article = Article.query.get(id)

        return cls(
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
        )

    def save(self):
        article = self._to_db_entry()

        try:
            self._update_relation(article)
        except DuplicatedEntryException as e:
            logger.warning("article {0} from {1} duplocated, igored".format(self.title, self.source_id))
            return
        db_session.add(article)

        # shouldn't need to update the relation for more than 3 times
        # as only origin and url are involved
        for i in range(3):
            try:
                db_session.commit()
                return
            except IntegrityError as e:
                logger.warning("Race condition detected with origin {0} and url {1}".format(self.origin, self.url))
                db_session.rollback()
                try:
                    self._update_relation(article)
                except DuplicatedEntryException as e:
                    logger.warning("article {0} from {1} duplocated, igored".format(self.title, self.source_id))
                    return
                db_session.add(article)

        raise Exception("Failed to add article_proto: " + str(self))

    def to_normalized(self):
        return self._replace(url=normalize_url(self.url))

    def _to_db_entry(self):
        article = Article()

        article.title = self.title
        article.timestamp = self.timestamp
        article.summary = self.summary

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
            if (
                db_session
                .query(Article)
                .filter_by(url_id=url_row.id, origin_id=origin.id)
                .first().title == article.title):
                    raise DuplicatedEntryException("article is duplicated: " + str(self))