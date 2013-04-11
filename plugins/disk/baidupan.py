""" Downloader class for pan.baidu.com """

import simplejson as json, re, requests, inspect
import config
import task

from StringIO import StringIO
from os.path import dirname
from __base__ import BaseDownloader, BaseDownloaderException
from time import time
from urllib2 import quote

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

    url_id_pattern = re.compile(r"^(?:http://)?pan.baidu.com/share/link\?")
    url_parse = re.compile("^(?:http://)?pan.baidu.com/share/link\?([^#]*)(?:#dir/path=(.*))?$")

    single_url = map(lambda x: re.compile(x, re.MULTILINE), [
            r'<a\s+class="new-dbtn"\s+href="([^"]*)".*>',
            r'<span class="header-name" title="([^"]*)".*>'])

    single_dir = map(lambda r: re.compile(r), [
        r'\\"server_filename\\":\\"((?:\\.|[0-9a-zA-Z])+)\\",',
        r'\\"parent_path\\":\\"((?:%|\w)+)\\",'])

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
        try:
            arg1, arg2 = self.url_parse.match(url).group(1, 2)
        except Exception as e:
            raise BaseDownloaderException("Malformed url: %s, %s" % (url, str(e)))

        if not arg2:
            # single file
            resq_url = url

            # get file list
            try:
                resp = requests.get(resq_url, headers = self.header)
            except Exception as e:
                raise BaseDownloaderException( "Fail to get file list from %s, %s" % (url, str(e)));

            filename = self.single_url[1].search(resp.text)
            if filename:
                url      = self.single_url[0].search(resp.text).group(1)
                filename = filename.group(1)
                yield (task.Task(filename = filename, url = url,
                     opts = {"header": ["%s: %s" % (k, v) for k, v in self.header.items()]}))
                raise StopIteration
            else:
                arg2 = "/".join([
                    self.single_dir[1].search(resp.text).group(1),
                    quote(self.single_dir[0].search(resp.text).group(1).replace('\\\\', '\\').decode("unicode_escape").encode("utf-8"))])

        resq_url = "http://pan.baidu.com/share/list?%s&dir=%s" % (arg1, arg2)

        try:
            resp = requests.get(resq_url, headers = self.header)
        except Exception as e:
            raise BaseDownloaderException( "Fail to get file list from %s, %s" % (url, str(e)));

        resp_json = json.load(StringIO(resp.text))

        if resp_json["errno"] != 0:
            print "resp: %r" % resp_json
            print "url: %s"  % resq_url
            raise BaseDownloaderException("Server returns error: %d" % resp_json["errno"])

        # print "\n".join("%s - %s" % (n["server_filename"], n["dlink"]) for n in resp_json["list"])
        for n in resp_json["list"]:
            yield (task.Task(filename = n["server_filename"], url = [n["dlink"]],
                 opts = {"header": ["%s: %s" % (k, v) for k, v in self.header.items()]}))

