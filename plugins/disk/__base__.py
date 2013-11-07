"""
Basic Interface of Downloader class
"""

class BaseDownloaderException(Exception):
    """ Downloader exceptions """

    def __init__(self, msg = "Unspecified Exception"):
        super(BaseDownloaderException, self).__init__()
        self.messege = msg

    def __str__(self):
        return self.messege

class BaseDownloader():
    brand = None

    def download_info(self, url):
        """ return task list from URL """
        raise BaseDownloaderException("download_info Not implemented")

    @staticmethod
    def login(username = None, password = None):
        """ Login. return cookie """
        if not (username and password):
            return {}
        else:
            raise BaseDownloaderException("Login not implemented")

    @staticmethod
    def url_pattern(url):
        raise BaseDownloaderException("staticmethod url_pattern() Must be implemed")

