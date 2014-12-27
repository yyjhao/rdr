import pickle
import hashlib

from base.redis import cache_redis
from base.types.exceptions import DuplicatedEntryException
from worker.task_queue import async_queue
from base.config import ASYNC_EXP


def status_key(string):
    return 'async_status:' + string


def result_key(string):
    return 'async_result:' + string


def async(func, args):
    string = pickle.dumps([
        func.__module__,
        func.__name__,
        args,
    ])
    task_id = hashlib.sha1(string).hexdigest()
    try:
        async_queue.add_task(_exc_async, [func, args, task_id])
        cache_redis.setex(status_key(task_id), ASYNC_EXP, 'working')
    except DuplicatedEntryException:
        pass
    return task_id


def _exc_async(func, args, task_id):
    result = func(*args)
    cache_redis.setex(status_key(task_id), ASYNC_EXP, 'done')
    cache_redis.setex(result_key(task_id), ASYNC_EXP, pickle.dumps(result))


def query_task(task_id):
    status = cache_redis.get(status_key(task_id))
    if status == b'done':
        result = pickle.loads(cache_redis.get(result_key(task_id)))
        cache_redis.expire(status_key(task_id), 300)
        cache_redis.expire(result_key(task_id), 300)
        return (status, result)
    else:
        return (status, None)
