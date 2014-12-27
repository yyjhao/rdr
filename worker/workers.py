import time
from datetime import datetime, timedelta
from multiprocessing import Process

from base.types.exceptions import DuplicatedEntryException
import base.config as config
import base.log as log


def work_for(queues, worker_id, sleep_time=1):
    from base.database.session import init_db
    init_db()

    logger = log.get_logger('worker')
    while True:
        executed = False
        for q in queues:
            try:
                r = q.pop_and_execute()
                if r:
                    logger.info("Worker {0} executed a task on Queue {1}".format(worker_id, q.queue))
                    executed = True
            except Exception:
                logger.error('Worker {0} failed to execute a task on Queue {1}'.format(worker_id, q.queue), exc_info=True)
        if not executed:
            time.sleep(sleep_time)


def crawl(sid):
    from worker.task_queue import crawler_queue
    from crawler.tasks import crawl_for_source

    if crawl_for_source(sid):
        crawler_queue.add_task(crawl, (sid,), delay=900, renew=True)
    else:
        crawler_queue.add_task(crawl, (sid,), delay=43200, renew=True)


def user_ai(user_id):
    from skynet.tasks import serve_user
    from worker.task_queue import ai_queue
    serve_user(user_id)
    ai_queue.add_task(user_ai, (user_id, ), delay=900, renew=True)


def add_source():
    from worker.task_queue import crawler_queue
    from base.types.sources import WrappedSource
    from base.database.session import init_db

    init_db()
    current = datetime.now()
    logger = log.get_logger('worker')
    for s in WrappedSource.get_all():
        if not s.last_retrive or current - s.last_retrive > timedelta(hours=2):
            try:
                logger.info('Attempting to add Source {0} to task queue.'.format(s.id))
                crawler_queue.add_task(crawl, (s.id,))
            except DuplicatedEntryException as e:
                pass


def add_user():
    from worker.task_queue import ai_queue
    from base.database.session import init_db, db_session
    from base.database.models import User
    from skynet.user_status import UserStatus

    logger = log.get_logger('add_user')

    init_db()
    for u in db_session.query(User.id).all():
        if UserStatus(u).get_current_status() != 'buried':
            try:
                logger.info("Attempting to add user {0} to ai queue.".format(u))
                ai_queue.add_task(user_ai, (u,))
            except:
                pass
        else:
            logger.info("User {0} is buried.".format(u))


def network_worker(wid):
    from worker.task_queue import crawler_queue, article_processor
    work_for([crawler_queue, article_processor], wid)


def async_worker(wid):
    from worker.task_queue import async_queue
    work_for([async_queue], wid)


def ai_worker(wid):
    from worker.task_queue import ai_queue
    work_for([ai_queue], wid)


def init():
    for i in range(config.NUM_NETWORK_WORKERS):
        Process(target=network_worker, args=(i,)).start()
    for i in range(config.NUM_AI_WORKERS):
        Process(target=ai_worker, args=(i + config.NUM_NETWORK_WORKERS,)).start()
    for i in range(config.NUM_ASYNC_WORKERS):
        Process(target=async_worker, args=(i + config.NUM_NETWORK_WORKERS + config.NUM_AI_WORKERS,)).start()
    add_source()
    add_user()
