r"""
http://github.com/in4lio/yupp/
 __    __    _____ _____
/\ \  /\ \  /\  _  \  _  \
\ \ \_\/  \_\/  \_\ \ \_\ \
 \ \__  /\____/\  __/\  __/
  \/_/\_\/___/\ \_\/\ \_\/
     \/_/      \/_/  \/_/

yup.py -- shell of yupp preprocessor
"""

from __future__ import division
import os
import sys
import re
import json
import traceback
from argparse import ArgumentParser
import stat

from yugen import log, trace
from yugen import config, yushell, yuinit, yuparse, yueval, RESULT
from yugen import make_ast_readable, reduce_emptiness, replace_steady

from yulic import *                                                                                                    #pylint: disable=wildcard-import
from yuconfig import *                                                                                                 #pylint: disable=wildcard-import,unused-wildcard-import

__version__ = VERSION

#   * * * * * * * * * * * * * * * * * *
#   *                                 *
#   *           S H E L L             *
#   *                                 *
#   * * * * * * * * * * * * * * * * * *


TITLE = r""" __    __    _____ _____
/\ \  /\ \  /\  _  \  _  \  %(description)s
\ \ \_\/  \_\/  \_\ \ \_\ \  %(app)s %(version)s
 \ \__  /\____/\  __/\  __/
  \/_/\_\/___/\ \_\/\ \_\/   %(copyright)s
     \/_/      \/_/  \/_/    %(holder)s (%(email)s)
""" % { 'description' : DESCRIPTION, 'app': APP, 'version': VERSION
      , 'copyright': COPYRIGHT, 'holder': HOLDER, 'email': EMAIL }

PP_I      = '<--'
PP_O      = '-->'
PP_FILE   = '[%s]'
OK        = '* OK *'
FAIL      = '\n%s: %s'
___       = '.' * 79
PROMPT    = '[yupp]# '
REPL_TEST = 'test'
REPL_EXIT = 'exit'

E_YUGEN   = '.yugen'
E_YUCFG   = '.yuconfig'
re_e_yu   = re.compile( r'\.yu(?:-([^.]+))?$', flags = re.IGNORECASE )
E_BAK     = '.bak'
E_AST     = '.ast'

QUIET_HELP = """
do not show usual greeting and other information
"""
QUIET = False

TYPE_OUTPUT_HELP = """
show content of an output file
"""
TYPE_OUTPUT = False

def shell():
    shell.quiet = QUIET
    shell.type_output = TYPE_OUTPUT
    shell.output_dir = ''
#   -- traceback exceptions
    shell.traceback = TRACEBACK

shell()

SYSTEM_EXIT_HELP = 'Moreover, you can pass the arguments through a response file: `yup.py @FILE`.' \
' The preprocessor exit status is a number of unsuccessfully processed files multiplied by 4' \
' or an error of command line arguments (2) or a program execution error (1)' \
' or zero in case of successful execution.'

#   ---------------------------------------------------------------------------
def shell_parse_cli_args():
    argp = ArgumentParser(
      description = 'yupp, %(description)s' % { 'description': DESCRIPTION }
    , version = '%(app)s %(version)s' % { 'app': APP, 'version': VERSION }
    , epilog = SYSTEM_EXIT_HELP
    )
    argp.add_argument( 'files', metavar = 'FILE', type = str, nargs = '*', help = "an input file" )
    argp.add_argument( '-q', '--quiet', action = 'store_true', dest = 'quiet', default = shell.quiet
    , help = QUIET_HELP )
    argp.add_argument( '-d', action = 'append', metavar = 'DIR', dest = 'directory'
    , help = "an import directory" )
    argp.add_argument( '-o', '--output', metavar = 'DIR', dest = 'output_dir', default = ''
    , help = "an output directory" )
