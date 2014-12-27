from base.types.sources import TwitterSource, RssSource
from worker.task_queue import crawler_queue
from worker.workers import crawl
from base.types.exceptions import DuplicatedEntryException

def user_add_rss(user_id, url):
    source = RssSource.create_or_update(url)
    source.add_to_user(user_id)
    try:
        crawler_queue.add_task(crawl, (source.id,))
    except DuplicatedEntryException:
        pass
    return (user_id, source.to_dict())


def user_add_twitter(user_id, token, token_secret):
    source = TwitterSource.create_or_update(token, token_secret)
    source.add_to_user(user_id)
    try:
        crawler_queue.add_task(crawl, (source.id,))
    except DuplicatedEntryException:
        pass
    return (user_id, source.to_dict())


def import_opml_url(url):
    pass
    # d = listparser.parse(str(url))
    # print d
    # sources = []
    # for f in d.feeds:
    #     source = RssSource.create_or_update(current_user, f.url)
    #     sources.append(source)
    # for s in sources:
    #     if s:
    #         Crawler.crawl_for_source(s)
    # sources = (
    #     db_session
    #     .query(Source)
    #     .filter_by(user_id=current_user.id)
    #     .all()
    # )
    # return jsonify({
    #     'sources': [s.serialize for s in sources]
    # })