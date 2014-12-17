import json
import base.log as log
from base.redis import cache_redis

logger = log.get_logger('cache')


class Cachable(object):
    expire_time = 604800 # one week
    cache_on_save = True

    @classmethod
    def get(cls, id):
        return cls.get_multiple([id])[0]

    @classmethod
    def get_multiple(cls, ids):
        keys = [cls.get_key(i) for i in ids]

        pipe = cache_redis.pipeline(transaction=False)
        for key in keys:
            pipe.get(key)
        objs = [None if not s else cls.deserialize(s.decode('utf-8')) for s in pipe.execute()]

        missing = []
        for idx, obj in enumerate(objs):
            if not obj:
                logger.info("Cache for key {0} misses.".format(keys[idx]))
                missing.append(ids[idx])
        if missing:
            freshes = cls.get_fresh_multiple(missing)
            cls._cache(obj for obj in freshes if obj)
            pos = 0
            for idx in range(len(objs)):
                if not objs[idx]:
                    objs[idx] = freshes[pos]
                    pos += 1

        return objs

    def save(self):
        self.save_fresh()
        if self.cache_on_save:
            cache_redis.set([self.id])

    @classmethod
    def _cache(cls, objs):
        pipe = cache_redis.pipeline(transaction=False)
        for obj in objs:
            pipe.set(cls.get_key(obj.id), obj.serialize().encode('utf-8'))
        pipe.execute()

    def serialize(self):
        raise NotImplementedError()

    @classmethod
    def deserialize(cls, string):
        raise NotImplementedError()

    @classmethod
    def get_key(cls, id):
        raise NotImplementedError()

    @classmethod
    def get_fresh_multiple(cls, ids):
        raise NotImplementedError()

    @classmethod
    def save_fresh(self):
        raise NotImplementedError()
