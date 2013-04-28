""" module for backends """

import config
import importlib

# import backend module and start backend server
mod     = importlib.import_module("plugins.backend." + config.backend)

backend     = mod.Backend()
task_status = mod.task_status
print("Using backend %s" % backend.backend)

