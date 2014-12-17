from redis import StrictRedis

import base.config as config

task_queue_redis = StrictRedis(db=config.TASK_QUEUE_DB)
cache_redis = StrictRedis(db=config.CACHE_DB)