"""
module for backends
"""

import config

# import backend module and start backend server
backend = __import__(config.backend, globals(), locals(), [], -1).Backend()

task_status = {
        "waiting":  0
    ,   "active":   1
    ,   "complete": 2
    ,   "error":    3
    ,   "paused":   4
    ,   "other":    5}

