r"""
http://github.com/in4lio/yupp/
 __    __    _____ _____
/\ \  /\ \  /\  _  \  _  \
\ \ \_\/  \_\/  \_\ \ \_\ \
 \ \__  /\____/\  __/\  __/
  \/_/\_\/___/\ \_\/\ \_\/
     \/_/      \/_/  \/_/

__main__.py -- console script of yupp preprocessor
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import sys

from .pp.yup import cli

#   ---------------------------------------------------------------------------
def main():
    cli( sys.argv[ 1: ])

#   ---------------------------------------------------------------------------
if __name__ == '__main__':
    main()
