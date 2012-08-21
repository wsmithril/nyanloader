"""
aria2c json rpc control class
"""

import urllib2, os, socket, subprocess, simplejson as json, inspect
import config

from os.path import dirname
from StringIO import StringIO
from __base__ import BaseBackend, BackendException, task_status

# status mapping
status_mapping = {
        "waiting":  0
    ,   "active":   1
    ,   "complete": 2
    ,   "error":    3
    ,   "paused":   4
    ,   "other":    5}

# error codes
error_code = {
        "0":  "If all downloads were successful."
    ,   "1":  "If an unknown error occurred."
    ,   "2":  "If time out occurred."
    ,   "3":  "If a resource was not found."
    ,   "4":  "If aria2 saw the specfied number of \"resource not found\" error. See --max-file-not-found option)."
    ,   "5":  "If a download aborted because download speed was too slow. See --lowest-speed-limit option)"
    ,   "6":  "If network problem occurred."
    ,   "7":  "If there were unfinished downloads. This error is only reported if all finished downloads were successful and there were unfinished downloads in a queue when aria2 exited by pressing Ctrl-C by an user or sending TERM or INT signal."
    ,   "8":  "If remote server did not support resume when resume was required to complete download."
    ,   "9":  "If there was not enough disk space available."
    ,   "10": "If piece length was different from one in .aria2 control file. See --allow-piece-length-change option."
    ,   "11": "If aria2 was downloading same file at that moment."
    ,   "12": "If aria2 was downloading same info hash torrent at that moment."
    ,   "13": "If file already existed. See --allow-overwrite option."
    ,   "14": "If renaming file failed. See --auto-file-renaming option."
    ,   "15": "If aria2 could not open existing file."
    ,   "16": "If aria2 could not create new file or truncate existing file."
    ,   "17": "If file I/O error occurred."
    ,   "18": "If aria2 could not create directory."
    ,   "19": "If name resolution failed."
    ,   "20": "If aria2 could not parse Metalink document."
    ,   "21": "If FTP command failed."
    ,   "22": "If HTTP response header was bad or unexpected."
    ,   "23": "If too many redirections occurred."
    ,   "24": "If HTTP authorization failed."
    ,   "25": "If aria2 could not parse bencoded file(usually .torrent file)."
    ,   "26": "If .torrent file was corrupted or missing information that aria2 needed."
    ,   "27": "If Magnet URI was bad."
    ,   "28": "If bad/unrecognized option was given or unexpected option argument was given."
    ,   "29": "If the remote server was unable to handle the request due to a temporary overloading or maintenance."
    ,   "30": "If aria2 could not parse JSON-RPC request." }

class Backend(BaseBackend):
    """
    Backend for aria2c json rpc server
    """

    backend     = "aria2c"
    server_port = config.aria2c_port
    server_addr = config.aria2c_addr
    server_url  = "http://%s:%d/jsonrpc" % (server_addr, server_port)

    start_args = [
            "aria2c"
        ,   "--enable-rpc"
        ,   "--rpc-listen-port=%d" % server_port
        ,   "--rpc-listen-all=true"
        ,   "--rpc-allow-origin-all=true"
        ,   "--load-cookies=%s" % dirname(inspect.getfile(inspect.currentframe())) + "/../../cookies/cookie"
        ,   "--daemon"]

    pid = -1

    # basic aria2c options
    rpc_basic      = {"jsonrpc": "2.0", "id": backend}
    default_option = { "dir": os.getcwd(), "continue": "true"}

    def __init__(self):
        """ start aria2c server if not started """

        # get cookie file

        if self.server_addr != "localhost" and self.server_addr != "127.0.0.1":
            if self.status() != self.BE_RUNNING:
                raise BackendException("aria2c server on %s not started" % self.server_addr)
            else:
                pass
        else:
            if self.status() != self.BE_RUNNING:
                self.start_server()
            else:
                print "aria2c server already started"

    def status(self):
        """
        querry backend status, return BE_RUNNING or BE_DOWN or BE_NA
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if s.connect_ex((self.server_addr, self.server_port)) != 0:
            return self.BE_DOWN
        else:
            s.close()
            return self.BE_RUNNING

    def start_server(self):
        # start aria2c rpc server
        self.pid = subprocess.Popen(self.start_args, close_fds = True).pid
        print "aria2c started, pid: %d" % self.pid

    def __rpc_call__(self, method, params = []):
        json_dict = self.rpc_basic
        json_dict["method"] = method
        json_dict["params"] = params

        print "json requrst: %r" % json_dict
        # call the rpc server
        try:
            call = urllib2.urlopen(self.server_url, json.dumps(json_dict))
            resp = json.load(StringIO(call.read()))
            call.close()
        except:
            raise BackendException("RPC Failed, call: %r", json_dict)
        return resp["result"]

    def new_task(self, uri, out = None, options = {}):
        local_opt = {"split": len(uri)}
        if out:
            # if filenmane given
            local_opt["out"] = out
        resp = self.__rpc_call__(
                    method = "aria2.addUri"
                ,   params = [
                        uri
                      , dict(self.default_option.items()
                           + options.items()
                           + local_opt.items())])
        return resp

    def querry_task_status(self, GID):
        try:
            resp =  self.__rpc_call__(method = "aria2.tellStatus",
                                     params = [GID])
        except Exception as e:
            raise BackendException("Qureey status fail. %s" % repr(e))

        st = status_mapping[resp["status"]]
        if st == task_status["error"]:
            if resp["errorCode"] == "11":
                st = task_status["other"]
            return {
                    "status": st
                ,   "errno": resp["errorCode"]
                ,   "errmsg": error_code[resp["errorCode"]]}
        else:
            return st

    def cleanup(self):
        try:
            self.__rpc_call__(method = "aria2.purgeDownloadResult")
        except:
            pass

