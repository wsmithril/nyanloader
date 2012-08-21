"""
module for backends
"""

import config
from __base__ import task_status

# import backend module and start backend server
backend = __import__(config.backend, globals(), locals(), [], -1).Backend()

