import time
from datetime import datetime, timedelta
from multiprocessing import Process

from base.types.exceptions import DuplicatedEntryException
import base.config as config
import base.log as log

def work_for(queues, worker_id, sleep_time=1):
    from base.database.session import init_db
    from worker.task_queue import get_queue
    init_db()

    logger = log.get_logger('worker')
    while True:
        executed = False
        for q in queues:
            try:
                r = get_queue().pop_and_execute(q)
                if r:
                    logger.info("Worker {0} executed a task on Queue {1}".format(worker_id, q))
                    executed = True
            except Exception:
                logger.error('Worker {0} failed to execute a task on Queue {1}'.format(worker_id, q), exc_info=True)
        if not executed:
            time.sleep(sleep_time)


def crawl(sid):
    from worker.task_queue import get_queue
    from base.types.sources import WrappedSource
    from crawler.crawlers import Crawler

    Crawler.get_crawler_for(WrappedSource.get(sid)).crawl()
    get_queue().add_task(crawl, (sid,), queue='crawler_queue', delay=1800, renew=True)


def add_source():
    from worker.task_queue import get_queue
    from base.types.sources import WrappedSource
    from base.database.session import init_db

    init_db()
    current = datetime.now()
    logger = log.get_logger('worker')
    for s in WrappedSource.get_all():
        if not s.last_retrive or current - s.last_retrive > timedelta(hours=2):
            try:
                logger.info('Attempting to add Source {0} to task queue.'.format(s.id))
                get_queue().add_task(crawl, (s.id,), queue='crawler_queue')
            except DuplicatedEntryException as e:
                pass


def init():
    for i in range(config.NUM_NETWORK_WORKERS):
        Process(target=work_for, args=(['crawler_queue', 'article_processor'], i)).start()
    add_source()
