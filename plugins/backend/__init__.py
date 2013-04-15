""" module for backends """

import config
from __base__ import task_status

# import backend module and start backend server
mod = __import__(config.backend, globals(), locals(), [], -1)
backend = mod.Backend()
print "Using backend %s" % backend.backend
