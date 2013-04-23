"""
Basic Interface of Downloader class
"""

class BaseDownloaderException(Exception):
    """ Downloader exceptions """

    def __init__(self, msg = "Unspecified Exception"):
        super(BaseDownloaderException, self).__init__()
        self.messege = msg

    def __str__(self):
        return repr(self.messege)

class BaseDownloader():
    brand = None

    def download_info(self, url, cookie):
        """ return task list from URL """
        raise BaseDownloaderException("download_info Not implemented")

    def login(self, username = None, password = None):
        """ Login. return cookie """
        if not (username and password):
            return {}
        else:
            raise BaseDownloaderException("Login not implemented")

    def url_pattern(self, url):
        return True


