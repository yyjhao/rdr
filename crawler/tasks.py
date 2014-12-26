from base.types.sources import WrappedSource
from crawler.crawlers import Crawler


def crawl_for_source(sid):
    crawler = Crawler.get_crawler_for(WrappedSource.get(sid))
    crawler.crawl()
    return crawler.new_article_count()

