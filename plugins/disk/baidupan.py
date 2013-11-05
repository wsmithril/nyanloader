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
    pan.baidu.com now has a new url schema:
    For normal link, url is pan.baidu.com/s/[uk], we need to extract share_id
    from the page.
    """

    brand  = "pan.baidu.com - v2"
    # pretented to be firefox 20.0 on win 7
    header = {"User-Agent": "MozillaMozilla/5.0 (Windows NT 6.1; rv:20.0) Gecko/20130403 Firefox/20.0"}
    cookies = None

    @staticmethod
    def try_parse(url):
        """ Parse url, returns "s" or "home" when matched, None for bad url """
        return (
            (re.compile(r"(?:http://)?pan.baidu.com/s/.+").match(url)          and "s")    or
            (re.compile(r'(?:http://)?pan.baidu.com/share/home?.+').match(url) and "home") or
            (re.compile(r'(?:http://)?pan.baidu.com/share/link?.+').match(url) and "s")    or
            None
        )

    def __init__(self):
        pass

    @staticmethod
    def login(username = None, password = None):
        """ Login not needed """
        return None

    @staticmethod
    def url_pattern(url):
        return Downloader.try_parse(url) and True or False

    def download_info(self, url, cookie = None):
        # home or filelist
        url_type = Downloader.try_parse(url)

        if url_type == "s":
            yield from Downloader.fileinfo_from_list(url)
        elif url_type == "home":
            yield from Downloader.fileinfo_from_home(url)
        else:
            raise BaseDownloaderException("URL Malform: %s, this should not happen" % (url))

    @staticmethod
    def extract_filejson(text):
        filelist = re.compile(r'<script type="text/javascript">.*?"(\[\{.*?\}\])".*?</script>')
        return json.load(StringIO(filelist.search(text).group(1).replace('\\\\', '\\').replace('\\"', '"')))

    @staticmethod
    def filelist_json_gen(baseurl, filelist):
        for fileinfo in filelist:
            if int(fileinfo["isdir"]) == 1:
                yield from Downloader.filelist_json_gen(baseurl, Downloader.get_json_for_dir(baseurl, fileinfo["path"]))
            else:
                yield (Task(filename = fileinfo["server_filename"], url = [fileinfo["dlink"]],
                     opts = {"header": ["%s: %s" % (k, v) for k, v in list(Downloader.header.items())]}))
        raise StopIteration

    @staticmethod
    def get_json_for_dir(baseurl, dir_name):
        # form url
        url = baseurl + '&dir=%s' % (dir_name)
        try:
            resp = requests.get(url, headers = Downloader.header)
        except Exception as e:
            raise BaseDownloaderException("Url: %s has no file. %s" % (url, str(e)))
        ret_json = json.load(StringIO(resp.text))
        if ret_json["errno"] != 0:
            print("resp: %r" % ret_json)
            print("url: %s"  % url)
            raise BaseDownloaderException("Server returns error: %d" % ret_json["errno"])
        return ret_json["list"]

    @staticmethod
    def fileinfo_from_list(url):
        # get page
        try:
            resp = requests.get(url, headers = Downloader.header)
        except Exception as e:
            raise BaseDownloaderException("Fail to get url: %s, %s" % (url, str(e)))

        try:
            uk       = re.compile(r'FileUtils\.sysUK="(\d+)"'   ).search(resp.text).group(1)
            share_id = re.compile(r'FileUtils\.share_id="(\d+)"').search(resp.text).group(1)
        except Exception as e:
            raise BaseDownloaderException("Url: %s has no file. %s" % (url, str(e)))

        if not uk or not share_id:
            raise BaseDownloaderException("Url: %s has no file." % (url))

        baseurl = "http://pan.baidu.com/share/list?uk=%s&shareid=%s" % (uk, share_id)

        resp_json = []
        dir_name = re.compile(r'dir/path=([^#]+)').search(url)
        resq_url = ""
        if dir_name:
            dir_name = dir_name.group(1)
            # extract uk and share_id
            resp_json = Downloader.get_json_for_dir(baseurl, dir_name)
        else:
            # file list hides in json embbeded in page
            resp_json = Downloader.extract_filejson(resp.text)
            if not resp_json:
                raise BaseDownloaderException("Url: %s has no file." % (url))
        yield from Downloader.filelist_json_gen(baseurl, resp_json)

    @staticmethod
    def fileinfo_from_home(url):
        # get UK
        uk = re.compile(r'uk=(\d+)').search(url).group(1)

        try:
            resp = requests.get(url, headers = Downloader.header)
        except Exception as e:
            raise BaseDownloaderException( "Fail to get file list from %s, %s" % (url, str(e)));

        # get num of files
        num_of_file = int(re.compile(r'FileUtils\.pubshare_count="(\d+)"').search(resp.text).group(1))

        start = 0
        # We can only get less than 100 items a time, or server will return an error
        while num_of_file > 0:
            limit = min(num_of_file, 60)
            # http://pan.baidu.com/pcloud/feed/getsharelist?auth_type=1&request_location=share_home&start=[start]&limit=[limit]&query_uk=[uk]
            resq_url = "http://pan.baidu.com/pcloud/feed/getsharelist?auth_type=1&request_location=share_home&start=%d&limit=%d&query_uk=%s" % (start, limit, uk)

            try:
                resp = requests.get(resq_url, headers = Downloader.header)
            except Exception as e:
                raise BaseDownloaderException( "Fail to get file list from %s, %s" % (url, str(e)));

            resp_json = json.load(StringIO(resp.text))

            if resp_json["errno"] != 0:
                print("resp: %r" % resp_json)
                print("url: %s"  % resq_url)
                raise BaseDownloaderException("Server returns error: %d" % resp_json["errno"])

            num_of_file = num_of_file - limit
            start       = start       + limit

            for f in resp_json["records"]:
                fileinfo = f["filelist"][0]
                baseurl = fileinfo["isdir"] == 1 and "http://pan.baidu.com/share/list?uk=%s&shareid=%s" % (uk, f["shareid"])
                try:
                    yield from Downloader.filelist_json_gen(baseurl, [fileinfo])
                except Exception as e:
                    print("Failed: %s" % f)
        raise StopIteration
