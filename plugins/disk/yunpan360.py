""" Downloader for yunpan.com """

import json as json, re, requests
from io import StringIO

from task import Task
from plugins.disk.__base__ import BaseDownloader, BaseDownloaderException

def extract_filelist_json(text):
    pattern = re.compile(r'var\s*rootFileList\s*=\s*\{.*,data:(\[\{.*\}\])\};')
    match   = pattern.search(text)
    if not match: return None
    return json.load(StringIO(match.group(1)))

def format_payload(shorturl, nid):
    return "shorturl=%s&nid=%s" % (shorturl, nid)

class Downloader(BaseDownloader):
    """ Downloader for yunpan.com """

    brand = "yunpan.com"

    # pretented to be firefox 20.0 on win 7
    header = {"User-Agent": "MozillaMozilla/5.0 (Windows NT 6.1; rv:20.0) Gecko/20130403 Firefox/20.0"}


    def __init__(self):
        self.cookie = None

    @staticmethod
    def login(username = None, password = None):
        """ Dose not need to login, for now """
        return None

    @staticmethod
    def url_pattern(url):
        pattern = re.compile(r"(?:http://)?(?:\w+\.)?l\d+\.yunpan.cn/lk/.+")
        return pattern.match(url) and True or None

    def download_info(self, url, cookie = None):
        # short URL
        try:
            domain, shorturl = re.compile(r'(?:http://)?((?:\w+\.)?l\d+\.yunpan.cn)/lk/(.+)$').search(url).group(1, 2)
        except Exception as e:
            raise BaseDownloaderException("Malform URL: %s, no shortur or domain" % (s, str(e)))

        # extract filelist json from page
        try:
            page = requests.get(url, headers = Downloader.header)
        except Exception as e:
            raise BaseDownloaderException("Fail to get page %s\n%s" % (s, str(e)))

        rootFileList = extract_filelist_json(page.text)

        if not rootFileList:
            raise BaseDownloaderException("Url %s has no file in it" % s)

        for fileinfo in rootFileList:
            # http://l10.yunpan.cn/share/downloadfile/
            post_url  = "http://%s/share/downloadfile/" % domain
            post_data = format_payload(shorturl, fileinfo["nid"])
            try:
                header = dict(list(Downloader.header.items()) + [
                    ("Referer", url),
                    ("Content-Type", "application/x-www-form-urlencoded UTF-8; charset=UTF-8"),
                ])

                post_resp = requests.post(post_url, data = post_data, headers = header, cookies = {})
                resp_json = json.load(StringIO(post_resp.text))
            except Exception as e:
                print("Fail to get file %s:" % fileinfo["path"])
                print("  POST url: %s, data: %s" % (post_url, post_data))
                print("  Request: %s %s" % (post_resp.request.headers, post_resp.request.body))
                print("  Server respond: %d %s" % (post_resp.status_code, post_resp.text))
                continue

            if resp_json["errno"] != 0:
                print("Fail to get file %s:" % fileinfo["path"])
                print("  POST url: %s, data: %s" % (post_url, post_data))
                print("  Request: %s %s" % (post_resp.request.headers, post_resp.request.body))
                print("  Server respond: %s" % (str(resp_json)))
                continue

            yield (Task(
                filename = fileinfo["path"],
                url      = [resp_json["data"]["downloadurl"]],
                opts     = {"header": ["%s: %s" % (k, v) for (k, v) in header.items()]})
            )






