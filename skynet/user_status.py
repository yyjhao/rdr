from base.redis import cache_redis

class UserStatus(object):
    def __init__(self, user_id):
        self.user_id = user_id
        self.key = 'user_status:' + str(self.user_id)

    def get_current_status(self):
        status = cache_redis.get(self.key)
        if status:
            status = status.decode('utf-8')
        else:
            status = 'idle'
        return status

    def set_status(self, val):
        cache_redis.set(self.key, val)

    def notify_user_action(self):
        status = self.get_current_status()
        if status in ('idle', 'incoming'):
            self.set_status('train')

    def notify_incoming_articles(self):
        status = self.get_current_status()
        if status == 'idle':
            self.set_status('incoming')

    def notify_training(self):
        self.set_status('idle')

    def notify_scoring(self):
        self.set_status('idle')

    def bury(self):
        self.set_status('buried')
