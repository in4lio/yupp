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

import sys

from .pp.yup import cli

#   ---------------------------------------------------------------------------
def main():
    return cli( sys.argv[ 1: ])

#   ---------------------------------------------------------------------------
if __name__ == '__main__':
    raise SystemExit( main())
