#! /bin/env python
# -*- coding: utf-8 -*-

""" Main Control """

import os, os.path as path, sys, argparse
from datetime import datetime
from time import sleep
from task import Task

from plugins.backend import backend, task_status
from plugins.disk import get_class
import config

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def main_loop(url_list):
    """ main loop. Download each url in the url_list """
    current_down = 0

    # downloading task status
    downloading = {}
    error_list  = []

    # download file generator
    tasks = download_task(url_list)
    task  = None

    while True:
        # start main loop
        while current_down <= config.max_concurrency:
            try:
                task = tasks.next()
            except StopIteration:
                break;

            # new task
            print "Starting download [%s]" % (task.filename)
            key = task.start()
            downloading[key] = task
            current_down += 1

        sleep(5)

        # querry task status
        for k, task in downloading.items():
            state = task.status()
            if state == task_status["complete"] or state == task_status["other"]:
                t = downloading.pop(key)
                print "[%s] Completed" % t.filename
                current_down -= 1
            elif state == task_status["error"]:
                t = downloading.pop(key)
                print "[%s] Error" % t.filename
                error_list.append(t)
                current_down -= 1

        if current_down == 0:
            break;

        print
        print "===== Downloading %d items =====" % len(downloading)
        for k, task in downloading.items():
            # show informations
            print "Downloading [%s] @ %5.2fkB/s, %s completed, ETA: %s" % (
                    task.filename,
                    task.speed / 1024.0,
                    task.size == 0 and "n.a." or "%5.2f%%" % (100.0 * task.downloaded / task.size),
                    (task.size == 0 or task.speed == 0) and "n.a." or "%ds" % (1.0 * (task.size - task.downloaded) / task.speed))


    # show all failed tasks
    for t in error_list:
        print "%s Failed" % t.filename

def download_task(url_list):
    """ generator for duwnload urls, yields urls """

    # cookies
    cookies = {}

    for url in url_list:
        brand = get_class(url)
        if not brand:
            print "Cannot parse %s as any of known net-disk providor" % url
            continue;
        else:
            print "%s recorgnized as %s" %(url, brand.brand)

        # get cookies
        try:
            cookie = cookies[brand]
        except KeyError:
            cookie = brand.login()
            cookies[brand] = cookie

        down_url_list = brand.download_info(url, cookie)
        while True:
            try:
                task = down_url_list.next()
            except StopIteration:
                break
            yield task

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
        for line in config.listfile[0].readlines():
            url_list.append(line)
        config.listfile[0].close()

    if config.url:
        url_list.extend(config.url)

    if not url_list:
        arg_parser.print_help()
        print "No url to download"
        exit(3)

    # start main loop
    main_loop(url_list)

