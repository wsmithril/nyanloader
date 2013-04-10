""" Basic class for backend class """

import config

task_status = {
        "waiting":  0
    ,   "active":   1
    ,   "complete": 2
    ,   "error":    3
    ,   "paused":   4
    ,   "other":    5}

class BackendException(Exception):
    """
    Exceptions
    """
    def __init__(self, msg = "Backend Exceptions"):
        self.message = msg

    def __str__(self):
        return self.message

class Singleton(type):
    """ Singleton Warpper """
    _instance = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instance:
            cls._instance[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instance[cls]

class BaseBackend(object):
    """
    Download Manager Class
    parse url to get download url, and pass url to backend
    provide method to add task and querry download status
    """

    # Any backend should be a Singleton
    __metaclass__ = Singleton

    backend = None
    max_concurrecy = config.max_concurrency
    BE_RUNNING = 0
    BE_DOWN    = 1
    BE_NA      = 2

    def __new__(self):
        pass

    def status(self, url):
        return self.BE_NA

    def new_task(self, task):
        """ add new download task, return key to task """
        raise BackendException("new_task not implemented")

    def querry_task_status(self, key):
        """ querry status of an task using key """
        raise BackendException("querry_task_status not implemented")

    def remove_task(self, key):
        """ tell backend to release a task """
        pass

    def change_config(self, configs):
        """ Change backend config, take an dick as config """
        pass