#   -- preprocessor options
    argp.add_argument( '--pp-skip-comments', metavar = 'TYPE', type = int, dest = 'pp_skip_comments'
    , choices = range( 0, 4 ), help = PP_SKIP_COMMENTS_HELP )
    argp.add_argument( '--pp-no-trim-app-indent', action = 'store_false', dest = 'pp_trim_app_indent' )
    argp.add_argument( '--pp-trim-app-indent', action = 'store_true', dest = 'pp_trim_app_indent'
    , help = PP_TRIM_APP_INDENT_HELP )
    argp.add_argument( '--pp-no-reduce-emptiness', action = 'store_false', dest = 'pp_reduce_emptiness' )
    argp.add_argument( '--pp-reduce-emptiness', action = 'store_true', dest = 'pp_reduce_emptiness'
    , help = PP_REDUCE_EMPTINESS_HELP )
    argp.add_argument( '--pp-no-browse', action = 'store_false', dest = 'pp_browse' )
    argp.add_argument( '--pp-browse', action = 'store_true', dest = 'pp_browse'
    , help = PP_BROWSE_HELP )
    argp.add_argument( '-Wno-unbound', '--warn-no-unbound-application', action = 'store_false'
    , dest = 'warn_unbound_application' )
    argp.add_argument( '-Wunbound', '--warn-unbound-application', action = 'store_true'
    , dest = 'warn_unbound_application', help = WARN_UNBOUND_APPLICATION_HELP )
#   -- debug options
    argp.add_argument( '-l', '--log', metavar = 'LEVEL', type = int, dest = 'log_level'
    , default = ( LOG_LEVEL ), choices = range( 1, 6 )
    , help = LOG_LEVEL_HELP )
    argp.add_argument( '-t', '--trace', metavar = 'STAGE', type = int, dest = 'trace_stage'
    , default = TRACE_STAGE, choices = range( 0, 4 )
    , help = TRACE_STAGE_HELP )
    argp.add_argument( '-b', '--traceback', metavar = 'TYPE', type = int, dest = 'traceback'
    , default = TRACEBACK, choices = range( 0, 3 )
    , help = TRACEBACK_HELP )
    argp.add_argument( '--type-file', action = 'store_true', dest = 'type_output', default = shell.type_output
    , help = TYPE_OUTPUT_HELP )
    argp.add_argument( '-i', '--input', metavar = 'TEXT', type = str, dest = 'text', default = ''
    , help = "an input text (used by Web Console)" )
    argp.add_argument( '--input-source', metavar = 'NAME', type = str, dest = 'text_source', default = ''
    , help = "an input text source (used by Web Console)" )

    argp.set_defaults(
      directory = []
    , pp_skip_comments = PP_SKIP_COMMENTS
    , pp_trim_app_indent = PP_TRIM_APP_INDENT
    , pp_reduce_emptiness = PP_REDUCE_EMPTINESS
    , pp_browse = PP_BROWSE
    , warn_unbound_application = WARN_UNBOUND_APPLICATION
    )
    if ( len( sys.argv ) == 2 ) and sys.argv[ 1 ].startswith( '@' ):
#       -- get arguments from response file
        try:
            with open( sys.argv[ 1 ][ 1: ], 'r' ) as f:
                return argp.parse_args( f.read().split())

        except IOError as e:
#           -- file operation failure
            log.critical( FAIL, type( e ).__name__, str( e ))
            sys.exit( 2 )

    return argp.parse_args()
#    return argp.parse_args([ '-h' ])

#   ---------------------------------------------------------------------------
def _exec_yuconfig_script( fn_cfg, context ):
    if os.path.isfile( fn_cfg ):
        try:
            execfile( fn_cfg, context )
        except Exception as e:                                                                                         #pylint: disable=broad-except
            log.error( 'unable to execute configuration script\n'
            'File "%s"\n%s: %s', fn_cfg, type( e ).__name__, str( e ))

#   ---------------------------------------------------------------------------
def shell_parse_yuconfig( fn ):
#   -- default configuration
    context = yuconfig_defaults()
    context[ 'directory' ] = []
    context[ 'dependency' ] = []
#   -- global configuration
    _exec_yuconfig_script( '' + E_YUCFG, context )
#   -- configuration for concrete source file
    _exec_yuconfig_script( os.path.splitext( fn )[ 0 ] + E_YUCFG, context )
    cfg = { k: val for k, val in context.items() if isinstance( val, yuconfig_types )}
    if isinstance( context[ 'directory' ], list ):
        cfg[ 'directory' ] = context[ 'directory' ]
    if isinstance( context[ 'dependency' ], list ):
        cfg[ 'dependency' ] = context[ 'dependency' ]
    return cfg

#   ---------------------------------------------------------------------------
def shell_input():
    try:
        return raw_input( PROMPT )

    except ( EOFError, ValueError ):
