# -*- coding: utf-8 -*-

from base.sources import TwitterSource, RssSource, WrappedSource
import base.config as config
from base.database import db_session
from base.models import Article, Origin, Source
from twitter import Twitter, OAuth
import dateutil.parser as date_parser
from skynet.scorer import Scorer
import re
import feedparser
from time import mktime
from datetime import datetime, timedelta
from crawler.util import htmltruncate
from crawler.url_util import normalize_url

url_regex = re.compile(r'''(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’]))''')
def remove_url(string):
    return url_regex.sub('', string)

def truncate_html(html_string):
    if not html_string:
        return html_string
    return htmltruncate(html_string, 1024, ellipsis='...')

class Crawler(object):
    MAX_AGO = timedelta(days=2)

    def __init__(self, source):
        self.source = source

    def crawl(self):
        # print 'crawl', self.source._source.token
        self.now = datetime.now()
        for entry in self.get_json_entries():
            # print entry.get('link')
            article = self.to_article(entry)
            if article:
                db_session.add(article)
                try:
                    db_session.commit()
                except Exception as e:
                    print e
                    db_session.rollback()

    def to_article(self, json_entry):
        article = self.process(json_entry)
        if not article:
            return None
        time_ago = self.now - article.timestamp
        if time_ago > self.MAX_AGO:
            return None
        # print time_ago
        if not article:
            return None

        article.url = normalize_url(article.url)

        db_article = (
            db_session
            .query(Article)
            .filter_by(url=article.url, user_id=article.user_id)
            .first()
        )
        if db_article:
            if not db_article.timestamp or db_article.timestamp < article.timestamp:
                db_article.timestamp = article.timestamp.strftime('%Y-%m-%d %H:%M:%S')

            if article.origins[0] not in db_article.origins:
                db_article.origins.append(article.origins[0])
        else:
            db_article = article

        return db_article

    def get_or_create_origin(self, orig_id):
        source_id = self.source.id
        origin = db_session.query(Origin).filter_by(identifier=orig_id, source_id=source_id).first()
        if not origin:
            origin = Origin()
            origin.identifier = orig_id
            origin.source_id = source_id
        return origin

    def get_json_entries(self):
        raise NotImplementedError()

    def process(self, json_entry):
        raise NotImplementedError()

    @staticmethod
    def get_for(source):
        t = source.get_type()
        if t == 'twitter':
            return TwitterCrawler(source)
        elif t == 'rss':
            return RssCrawler(source)

    @staticmethod
    def crawl_for_source(source, score=True):
        wrapped_source = WrappedSource.get_for(source)
        crawler = Crawler.get_for(wrapped_source)
        crawler.crawl()
        if score:
            try:
                Scorer(source.user_id).score_new()    
            except:
                # lol
                pass

    @staticmethod
    def crawl_for_user(user_id):
        sources = db_session.query(Source).filter_by(user_id=user_id).all()
        for s in sources:
            Crawler.crawl_for_source(s, score=True)
        Scorer(user_id).score_new()


class TwitterCrawler(Crawler):

    def __init__(self, source):
        assert isinstance(source, TwitterSource)
        super(TwitterCrawler, self).__init__(source)

    def get_json_entries(self):
        t = Twitter(
            auth=OAuth(self.source.token, self.source.token_secret,
                       config.TWITTER_KEY, config.TWITTER_SECRET)
        )
        results = []
        if self.source.since_id:
            results = t.statuses.home_timeline(count=200, since_id=self.source.since_id)
        else:
            results = t.statuses.home_timeline(count=200)

        if results:
            self.source.since_id = results[0]['id']
        return results

    def process(self, json_entry):
        article = Article()
        urls = json_entry['entities']['urls']
        if not len(urls):
            return None
        url_obj = urls[0]
        url = url_obj['expanded_url']
        if not url:
            url = url_obj['url']
        if not url:
            return None

        article.user_id = self.source.user_id
        article.url = url
        article.title = remove_url(json_entry['text'])
        article.timestamp = date_parser.parse(json_entry['created_at']).replace(tzinfo=None)
        orig_id = json_entry['user']['id_str']
        origin = self.get_or_create_origin(orig_id)
        origin.image_url = json_entry['user']['profile_image_url']
        origin.display_name = json_entry['user']['name']
        article.origins.append(origin)

        return article

class RssCrawler(Crawler):

    def __init__(self, source):
        assert isinstance(source, RssSource)
        super(RssCrawler, self).__init__(source)

    def get_json_entries(self):
        last = self.source.last_modified_indicator
        feed = None
        self.image = None
        if 'etag' in last:
            feed = feedparser.parse(self.source.url, etag=last['etag'])
        elif 'modified' in last:
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
        article = Article()
        url = json_entry.get('feedburner_origlink')
        if not url:
            url = json_entry.get('link')

        article.user_id = self.source.user_id
        article.url = url
        article.title = json_entry.get('title')
        parsed_time = json_entry.get('published_parsed') or json_entry.get('updated_parsed')
        if parsed_time:
            article.timestamp = datetime.fromtimestamp(mktime(parsed_time))
        else:
            print 'no time for', self.source.url
            article.timestamp = datetime.now()
        article.summary = truncate_html(json_entry.get('summary'))

        orig_id = str(self.source.id) + '-' + json_entry.get('author', '')
        origin = self.get_or_create_origin(orig_id)
        origin.image_url = self.image
        origin.display_name = json_entry.get('author', self.source.name)
        article.origins.append(origin)

        return article
