"""
Basic class for backend class
"""

import config

class BackendException(Exception):
    """
    Exceptions
    """
    def __init__(self, msg = "Backend Exceptions"):
        self.messege = msg

    def __str__(self):
        return repr(msg)

class BaseBackend(object):
    """
    Download Manager Class
    parse url to get download url, and pass url to backend
    provide method to add task and querry download status
    """

    backend = None
    max_concurrecy = config.max_concurrency
    BE_RUNNING = 0
    BE_DOWN    = 1
    BE_NA      = 2

    def __init__(self):
        pass

    def status(self, url):
        return self.BE_NA

    def new_task(self, url):
        """
        add new download task, return key to task
        """
        raise BackendException("new_task not implemented")

    def querry_task_status(self, key):
        """
        querry status of an task using key
        """
        raise BackendException("querry_task_status not implemented")

    def remove_task(self, key):
        """
        tell backend to release a task
        """
        pass

    def change_config(self, configs):
        """
        Change backend config, take an dick as config
        """
        pass

