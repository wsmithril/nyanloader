# -*- coding: utf-8 -*-
""" For kuai.xunlei.com """

import re, requests, traceback

from task import Task
from plugins.disk.__base__ import BaseDownloader, BaseDownloaderException

class Downloader(BaseDownloader):
    """
    kuai.xunlei.com has all of its download link in the HTML.
    No extra request need to get real url
    """

    brand = "kuai.xunlei.com"

    # pretent we are Firefox 20.0 on Win 7
    header = {"User-Agent": "MozillaMozilla/5.0 (Windows NT 6.1; rv:20.0) Gecko/20130403 Firefox/20.0",
              "Accept-Language": "zh-cn"}

    # all file in the url are in a the <a> tag under the class "file-name"
    # something like this one: <a ... class="file_name" href="url" ...>name</a>
    file_regex   = re.compile(r'(<a.*?class="file_name".*?>)')
    ttasks_regex = re.compile(r'<input type="hidden" id="total_task" value="(\d+)"/>')

    def __init__(self):
        pass

    @staticmethod
    def login(username = None, password = None):
        """ No login required """
        return None

    @staticmethod
    def url_pattern(url):
        return url.startswith("http://kuai.xunlei.com/")

    def download_info(self, url):
        try:
            resp = requests.get(url, headers = self.header)
        except Exception as e:
            traceback.print_exc()
            raise BaseDownloaderException("Cannot read from Url: %s, %s" % (url, str(e)))

        # get number of pages
        try:
            num_of_pages = int((int(self.ttasks_regex.search(resp.text).group(1)) + 9) / 10)
        except:
            num_of_pages = 1

        base_url = resp.url

        for pg in range(1, num_of_pages + 1):
            if pg > 1:
                try:
                    resq_url = base_url + "?p_index=%s" % pg
                    resp = requests.get(resq_url, headers = self.header)
                except Exception as e:
                    continue

            # kuai.xunlei.com set Encoding in the respond header as ISO-8859-1
            # but the respond body is acutually in UTF-8. So, we need manually
            # set it
            resp.encoding = "utf-8"

            for l in self.file_regex.findall(resp.text):
                fn   = None
                durl = None
                for (k, v) in [s.split('="', 1) for s in re.split('"(?: |>)', l[3:]) if s != '']:
                    if k == "title":
                        fn = v
                    elif k == "href":
                        durl = v

                if durl.startswith("http://kuai.xunlei.com/"):
                    # this is an dir, we needs to recursively yields it
                    yield from self.download_info(durl)
                else:
                    if durl.startswith("#"):
                        continue

                    yield (Task(filename = fn, url = [durl],
                           opts = {"header": ["%s: %s" % (k, v) for k, v in list(self.header.items())]}))

