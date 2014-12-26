import pickle
import importlib
import hashlib
import time

from base.types.exceptions import DuplicatedEntryException
import base.log as log
from base.redis import task_queue_redis

_redis = task_queue_redis

_adder = _redis.register_script('''
    local hash = KEYS[1]
    local task = KEYS[2]
    local queue = KEYS[3]
    local timeout = KEYS[4]
    local delay = KEYS[5]
    local now = KEYS[6]
    local renew = KEYS[7]

    if redis.call('HEXISTS', queue .. "_map", hash) == 1 then
        if renew then
            redis.call('HSET', queue .. "_renew", hash, delay)
        else
            return 'duplicated'
        end
    else
        redis.call('HSET', queue .. "_map", hash, task)
        redis.call('ZADD', queue .. "_queue", delay + now, hash)
        redis.call('HSET', queue .. "_timeout", hash, timeout)
        return 1
    end
''')

_popper = _redis.register_script('''
    local queue = KEYS[1]
    local now = KEYS[2]
    while 1 do
        local hashes = redis.call('ZRANGEBYSCORE', queue .. "_queue", 0, now, 'limit', 0, 1)
        if table.getn(hashes) == 0 then
            return nil
        elseif redis.call('HEXISTS', queue .. "_map", hashes[1]) == 0 then
            redis.call('ZREM', queue .. "_queue", hashes[1])
            redis.call('HDEL', queue .. "_timeout", hashes[1])
        else
            redis.call('ZADD', queue .. "_queue", redis.call('HGET', queue .. "_timeout", hashes[1]) + now, hashes[1])
            return {redis.call('HGET', queue .. "_map", hashes[1]), hashes[1]}
        end
    end
''')

_completer = _redis.register_script('''
    local hash = KEYS[1]
    local queue = KEYS[2]
    local now = KEYS[3]
    if redis.call('HEXISTS', queue .. "_renew", hash) == 1 then
        redis.call('ZADD', queue .. "_queue", now + redis.call('HGET', queue .. "_renew", hash), hash)
        redis.call('HDEL', queue .. "_renew", hash)
    else
        redis.call('ZREM', queue .. "_queue", hash)
        redis.call('HDEL', queue .. "_map", hash)
        redis.call('HDEL', queue .. "_timeout", hash)
    end
''')

logger = log.get_logger('task queue')


class TaskQueue(object):
    def __init__(self, queue):
        self.queue = queue
        self._adder = _adder
        self._completer = _completer
        self._popper = _popper
        super(TaskQueue, self).__init__()

    def add_task(self, func, args, timeout=300, delay=0, renew=False):
        string = self._serialize(func, args)
        sha1 = hashlib.sha1(string).hexdigest()
        result = self._adder(keys=[
            sha1,
            self._serialize(func, args),
            self.queue,
            timeout,
            delay,
            int(time.time()),
            renew,
        ])

        if result != 1:
            if result == b'duplicated':
                raise DuplicatedEntryException()

    def _serialize(self, func, args):
        return pickle.dumps([
            func.__module__,
            func.__name__,
            args,
        ])

    def _deserialize(self, string):
        module, func, args = pickle.loads(string)
        lib = importlib.import_module(module)
        return getattr(lib, func), args

    def pop_and_execute(self):
        result = self._popper(keys=[self.queue, int(time.time())])

        if result:
            task, tid = result
            func, args = self._deserialize(task)
            logger.debug("Popped task {0}, {1}, {2}".format(func, args, tid))
            start = time.time()
            try:
                func(*args)
            except Exception:
                logger.error("Task {0}, {1}, {2} failed".format(func, args, tid), exc_info=True)
            end = time.time()
            self._completer(keys=[tid, self.queue, int(time.time())])
            logger.info("Task {0} took {1} seconds".format(tid, end - start))
            return True
        else:
            return False

crawler_queue = TaskQueue('crawler_queue')
article_processor = TaskQueue('article_processor')
ai_queue = TaskQueue('ai_queue')
