""" Downloader class for f.xunlei.com """

import simplejson as json, re, requests, inspect
from io import StringIO
from os.path import dirname
from time import time
from urllib.parse import quote
from hashlib import md5

import config
from task import Task
from plugins.disk.__base__ import BaseDownloader, BaseDownloaderException

def pass_hash(p, s):
    return md5(md5(md5(p).hexdigest()).hexdigest() + s.upper()).hexdigest()

class Downloader(BaseDownloader):
    brand  = "f.xunlei.com"
    header = {"User-Agent": "Mozilla/5.0 (Windows NT 5.1; rv:10.0) Gecko/20100101 Firefox/10.0"}

    url_id_pattern = re.compile("^(?:http://)?f.xunlei.com/\d+/(?:f/|file/|folder#)[0-9a-f-]+$")
    parser_re      = re.compile("^(?:http://)?f.xunlei.com/(\d+)/(f/|file/|folder#)([0-9a-f-]+)$")

    default_cookie_file = dirname(inspect.getfile(inspect.currentframe())) + "/../../cookies/"  + brand

    cookies = None

    def __init__(self):
        pass

    def login(self, username = config.thunderF_username, password = config.thunderF_password):
        """ use username and password to login
            due to design flaut of in the site, We can actually bypass the verify code,
            for f.xunlei.com provides alternative verify method in their javascript"""
        resp = requests.get("http://login.xunlei.com/check?u=%s&t=%d" % (username, time()), headers = self.header)
        check = resp.cookies["check_result"]
        if check[0:2] == "0:":
            check = check[2:]
        post_data = "u=%s&p=%s&verifycode=%s&login_enable=1&login_hour=336&loginTime=%d" % (
                username # username
            ,   pass_hash(password, check) # password, salted and hashed.
            ,   quote(check) # salt
            ,   time() # timestamp
        )

        resp = requests.post(
                "http://login.xunlei.com/sec2login/?xltime=%d" % time()
            ,   data = post_data
            ,   cookies = resp.cookies, headers = self.header)
        return resp.cookies

    def url_pattern(self, url):
        return self.url_id_pattern.match(url) and True or False

    def download_info(self, url, cookie):
        # parse url
        try:
            user_id, type_seg, node = self.parser_re.match(url).groups()
        except Exception as e:
            raise BaseDownloaderException("Cannot parse %s as %s, url malformated" % (url, self.brand))
        type_seg = type_seg[0:-1]

        # type?
        url_type = None
        if type_seg == "file":
            url_type = self.TYPE_FILE
        elif type_seg == "f" or type_seg == "folder":
            url_type = self.TYPE_FOLDER
        else:
            raise BaseDownloaderException("Cannot parse %s as %s, url malformated" % (url, self.brand))

        # make requests and get url
        num_of_file = 0

        request_url = ""
        if url_type == self.TYPE_FOLDER:
            # get folder content from url
            # http://svr.f.xunlei.com/file/getUserFileList?userId=$user_id&node=$node&needAudit=1
            request_url = "http://svr.f.xunlei.com/file/getUserFileList?userId=%s&node=%d&needAudit=1&callback=" % (user_id, node)
        else:
            # single file
            # http://svr.f.xunlei.com/file/getUserFileList?includingNode=$user_id%3A$node&userId=$user_id
            request_url = "http://svr.f.xunlei.com/file/getUserFileList?callback=&includingNode=%s%%3A%s&userId=%s&onlyFile=1" % (user_id, node, user_id)

        try:
            resp = requests.get(request_url, cookies = cookie, headers = self.header)
        except Exception as e:
            raise BaseDownloaderException("get file list in %s failed, %s" % (url, repr(e)))

        # respond was warped in (), need to remove these
        # accutualy, responded json was warp in xxx(...), where xxx is cgi args passed in callback.
        resp_json = json.load(StringIO(resp.text[1:-1]))

        # server return error?
        if resp_json["rtn"] != 0:
            raise BaseDownloaderException("Resquest file list fail, server return %d: %s" % (resp_json["rtn"], resp_json["data"]["msg"]))

        if url_type == self.TYPE_FOLDER:
            # read file list
            num_of_file = int(resp_json["data"]["nodesTotalNum"])
        else:
            num_of_file = 1

        last_cookies = "Cookie: " + "; ".join("%s=%s" % (k, v) for k, v in list(resp.cookies.items()))

        return (Task(
                 filename = n["name"],
                 url      = [n["url"]],
                 opts     = {"header": [last_cookies] + ["%s: %s" % (k, v) for k, v in list(self.header.items())] + ["Referer: " + url]})
                for n in resp_json["data"]["nodes"]
                if url_type == self.TYPE_FOLDER or n["nodeId"] == node)

