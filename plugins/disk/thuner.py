# -*- coding: utf-8 -*-
""" For kuai.xunlei.com """

import re, requests

import task, config
from __base__ import BaseDownloader, BaseDownloaderException

class Downloader(BaseDownloader):
    """
    kuai.xunlei.com has all of its download link in the HTML.
    No extra request need to get real url
    """

    brand = "kuai.xunlei.com"

    # pretent we are Firefox 20.0 on Win 7
    header = {"User-Agent": "MozillaMozilla/5.0 (Windows NT 6.1; rv:20.0) Gecko/20130403 Firefox/20.0"}

    # all file in the url are in a the <a> tag under the class "file-name"
    # something like this one: <a ... class="file_name" href="url" ...>name</a>
    file_regex   = re.compile(r'(<a.*?class="file_name".*?>)')
    ttasks_regex = re.compile(r'<input type="hidden" id="total_task" value="(\d+)"/>')

    def login(self, username = None, password = None):
        """ No login required """
        return None

    def url_pattern(self, url):
        return url.startswith("http://kuai.xunlei.com/")

    def download_info(self, url, vookie = None):
        try:
            resp = requests.get(url, headers = self.header)
        except Exception as e:
            raise BaseDownloaderException("Cannot read from Url: %s, %s", (url, str(e)))

        # get number of pages
        try:
            num_of_pages = int((int(self.ttasks_regex.search(resp.text).group(1)) + 9) / 10)
        except:
            num_of_pages = 1

        base_url = resp.url

        for pg in xrange(1, num_of_pages + 1):
            if pg > 1:
                try:
                    resq_url = base_url + "?p_index=%s" % pg
                    resp = requests.get(resq_url, headers = self.header)
                except Exception as e:
                    print "Cannot read from Url: %s, %s", (url, str(e))
                    continue

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
                    for t in self.download_info(durl):
                        yield t
                else:
                    yield (task.Task(filename = fn, url = [durl],
                           opts = {"header": ["%s: %s" % (k, v) for k, v in self.header.items()]}))

