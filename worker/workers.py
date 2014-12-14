import time
from datetime import datetime, timedelta
from multiprocessing import Process

from base.exceptions import DuplicatedEntryException
import base.config as config

def work_for(queues, worker_id, sleep_time=5):
    from base.database import init_db
    from worker.task_queue import get_queue
    init_db()
    while True:
        executed = False
        for q in queues:
            r = get_queue().pop_and_execute(q)
            if r:
                print("Worker {0} did some work on queue {1}".format(worker_id, q))
                executed = True
        if not executed:
            time.sleep(sleep_time)


def crawl(sid):
    from worker.task_queue import get_queue
    from base.sources import WrappedSource
    from crawler.crawlers import Crawler

    Crawler.get_crawler_for(WrappedSource.get(sid)).crawl()
    get_queue().add_task(crawl, (sid,), queue='crawler_queue', delay=3600, renew=True)


def add_source():
    from worker.task_queue import get_queue
    from base.sources import WrappedSource
    from base.database import init_db

    init_db()
    current = datetime.now()
    for s in WrappedSource.get_all():
        if not s.last_retrive or current - s.last_retrive > timedelta(hours=2):
            try:
                get_queue().add_task(crawl, (s.id,), queue='crawler_queue')
            except DuplicatedEntryException as e:
                pass


def init():
    for i in range(config.NUM_NETWORK_WORKERS):
        Process(target=work_for, args=(['crawler_queue', 'article_processor'], i)).start()
    add_source()
