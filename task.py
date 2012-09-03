"""
Downloading tasks
"""

import config
from plugins.disk import get_class
from plugins.backend import backend, task_status

class Task(object):
    """ downloading task. each downloading file should have one """

    def __init__(self, url, filename, options = {}):
        self.url = url
        self.filename = filename
        self.options  = options
        self.stauts = task_status["waiting"]
        self.errno = 0
        self.errmsg = ""
        self.key = None

    def start(self):
        if True or self.status == task_status["waiting"]:
            self.key = backend.new_task(self.url, self.filename, options = self.options)
            self.status = task_status["active"]
        else:
            print "file %s is in status \"%s\" not in waiting status" % (self.filename, self.status)

    def status(self):
        return backend.querry_task_status(self.key)

