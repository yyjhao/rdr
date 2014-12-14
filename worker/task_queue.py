from redis import StrictRedis
import pickle
import importlib
import hashlib
import time

from base.exceptions import DuplicatedEntryException

_queue = None


class _TaskQueue(object):
    def __init__(self):
        self._redis = StrictRedis()

        self._adder = self._redis.register_script('''
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

        self._popper = self._redis.register_script('''
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

        self._completer = self._redis.register_script('''
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

        super(_TaskQueue, self).__init__()

    def add_task(self, func, args, queue="default", timeout=300, delay=0, renew=False):
        string = self._serialize(func, args)
        sha1 = hashlib.sha1(string).hexdigest()
        adder = self._adder
        result = adder(keys=[
            sha1,
            self._serialize(func, args),
            queue,
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

    def pop_and_execute(self, queue="default"):
        result = self._popper(keys=[queue, int(time.time())])

        if result:
            task, tid = result
            func, args = self._deserialize(task)
            self._redis.hset(queue + '_done', tid, 1)
            self._completer(keys=[tid, queue, int(time.time())])
            return True
        else:
            return False


def get_queue():
    if not _queue:
        queue = _TaskQueue()

    return queue

