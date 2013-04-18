"""
Basic Interface of Downloader class
"""

class BaseDownloaderException(Exception):
    """ Downloader exceptions """

    def __init__(self, msg = "Unspecified Exception"):
        self.messege = msg

    def __str__(self):
        return repr(self.messege)

class BaseDownloader():
    brand = None
    TYPE_FOLDER = 1
    TYPE_FILE   = 0

    def download_info(self):
        """ gather information from url,
            return generator of list of dict contains 2 key:
                filename - the real filenamer
                url      - list of usable url
        """
        raise BaseDownloaderException("download_info Not implemented")

    def login(self, username = None, password = None):
        """ Login. return cookie dictionary """
        if not (username and password):
            return {}
        else:
            raise BaseDownloaderException("Login not implemented")

    def url_pattern(self, url):
        return True


