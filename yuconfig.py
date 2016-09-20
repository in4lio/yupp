r"""
http://github.com/in4lio/yupp/
 __    __    _____ _____
/\ \  /\ \  /\  _  \  _  \
\ \ \_\/  \_\/  \_\ \ \_\ \
 \ \__  /\____/\  __/\  __/
  \/_/\_\/___/\ \_\/\ \_\/
     \/_/      \/_/  \/_/

yuconfig.py -- configuration of yupp preprocessor
"""

#   -----------------------------------
#   PP_SKIP_COMMENTS
#   -----------------------------------
PP_SKIP_COMMENTS_HELP = """
skip processing of comments: 0 - NONE 1 - C 2 - PYTHON 3 - AUTO
"""
PP_SKIP_COMMENTS_NONE   = 0
PP_SKIP_C_COMMENTS      = 1
PP_SKIP_PYTHON_COMMENTS = 2
PP_SKIP_COMMENTS_AUTO   = 3

PP_SKIP_COMMENTS = PP_SKIP_COMMENTS_NONE

#   -----------------------------------
#   PP_TRIM_APP_INDENT
#   -----------------------------------
PP_TRIM_APP_INDENT_HELP = """
use an application ($ _ ) indent as the base for all substituting lines,
delete a spacing after ($set _ ), ($macro _ ) and ($! _ )
"""
PP_TRIM_APP_INDENT = True

#   -----------------------------------
#   PP_REDUCE_EMPTINESS
#   -----------------------------------
PP_REDUCE_EMPTINESS_HELP = """
reduce an amount of successive empty lines up to one
"""
PP_REDUCE_EMPTINESS = True

#   -----------------------------------
#   PP_BROWSE
#   -----------------------------------
PP_BROWSE_HELP = """
save browse information
"""
PP_BROWSE = False

#   -----------------------------------
#   WARN_UNBOUND_APPLICATION
#   -----------------------------------
WARN_UNBOUND_APPLICATION_HELP = """
warn if an application of unbound atom is detected
"""
WARN_UNBOUND_APPLICATION = True

#   -----------------------------------
#   LOG_LEVEL
#   -----------------------------------
LOG_LEVEL_HELP = """
set a logging level: 1 - DEBUG 2 - INFO 3 - WARNING 4 - ERROR 5 - CRITICAL
"""
LOG_LEVEL_DEBUG    = 1
LOG_LEVEL_INFO     = 2
LOG_LEVEL_WARNING  = 3
LOG_LEVEL_ERROR    = 4
LOG_LEVEL_CRITICAL = 5

LOG_LEVEL = LOG_LEVEL_DEBUG
LOG_LEVEL__SCALE_ = 10

#   -----------------------------------
#   TRACE_STAGE
#   -----------------------------------
TRACE_STAGE_HELP = """
set a tracing stage: 0 - NONE 1 - PARSE 2 - EVAL 3 - BOTH,
tracing of evaluation can take too much time for complicated expressions
"""
TRACE_STAGE_NONE  = 0
TRACE_STAGE_PARSE = 1
TRACE_STAGE_EVAL  = 2
TRACE_STAGE_ALL   = 3

TRACE_STAGE = TRACE_STAGE_NONE

#   -----------------------------------
#   TRACEBACK
#   -----------------------------------
TRACEBACK_HELP = """
set traceback of exceptions: 0 - NONE 1 - PYTHON 2 - ALL
"""
TRACEBACK_NONE   = 0
TRACEBACK_PYTHON = 1
TRACEBACK_ALL    = 2

TRACEBACK = TRACEBACK_PYTHON

#   -----------------------------------
yuconfig_types = ( int, bool )

#   ---------------------------------------------------------------------------
def yuconfig_defaults():
    return {
        k: val for k, val in globals().items()
               if not k.startswith( '__' ) and isinstance( val, yuconfig_types )
    }
