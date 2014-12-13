from redis import StrictRedis
import time
import json
import importlib


def now_in_ms():
    return int(round(time.time() * 1000))

_queue = None

class _TaskQueue(object):
    def __init__(self):
        self._redis = StrictRedis()

        # keys: task id counter name, task hashmap name, task string,
        # queue name, delay until (in ms), timeout hashmap name, timeout time
        self._adder = self._redis.register_script('''
            local tid = redis.call('INCR', KEYS[1]);
            redis.call('HSET', KEYS[2], tid, KEYS[3])
            redis.call('ZADD', KEYS[4], KEYS[5], tid)
            redis.call('HSET', KEYS[6], tid, KEYS[7])
            return tid
        ''')

        # keys: queue name, current timestamp (in ms), done hashmap name
        # task hashmap name, timeout map name
        self._popper = self._redis.register_script('''
            while 1 do
                local tids = redis.call('ZRANGEBYSCORE', KEYS[1], 0, KEYS[2], 'limit', 0, 1)
                if table.getn(tids) == 0 then
                    return nil
                elseif redis.call('HEXISTS', KEYS[3], tids[1]) == 1 then
                    redis.call('ZREM', KEYS[1], tids[1])
                    redis.call('HDEL', KEYS[3], tids[1])
                    redis.call('HDEL', KEYS[4], tids[1])
                    redis.call('HDEL', KEYS[5], tids[1])
                else
                    redis.call('ZINCRBY', KEYS[1], redis.call('HGET', KEYS[5], tids[1]), tids[1])
                    return {redis.call('HGET', KEYS[4], tids[1]), tids[1]}
                end
            end
        ''')
        super(_TaskQueue, self).__init__()

    def add_task(self, func, args, queue="default", timeout=300000):
        self._adder(keys=[
            queue + '_counter',
            queue + '_tasks',
            self._serialize(func, args),
            queue + '_queue',
            now_in_ms(),
            queue + '_timeout',
            timeout,
        ], args=[])

    def _serialize(self, func, args):
        return json.dumps([
            func.__module__,
            func.__name__,
            args,
        ])

    def _deserialize(self, string):
        module, func, args = json.loads(string.decode("utf-8"))
        lib = importlib.import_module(module)
        return getattr(lib, func), args

    def pop_and_execute(self, queue="default"):
        result = self._popper(keys=[
            queue + '_queue',
            now_in_ms(),
            queue + '_done',
            queue + '_tasks',
            queue + '_timeout',
        ])

        if result:
            task, tid = result
            func, args = self._deserialize(task)
            func(*args)
            self._redis.hset(queue + '_done', tid, 1)


def get_queue():
    if not _queue:
        queue = _TaskQueue()

    return queue

