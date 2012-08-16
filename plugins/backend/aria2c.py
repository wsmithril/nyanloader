"""
aria2c json rpc control class
"""

import urllib2, os, socket, subprocess
import simplejson as json
from StringIO import StringIO
import config
from __base__ import BaseBackend, BackendException

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
        ,   "--daemon"]

    pid = -1

    # basic aria2c options
    rpc_basic      = {"jsonrpc": "2.0", "id": backend}
    default_option = { "dir": os.getcwd(), "continue": "true"}

    def __init__(self):
        """
        start aria2c server if not started
        """
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

        # call the rpc server
        try:
            call = urllib2.urlopen(self.server_url, json.dumps(json_dict))
            resp = json.load(StringO(call.read()))
            call.close()
        except:
            raise BackendException("RPC Failed, call: %r", json_dict)
        return resp

    def new_task(self, uri, option = {}):
        local_opt = {"split": len(uri)}
        resp = self.__rpc_call__(
                    method = "aria2.addUri"
                ,   params = [
                        uri
                      , dict(self.default_option.items()
                           + option.items()
                           + local_opt.items())])
        return resp["result"]

    def querry_task_status(self, GID):
        return self.__rpc_call__(method = "aria2.tellStatus",
                                 params = [GID])

    def cleanup(self):
        return self.__rpc_call__(method = "aria2.purgeDownloadResult")

