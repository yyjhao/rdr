# -*- coding: utf-8 -*-

from base.types.sources import TwitterSource, RssSource
import base.config as config
from base.database.session import db_session
from base.types.article import WrappedArticle
import base.log as log
from twitter import Twitter, OAuth
import dateutil.parser as date_parser
import feedparser
from time import mktime
from datetime import datetime, timedelta
from crawler.util import htmltruncate
from worker.task_queue import get_queue

from bs4 import BeautifulSoup, Comment


def add_article(article):
    article.to_normalized().save()


def truncate_html(html_string):
    if not html_string:
        return html_string
    soup = BeautifulSoup(html_string)
    comments = soup.findAll(text=lambda text: isinstance(text, Comment))
    [comment.extract() for comment in comments]
    [i.extract() for i in soup.findAll("script")]
    return htmltruncate(str(soup), 1024, ellipsis='...')


class Crawler(object):
    MAX_AGO = timedelta(days=14)

    def __init__(self, source):
        self.source = source
        self.log = log.get_logger('crawler {0}'.format(self.source.id))

    def crawl(self):
        self.start_time = datetime.now()
        self.log.info('Starting to crawl')
        for entry in self.get_json_entries():
            article = self.to_article(entry)
            if article:
                get_queue().add_task(add_article, (article,), queue='article_processor')
        self.source.last_retrive = self.start_time
        try:
            db_session.commit()
        except Exception as e:
            db_session.rollback()

    def to_article(self, json_entry):
        article = self.process(json_entry)
        if not self.source.should_add_article(article):
            self.log.info('Article {0} should not be added'.format(article.title))
            return None
        time_ago = self.start_time - article.timestamp
        if time_ago > self.MAX_AGO:
            return None

        return article

    def get_json_entries(self):
        raise NotImplementedError()

    def process(self, json_entry):
        raise NotImplementedError()

    @staticmethod
    def get_crawler_for(source):
        if isinstance(source, TwitterSource):
            return TwitterCrawler(source)
        elif isinstance(source, RssSource):
            return RssCrawler(source)


class TwitterCrawler(Crawler):

    def __init__(self, source):
        assert isinstance(source, TwitterSource)
        super(TwitterCrawler, self).__init__(source)

    def get_twitter_timeline(self, t, since_id=None, max_id=None, count=300):
        results = []
        try:
            results = t.statuses.home_timeline(count=count, since_id=self.source.since_id)
        except ValueError as e:
            self.log.warning('Failed to get twitter timeline, retrying')
            if count > 30:
                results = self.get_twitter_timeline(t, since_id=since_id, max_id=max_id, count=count / 2)
                results += self.get_twitter_timeline(t, since_id=since_id, max_id=results[-1]['id'], count=count / 2)
            else:
                results = t.statuses.home_timeline(count=count, since_id=self.source.since_id)

        return results

    def get_json_entries(self):
        t = Twitter(
            auth=OAuth(self.source.token, self.source.token_secret,
                       config.TWITTER_KEY, config.TWITTER_SECRET)
        )
        results = self.get_twitter_timeline(t, self.source.since_id)
        if results:
            self.source.since_id = results[0]['id']
        return results

    def process(self, json_entry):
        urls = json_entry['entities']['urls']
        if not len(urls):
            return None
        url_obj = urls[0]
        url = url_obj['expanded_url']
        if not url:
            url = url_obj['url']
        if not url:
            return None

        return WrappedArticle(
            url=url,
            title=json_entry['text'],
            timestamp=date_parser.parse(json_entry['created_at']).replace(tzinfo=None),
            origin='twitter:' + json_entry['user']['id_str'],
            origin_img=json_entry['user']['profile_image_url'],
            origin_display_name=json_entry['user']['name'],
            source_id=self.source.id,
            summary=None,
            time_unknown=False,
        )


class RssCrawler(Crawler):

    def __init__(self, source):
        assert isinstance(source, RssSource)
        super(RssCrawler, self).__init__(source)

    def get_json_entries(self):
        last = self.source.last_modified_indicator
        feed = None
        self.image = None
        # if self.source.url in ("http://golem.ph.utexas.edu/category/atom10.xml", "http://www.chromi.org/feed"):
        #     return []
        if last and ('etag' in last):
            feed = feedparser.parse(self.source.url, etag=last['etag'])
        elif last and ('modified' in last):
            feed = feedparser.parse(self.source.url, modified=last['modified'])
        else:
            feed = feedparser.parse(self.source.url)
        if feed.entries and feed.feed.get('image'):
            self.image = feed.feed.image.href
        if feed.get('etag'):
            self.source.last_modified_indicator = {
                'etag': feed.etag
            }
        elif feed.get('modified'):
            self.source.last_modified_indicator = {
                'modified': feed.modified
            }

        return feed.entries

    def process(self, json_entry):
        url = json_entry.get('feedburner_origlink') or json_entry.get('link')
        parsed_time = json_entry.get('published_parsed') or json_entry.get('updated_parsed')
        timestamp = None
        time_unknown = False
        if parsed_time:
            timestamp = datetime.fromtimestamp(mktime(parsed_time))
        else:
            time_unknown = True
            timestamp = self.start_time

        return WrappedArticle(
            url=url,
            title=json_entry.get('title'),
            timestamp=timestamp,
            summary=truncate_html(json_entry.get('summary')),
            origin=str(self.source.id) + ':' + json_entry.get('author', ''),
            origin_img=self.image,
            origin_display_name=json_entry.get('author', self.source.name),
            image_url=None,
            source_id=self.source.id,
            time_unknown=time_unknown,
        )