#       -- e.g. run into environment without terminal input
        print
        return REPL_EXIT

#   ---------------------------------------------------------------------------
def shell_backup( fn ):
    if os.path.isfile( fn ):
        fn_bak = fn + E_BAK
        if os.path.isfile( fn_bak ):
            os.chmod( fn_bak, stat.S_IWRITE )
            os.remove( fn_bak )
        os.rename( fn, fn_bak )

#   ---------------------------------------------------------------------------
def shell_savetofile( fn, text ):
    with open( fn, 'wb' ) as f:
        f.write( text )


#   * * * * * * * * * * * * * * * * * *
#   *                                 *
#   *       P P   W R A P P E R       *
#   *                                 *
#   * * * * * * * * * * * * * * * * * *

#   ---------------------------------------------------------------------------
def _pp_configure( cfg ):
    log.setLevel( cfg.get( 'log_level', LOG_LEVEL ) * LOG_LEVEL__SCALE_ )
    trace.stage = cfg.get( 'trace_stage', TRACE_STAGE )
    config.pp_skip_comments = cfg.get( 'pp_skip_comments', PP_SKIP_COMMENTS )
    config.pp_trim_app_indent = cfg.get( 'pp_trim_app_indent', PP_TRIM_APP_INDENT )
    config.pp_reduce_emptiness = cfg.get( 'pp_reduce_emptiness', PP_REDUCE_EMPTINESS )
    config.pp_browse = cfg.get( 'pp_browse', PP_BROWSE )
    config.warn_unbound_application = cfg.get( 'warn_unbound_application', WARN_UNBOUND_APPLICATION )
    config.directory = cfg.get( 'directory', [])
    shell.quiet = cfg.get( 'quiet', QUIET )
    shell.type_output = cfg.get( 'type_output', TYPE_OUTPUT )
    shell.output_dir = cfg.get( 'output_dir', '' )
    shell.traceback = cfg.get( 'traceback', TRACEBACK )
#debug!!!
#    if log.level != LOG_LEVEL * LOG_LEVEL__SCALE_:
#        print 'log_level', log.level
#    if trace.stage != TRACE_STAGE:
#        print 'stage', trace.stage
#    if config.pp_skip_comments != PP_SKIP_COMMENTS:
#        print 'pp_skip_comments', config.pp_skip_comments
#    if config.pp_trim_app_indent != PP_TRIM_APP_INDENT:
#        print 'pp_trim_app_indent', config.pp_trim_app_indent
#    if config.pp_reduce_emptiness != PP_REDUCE_EMPTINESS:
#        print 'pp_reduce_emptiness', config.pp_reduce_emptiness
#    if config.pp_browse != PP_BROWSE:
#        print 'pp_browse', config.pp_browse
#    if config.warn_unbound_application != WARN_UNBOUND_APPLICATION:
#        print 'warn_unbound_application', config.warn_unbound_application
#    if config.directory != []:
#        print 'directory', config.directory
#    if shell.quiet != QUIET:
#        print 'quiet', shell.quiet
#    if shell.type_output != TYPE_OUTPUT:
#        print 'type_output', shell.type_output
#    if shell.output_dir != '':
#        print 'output_dir', shell.output_dir
#    if shell.traceback != TRACEBACK:
#        print 'traceback', shell.traceback

#   ---------------------------------------------------------------------------
def _pp():                                                                                                             #pylint: disable=too-many-statements
    """
    return yueval( yuparse( yushell.input_file ))
    (also tracing and logging)
    """
#   ---------------
    trace.set_current( TRACE_STAGE_PARSE )
    TR2F = trace.enabled and trace.to_file
    LOG = not trace.enabled or trace.to_file
#   -- parse
    try:
        if TR2F:
            trace.info( yushell.source[ yushell.input_file ][ 1 ])

        ast = yuparse( yushell.input_file )

        if trace.enabled:
            trace.info( repr( ast ))
            trace.info( trace.TEMPL_DEEPEST, trace.deepest )
    except:                                                                                                            #pylint: disable=bare-except
        e_type, e, tb = sys.exc_info()
        msg = '\n'
        arg = e.args[ 0 ] if e.args else None
        if (( shell.traceback == TRACEBACK_ALL ) or
            ( shell.traceback == TRACEBACK_PYTHON ) and isinstance( arg, str ) and arg.startswith( 'python' )):
