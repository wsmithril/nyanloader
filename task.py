import config
from plugins.backend import backend, task_status

class Task(object):
    """ Downloading task Control """

    def __init__(self, url, filename, opts = []):
        self.url      = url
        self.filename = filename
        self.key      = None
        self.opts     = opts

    def start(self):
        self.key = backend.new_task(self)
        return self

    def status(self):
        if self.key:
            return backend.querry_task_status(self.key)
        else:
            return task_status["waiting"]

