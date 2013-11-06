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

    def download_info(self, url, cookies = {}):
        # extract filelist json from page
        try:
            page = requests.get(url, headers = Downloader.header)
        except Exception as e:
            raise BaseDownloaderException("Fail to get page %s\n%s" % (e, str(e)))

        if page.text.find("rootFileList") > 0:
            yield from Downloader.filelist_from_dir(page.text, url)
        else:
            yield Downloader.filelist_form_singlefile(page.text, url)

    @staticmethod
    def post_for_link(referer, domain, surl, fileinfo):
        post_url  = "http://%s/share/downloadfile/" % domain
        post_data = format_payload(surl, fileinfo["nid"])
        try:
            header = dict(list(Downloader.header.items()) + [
                ("Referer", referer),
                ("Content-Type", "application/x-www-form-urlencoded UTF-8; charset=UTF-8"),
            ])

            post_resp = requests.post(post_url, data = post_data, headers = header, cookies = {})
            resp_json = json.load(StringIO(post_resp.text))
        except Exception as e:
            raise BaseDownloaderException("\n".join([
                ["  POST url: %s, data: %s" % (post_url, post_data)],
                ["  Request: %s %s" % (post_resp.request.headers, post_resp.request.body)],
                ["  Server respond: %d %s" % (post_resp.status_code, post_resp.text)],
            ]))

        if resp_json["errno"] != 0:
            raise BaseDownloaderException("\n".join([
                ["  POST url: %s, data: %s" % (post_url, post_data)],
                ["  Request: %s %s" % (post_resp.request.headers, post_resp.request.body)],
                ["  Server respond: %d %s" % (post_resp.status_code, post_resp.text)],
            ]))

        return (Task(
            filename = fileinfo["path"],
            url      = [resp_json["data"]["downloadurl"]],
            opts     = {"header": ["%s: %s" % (k, v) for (k, v) in Downloader.header.items()] + [
                            "Referer: %s" % referer,
                            "Cookie: %s" % '; '.join("%s=%s" % (k,v) for (k, v) in post_resp.cookies.get_dict().items())
        ]}))

    @staticmethod
    def filelist_from_dir(page, url):
        # short URL
        try:
            domain, shorturl = re.compile(r'(?:http://)?((?:\w+\.)?l\d+\.yunpan.cn)/lk/(.+)$').search(url).group(1, 2)
        except Exception as e:
            raise BaseDownloaderException("Malform URL: %s, no shortur or domain" % (s, str(e)))

        rootFileList = extract_filelist_json(page)
        if not rootFileList:
            raise BaseDownloaderException("Url %s has no file in it" % s)

        for fileinfo in rootFileList:
            try:
                yield Downloader.post_for_link(url, domain, shorturl, fileinfo)
            except Exception as e:
                print("Fail to get file %s:\n%s" % (fileinfo["path"], str(e)))
                continue

        raise StopIteration

    @staticmethod
    def filelist_form_singlefile(page, url):
        try:
            domain = re.compile(r'(?:http://)?((?:\w+\.)?l\d+\.yunpan.cn)/lk/.+$').search(url).group(1)
        except Exception as e:
            raise BaseDownloaderException("Malform URL: %s, no shortur or domain" % (s, str(e)))

        try:
            surl = re.compile(r"surl\s*:\s*'(\w+)',?").search(page).group(1)
            nid  = re.compile(r"nid\s*:\s*'(\d+)',?").search(page).group(1)
            name = re.compile(r"name\s*:\s*'((?:[^']|\\')+)',?").search(page).group(1)
        except Exception as e:
            raise BaseDownloaderException("Url: %s has no file.\n%s" % (url, str(e)))

        return Downloader.post_for_link(url, domain, surl, {"nid": nid, "path": name})


