""" module for backends """

import config

# import backend module and start backend server
mod     = __import__(config.backend, globals(), locals(), [], -1)

backend     = mod.Backend()
task_status = mod.task_status
print "Using backend %s" % backend.backend

