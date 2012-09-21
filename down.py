"""
Main Control
"""

import os, os.path as path,  sys, argparse
from datetime import datetime
from time import sleep

from plugins.disk import get_class
from plugins.backend import backend, task_status
from task import Task
import config

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main_loop(url_list):
    """ main loop. Download each url in the url_list """
    all_done = False
    current_down = 0

    # downloading task status
    downloading = {}

    # download file generator
    down_url_gen = down_url_list(url_list)

    while not all_done:
        # start main loop
        while current_down <= config.max_concurrency:
            try:
                down_url = down_url_gen.next()
            except StopIteration:
                break;

            # new task
            task = Task(down_url["url"], down_url["filename"], down_url["options"])
            print "Starting download %s" % (down_url["filename"])
            key = task.start()
            downloading[key] = task
            current_down += 1

        # querry task status
        for k, task in downloading.items():
            state = task.get_status()
            if state == task_status["complete"]:
                t = downloading.pop(key)
                print "%s Completed"
            else:
        sleep(5)
def down_url_list(url_list):
    """ generator for duwnload urls,
        yields urls """
    # cookies
    cookies = {}

    got_one = False
    for url in url_list:
        brand = get_class(url)
        if not brand:
            print "Cannot parse %s as any of known net-disk providor" % url
            continue;
        else:
            print "%s recorgnized as %s" %(url, brand.brand)

        # get cookies
        try:
            cookie = cookies[brand.brand]
        except KeyError:
            cookie = brand.login()

        down_url_list = brand.download_info(url, cookie)
        try:
            down_url = down_url_list.next()
        except StopIteration:
            continue
            cookies[brand.brand] = cookie
        yield down_url

if __name__ == "__main__":
    # build cli args parser
    arg_parser = argparse.ArgumentParser(description = "Download file from varias net-disk")
    arg_parser.add_argument("-l", "--list-file", type = file, dest = 'listfile', nargs = 1, metavar = "filename", help = "Read url list from file")
    arg_parser.add_argument("-v", "--verbose", action = "count", dest = "loglevel", default = 3)
    arg_parser.add_argument("url" , nargs = "*")

    # parse args to config
    arg_parser.parse_args(sys.argv[1:], namespace = config)

    # get url list for cli arg and list-file
    url_list = []
    if config.listfile:
        for line in config.listfile.readlines():
            url_list.append(line)
    if config.url:
        url_list.extend(config.url)

    if not url_list:
        arg_parser.print_help()
        print "No url to download"
        exit(3)

    # start main loop
    main_loop(url_list)

