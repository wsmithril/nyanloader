"""
aria2c json rpc control class
"""

import urllib.request, urllib.error, urllib.parse, os, socket, subprocess, simplejson as json, signal
from io import StringIO

import config
from plugins.backend.__base__ import BaseBackend, BackendException, task_status

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
    """ Backend for aria2c json rpc server """

    backend     = "aria2c"
    server_port = config.aria2c_port
    server_addr = config.aria2c_addr
    server_url  = "http://%s:%d/jsonrpc" % (server_addr, server_port)

    start_args = [
        "aria2c"
      , "--enable-rpc"
      , "--rpc-listen-port=%d" % server_port
      , "--rpc-listen-all=true"
      , "--rpc-allow-origin-all=true"]
    pid = -1

    # basic aria2c options
    rpc_basic      = {"jsonrpc": "2.0", "id": backend}
    default_option = { "dir": os.getcwd(), "continue": "true"}

    local_start = False

    def __init__(self):
        """ start aria2c server if not started """
        self.process = None
        if self.server_addr != "localhost" and self.server_addr != "127.0.0.1":
            # Raise an exception if the remote server not started
            if self.status() != self.BE_RUNNING:
                raise BackendException("aria2c server on %s not started" % self.server_addr)
        else:
            # try to start server if we are running on local machine
            if self.status() != self.BE_RUNNING:
                self.start_server()
                self.local_start = True
            else:
                print("aria2c server already started")

    def status(self):
        """ querry backend status, return BE_RUNNING or BE_DOWN or BE_NA """
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if s.connect_ex((self.server_addr, self.server_port)) != 0:
            return self.BE_DOWN
        else:
            s.close()
            return self.BE_RUNNING

    def start_server(self):
        """ start aria2c rpc server """
        self.process = subprocess.Popen(self.start_args,
                stdin  = subprocess.PIPE,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE)
        self.process.stdout.close()
        self.process.stderr.close()
        self.process.stdin.close()
        print("aria2c started")

    def __rpc_call__(self, method, params = []):
        json_dict = self.rpc_basic
        json_dict["method"] = method
        json_dict["params"] = params

        # call the rpc server
        try:
            call = urllib.request.urlopen(self.server_url, json.dumps(json_dict))
            resp = json.load(StringIO(call.read()))
            call.close()
        except Exception as e:
            raise BackendException("RPC Failed, call: %r, %s" % (json_dict, str(e)))
        return resp["result"]

    def new_task(self, task):
        local_opt = {"split": len(task.url)}
        if task.filename:
            # when given a filename, use it
            local_opt["out"] = task.filename
        resp = self.__rpc_call__(
                    method = "aria2.addUri"
                  , params = [
                        task.url
                      , dict(list(self.default_option.items())
                           + list(task.opts.items())
                           + list(local_opt.items()))])
        return resp

    def querry_task_status(self, task):
        try:
            resp =  self.__rpc_call__(method = "aria2.tellStatus",
                                     params = [task.key])
        except Exception as e:
            raise BackendException("Qureey status fail.resp: %s" % (str(e)))

        st = status_mapping[resp["status"]]

        task.size           = int(resp["totalLength"])
        task.downloaded     = int(resp["completedLength"])
        task.speed          = int(resp["downloadSpeed"])

        if st == task_status["error"] and resp["errorCode"] == "11":
            return task_status["other"]
        return st

    def terminate(self):
        """ terminate server """
        if not self.local_start:
            return
        if self.server_addr == "localhost" or self.server_addr == "127.0.0.1":
            # only terminate server running on local
            if self.process:
                print("Send SIGTERM to backend [%d]" % self.process.pid)
                self.process.send_signal(signal.SIGTERM)
                print("wait backend to exit")
                self.process.wait()

    def cleanup(self):
        try:
            self.__rpc_call__(method = "aria2.purgeDownloadResult")
        except:
            pass