#           -- enabled traceback
            msg += ''.join( traceback.format_tb( tb ))
        msg += ''.join( traceback.format_exception_only( e_type, e ))
        if TR2F:
            trace.info( msg )
        if LOG:
            log.error( msg )
        if trace.enabled:
            trace.info( trace.TEMPL_DEEPEST, trace.deepest )
        if TR2F:
            trace.info( ___ )
        return False, ''

#   -- eval
    trace.set_current( TRACE_STAGE_EVAL )
    TR2F = trace.enabled and trace.to_file
    LOG = not trace.enabled or trace.to_file
    try:
        plain = yueval( ast )

        ok = isinstance( plain, str )
        if ok:
            plain = replace_steady( reduce_emptiness( plain ))
        else:
            plain = make_ast_readable( plain )
            log.error( 'unable to translate input text into plain text' )
            if yushell.hazard:
                log.warn( 'the following usage of built-in function(s) can be the reason'
                + ''.join( x.loc() for x in yushell.hazard ))
        if trace.enabled:
            trace.info( plain )
            trace.info( trace.TEMPL_DEEPEST, trace.deepest )
    except:                                                                                                            #pylint: disable=bare-except
        e_type, e, tb = sys.exc_info()
        msg = '\n'
        arg = e.args[ 0 ] if e.args else None
        if (( shell.traceback == TRACEBACK_ALL ) or
            ( shell.traceback == TRACEBACK_PYTHON ) and isinstance( arg, str ) and arg.startswith( 'python' )):
#           -- enabled traceback
            msg += ''.join( traceback.format_tb( tb ))
        msg += ''.join( traceback.format_exception_only( e_type, e ))
        if TR2F:
            trace.info( msg )
        if LOG:
            log.error( msg )
        if trace.enabled:
            trace.info( trace.TEMPL_DEEPEST, trace.deepest )
        if TR2F:
            trace.info( ___ )
        return False, ''

    if TR2F:
        trace.info( ___ )
    return ( ok, plain )

#   ---------------------------------------------------------------------------
def _output_fn( fn ):
    fn_o, e = os.path.splitext( os.path.join( shell.output_dir, os.path.basename( fn )) if shell.output_dir else fn )
    if not e:
#   ---- * --> *.yugen
        return fn_o + E_YUGEN

    e_yu = re_e_yu.search( e )
    if e_yu is None:
#   ---- *.* --> *.yugen.*
        return fn_o + E_YUGEN + e

    if e_yu.group( 1 ):
#   ---- *.yu-* --> *.*
        return fn_o + '.' + e_yu.group( 1 )

    if not os.path.splitext( fn_o )[ 1 ]:
#   ---- *.yu --> *.yugen
        return fn_o + E_YUGEN

#   ---- *.*.yu --> *.*
    return fn_o

#   ---------------------------------------------------------------------------
def _pp_stream( _stream, fn, fn_o ):
    ok = False
    plain = None
    try:
        text = _stream.read()
#       -- preprocessing
        yushell( text, fn, fn_o )
        yuinit()
        ok, plain = _pp()
        if ok:
#           -- output file backup
            shell_backup( fn_o )
#           -- output file writing
            shell_savetofile( fn_o, plain )
            os.chmod( fn_o, stat.S_IREAD )
            if isinstance( plain, RESULT ):
#               -- browse writing
                with open( fn_o + '.json', 'w' ) as f:
                    json.dump({
                      'files': sorted( RESULT.files, key=RESULT.files.get )
                    , 'browse': plain.browse
                    , 'offset': plain.offset
                    }, f )
        else:
            if plain:
#               -- plain contains AST
                fn_o = os.path.splitext( fn_o )[ 0 ] + E_AST
#               -- output file writing
                shell_savetofile( fn_o, plain )
                log.warn( 'result was saved as AST file' )

    except IOError as e:
#       -- e.g. file operation failure
        log.critical( FAIL, type( e ).__name__, str( e ))

    return ( ok, plain )

#   ---------------------------------------------------------------------------
def _pp_file( fn ):
    try:
#       -- open input file
        f = open( fn, 'r' )
    except IOError as e:
