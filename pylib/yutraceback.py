from __future__ import absolute_import

import sys

if sys.version_info[0] < 3:
    from .yutraceback2 import *
else:
    from .yutraceback3 import *
