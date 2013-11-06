""" task """

from time import time
from plugins.backend import backend, task_status

class Task(object):
    """ Downloading task Control """

    def __init__(self, url, filename, opts = []):
        self.url        = url
        self.filename   = filename
        self.key        = None
        self.opts       = opts
        self.size       = 0
        self.downloaded = 0
        self.start_time = time()
        self.speed      = 0
        self.statuscode = 0

    def start(self):
        self.key = backend.new_task(self)
        return self

    def status(self):
        if self.key:
            return backend.querry_task_status(self)
        else:
            return task_status["waiting"]

