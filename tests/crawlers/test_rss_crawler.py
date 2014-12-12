from crawler.crawlers import Crawler
from base.models import Source
from base.sources import WrappedSource, RssSource


source = RssSource.create_or_update('http://feeds.feedburner.com/Techcrunch')

Crawler.get_crawler_for(source).crawl()