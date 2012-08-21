"""
Main Control
"""

import os, os.path as path,  sys, argparse
from datetime import datetime

from plugins.disk import get_class
from plugins.backend import backend, task_status
from task import Task
import config

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main_loop(url_list):
    """ main loop. Download each url in the url_list """
    all_done = False
    all_down = False
    current_down = 0

    # url_list to generator
    url_gen = (u for u in url_list)

    # down_file_gen begin with an empty generator
    down_file_gen = (i for i in [])

    # downloading task status
    downloading = {}

    # cookies
    cookies = {}

    while not all_done:
        # start main loop
        while not all_down and current_down <= config.max_concurrency:
            pass_this = False
            try:
                down_url = down_file_gen.next()
                print down_url
            except StopIteration:
                # get next url
                try:
                    url  = url_gen.next()
                except StopIteration:
                    all_down = True
                    break

                # get brand of net-disk from url
                brand = get_class(url)
                if not brand:
                    print "%s not recorgnized as any known net-disk, skipped" % url
                    pass_this = True
                else:
                    print "%s recorgnized as %s" % (url, brand.brand)

                    # get cookie if not logged in
                    try:
                        cookie = cookies[brand.brand]
                    except KeyError:
                        cookie = brand.login()
                        cookies[brand.brand] = cookie

                    # parse url
                    try:
                        down_file_gen = brand.download_info(url, cookie)
                    except Exception as e:
                        print "Cannot parse url %s as %s, skipped" % (url, brand.brand)
                        print "Error: " + str(e)

                # pass this loop
                pass_this = True

            if pass_this:
                continue

            # new task
            task = Task(down_url["url"], down_url["filename"])
            print "Starting download %s from %s" % (down_url["filename"], url)
            key = task.start()
            downloading[key] = task


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