#       -- e.g. file operation failure
        log.critical( FAIL, type( e ).__name__, str( e ))
        return False

    if not shell.quiet:
        print PP_I, PP_FILE % fn

#   -- figure out a name for output file
    fn_o = _output_fn( fn )

    ok, plain = _pp_stream( f, fn, fn_o )
    f.close()

    print
    if ok:
        if shell.type_output:
            print plain
        if not shell.quiet:
            print PP_O, PP_FILE % fn_o
            print OK
    else:
        if plain:
#           -- plain contains AST
            if shell.type_output:
                print plain
            if not shell.quiet:
                print PP_O, PP_FILE % fn_o
    return ok

#   ---------------------------------------------------------------------------
def _pp_test( text, echo = True ):
    if not text.strip():
#       -- ignore empty text
        return True

    if echo:
        print PP_I, text
    yushell( text )
    yuinit()
    ok, plain = _pp()

    print
    if plain:
        print PP_O, plain
    if ok:
        print OK
    return ok

#   ---------------------------------------------------------------------------
def _pp_text( text, text_source = None ):
    yushell( text, text_source )
    yuinit()
    ok, plain = _pp()

    print
    if plain:
        print plain
    if ok:
        print OK
    return ok

#   ---------------------------------------------------------------------------
def _getmtime( fn ):
    try:
        return os.path.getmtime( fn )

    except Exception as e:
        log.warn( 'unable to check dependency\n%s: %s', type( e ).__name__, str( e ))
        raise

#   ---------------------------------------------------------------------------
def proc_stream( _stream, fn ):
    """
    Stream preprocessing (for Python package).
    """
    _stream.seek( 0 )
#   -- figure out a name for output file
    fn_o = _output_fn( fn )

    cfg = shell_parse_yuconfig( fn )
    _pp_configure( cfg )
#   -- check that we can skip re-preprocessing
    if not cfg.get( 'force', False ) and os.path.isfile( fn_o ):
        try:
            deps = cfg.get( 'dependency', [])
            deps.append( fn )
            t = os.path.getmtime( fn_o )
#           -- if sources of dependencies are not changed...
            if all( _getmtime( d ) < t for d in deps ):
#               -- ...just read output file
                with open( fn_o, 'r' ) as f:
                    data = f.read()
#debug!!!
                print 'skip yupp'
                return ( True, data, fn_o, 1 if 'coding:' in _stream.readline() else 2 )

        except:                                                                                                        #pylint: disable=bare-except
#           -- process input file in the usual way
            pass

    ok, data = _pp_stream( _stream, fn, fn_o )
    return ( ok, data, fn_o, yushell.shrink )

#   ---------------------------------------------------------------------------
def proc_file( fn ):
    """
    File preprocessing (for Python package).
    """
    try:
#       -- open input file
        f = open( fn, 'r' )
    except IOError as e:
#       -- e.g. file operation failure
        log.critical( FAIL, type( e ).__name__, str( e ))
        return ( False, None )

    ok, _, fn_o, _ = proc_stream( f, fn )
    return ( ok, fn_o )

#   ---------------------------------------------------------------------------
if __name__ == '__main__':
    args = shell_parse_cli_args()
    if not args.files:
        args.pp_browse = False
    _pp_configure( args.__dict__ )

    if not shell.quiet:
        print TITLE
#       -- startup testing
        _pp_test( r"""($($\y:u.\m.\...(m y($\C.\p.(r)e p)($\ro.(ce)s)))so r)""" )
        _pp_test( r"""
""" )

    if args.text:
#       -- input text preprocessing
        _pp_text( args.text, args.text_source )

    if args.files:
        f_failed = 0
#       -- input files preprocessing
        for path in args.files:
            if not _pp_file( path ):
                f_failed += 1
#       -- sys.exit() redefined in Web Console
        sys.exit( f_failed << 2 )

    else:
#       -- Read-Eval-Print Loop
        print PROMPT + 'Type "%s" or source code + "%s".' % ( REPL_EXIT, REPL_TEST )
        test = ''
        while True:
            line = shell_input()
            stripped = line.strip()
            if stripped == REPL_EXIT:
#               -- quit REPL
                break
            if stripped == REPL_TEST:
#               -- run preprocessor
                _pp_test( test, False )
                test = ''
            else:
                test += line + '\n'
        sys.exit( 0 )
