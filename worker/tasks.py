class ProcessArticleTask(object):
    def __init__(self):
        super(ProcessArticleTask, self).__init__()

    @classmethod
    def init_with_article(cls, article_proto):
        task = cls()
        task.article_proto = article_proto
        return task

    def add(self):
        print(self.article_proto)
