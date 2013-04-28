""" Downloader class for pan.baidu.com """

import simplejson as json, re, requests
from io import StringIO
from urllib.parse import quote
from html.parser import HTMLParser

from task import Task
from plugins.disk.__base__ import BaseDownloader, BaseDownloaderException

html_parser = HTMLParser()

class Downloader(BaseDownloader):
    """
    Downlink for pan.baidu.com looks like this:
    http://pan.baidu.com/share/link?shareid=[ID]&uk=[UK]#dir/path=[SOMEPATH]
    Just GET http://pan.baidu.com/share/list?dir=[SOMEPATH]&uk=[UK]&shareid=[ID]
    The Server will return a JSON object containing list of files

    Everything else in the url is usless, for now.
    """

    brand  = "pan.baidu.com"
    # pretented to be firefox 20.0 on win 7
    header = {"User-Agent": "MozillaMozilla/5.0 (Windows NT 6.1; rv:20.0) Gecko/20130403 Firefox/20.0"}

    url_id_pattern = re.compile(r"^(?:http://)?pan.baidu.com/share/(link|home)\?")
    url_parse = re.compile("^(?:http://)?pan.baidu.com/share/(link|home)\?([^#]*)(?:#(.*))?$")

    json_from_html = re.compile(r'<script type="text/javascript">.*?function.*?"(\[\{.*?\}\])".*?</script>')

    cookies = None

    def __init__(self):
        pass

    def login(self, username = None, password = None):
        """ Login not needed """
        return None

    def url_pattern(self, url):
        return self.url_id_pattern.match(url) and True or False

    def download_info(self, url, cookie = None):
        # parse url
        home = None
        arg1 = None
        arg2 = None
        try:
            home, arg1, arg2 = self.url_parse.match(url).group(1, 2, 3)
        except Exception as e:
            raise BaseDownloaderException("URL Malform: %s, %s" % (url, str(e)))

        # type?
        url_type = ""
        if home == "home":
            # First, get num of file in home dir
            try:
                resp = requests.get(url, headers = self.header)
            except Exception as e:
                raise BaseDownloaderException( "Fail to get file list from %s, %s" % (url, str(e)));
            num_of_file = int(re.compile(r'<em class="publiccnt">(\d+)</em>').search(resp.text).group(1))

            # then make the request
            # http://pan.baidu.com/share/homerecord?uk=[uk]&num=[num_of_file]&page=1&dir=%2F
            resq_url = "http://pan.baidu.com/share/homerecord?%s&num=%d&page=1&dir=%%2F" % (arg1, num_of_file)

            try:
                resp = requests.get(resq_url, headers = self.header)
            except Exception as e:
                raise BaseDownloaderException( "Fail to get file list from %s, %s" % (url, str(e)));

            resp_json = json.load(StringIO(resp.text))

            if resp_json["errno"] != 0:
                print("resp: %r" % resp_json)
                print("url: %s"  % resq_url)
                raise BaseDownloaderException("Server returns error: %d" % resp_json["errno"])

            for f in resp_json["list"]:
                if len(f["fsIds"]) == 0:
                    continue

                if int(f["typicalCategory"]) == -1:
                    # Directory entry
                    resq_url = "http://pan.baidu.com/share/link?%s&shareid=%s#%s" % ( arg1, f["shareid"], quote(f['typicalPath']))
                else:
                    # file entry, yield recursive
                    resq_url = "http://pan.baidu.com/share/link?%s&shareid=%s" % (arg1, f["shareId"])

                try:
                    for t in self.download_info(resq_url):
                        yield t
                except Exception as e:
                    print("Url %s fail, %s" % (resq_url, str(e)))
                    continue

            raise StopIteration

        resp_json = []
        if not arg2 or not arg2.startswith("dir/path="):
            # json in HTML
            resq_url = url
            try:
                resp = requests.get(resq_url, headers = self.header)
            except Exception as e:
                raise BaseDownloaderException("Fail to get file list from %s, %s" % (url, str(e)));

            # extract json from HTML
            try:
                resp_json = json.load(StringIO(self.json_from_html.search(resp.text).group(1).replace('\\\\', '\\').replace('\\"', '"')))
            except Exception as e:
                raise BaseDownloaderException("Url %s contains no file" % url)
        else:
            # get JSON from an request
            resq_url = "http://pan.baidu.com/share/list?%s&dir=%s" % (arg1, arg2[9:])

            try:
                resp = requests.get(resq_url, headers = self.header)
            except Exception as e:
                raise BaseDownloaderException( "Fail to get file list from %s, %s" % (url, str(e)));

            resp_json = json.load(StringIO(resp.text))

            if resp_json["errno"] != 0:
                print("resp: %r" % resp_json)
                print("url: %s"  % resq_url)
                raise BaseDownloaderException("Server returns error: %d" % resp_json["errno"])

            resp_json = resp_json["list"]

        for n in resp_json:
            if int(n["isdir"]) == 1:
                resq_url = "http://pan.baidu.com/share/link?%s#dir/path=%s" % (arg1, quote(n["path"].encode("utf-8")))
                try:
                    for t in self.download_info(resq_url):
                        yield t
                except Exception as e:
                    print("Url %s fail, %s" % (resq_url, str(e)))
                    continue
            else:
                yield (Task(filename = n["server_filename"], url = [n["dlink"]],
                     opts = {"header": ["%s: %s" % (k, v) for k, v in list(self.header.items())]}))

