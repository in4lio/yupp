r"""
http://github.com/in4lio/yupp/
 __    __    _____ _____
/\ \  /\ \  /\  _  \  _  \
\ \ \_\/  \_\/  \_\ \ \_\ \
 \ \__  /\____/\  __/\  __/
  \/_/\_\/___/\ \_\/\ \_\/
     \/_/      \/_/  \/_/

yugen.py -- an implementation of yupp preprocessor in Python
"""

from __future__ import division
import sys
import os
import tempfile
import logging
import inspect
import copy
import re
import imp
import string                                                                                                          #pylint: disable=deprecated-module
import operator
import math
import datetime
import zlib
from textwrap import dedent
from ast import NodeVisitor
from ast import parse
from ast import literal_eval

from yulic import *                                                                                                    #pylint: disable=wildcard-import,unused-wildcard-import
from yuconfig import *                                                                                                 #pylint: disable=wildcard-import,unused-wildcard-import

sys.setrecursionlimit( 2 ** 20 )

#   ---------------------------------------------------------------------------
def config():
    config.pp_skip_comments = PP_SKIP_COMMENTS
    config.pp_trim_app_indent = PP_TRIM_APP_INDENT
    config.pp_reduce_emptiness = PP_REDUCE_EMPTINESS
    config.pp_browse = PP_BROWSE
    config.warn_unbound_application = WARN_UNBOUND_APPLICATION
    config.directory = []

config()


#   * * * * * * * * * * * * * * * * * *
#   *                                 *
#   *            D E B U G            *
#   *                                 *
#   * * * * * * * * * * * * * * * * * *

ERR_SLICE = 64
APP_DELIMIT = ' <-- '

#   ---------------------------------------------------------------------------
def callee():
    return inspect.getouterframes( inspect.currentframe())[ 1 ][ 1:4 ][ 2 ]

#   ---------------------------------------------------------------------------
def _create_logger( name, handler, _format ):
    l = logging.getLogger( name )
    handler.setFormatter( logging.Formatter( _format ))
    l.addHandler( handler )
    return l

#   -----------------------------------
#   Logging
#   -----------------------------------

LOG_FORMAT = '* %(levelname)s * %(message)s'

log = _create_logger( 'log', logging.StreamHandler( sys.stdout ), LOG_FORMAT )
log.setLevel( LOG_LEVEL * LOG_LEVEL__SCALE_ )

#   -----------------------------------
#   Trace parsing and evaluation
#   -----------------------------------

TRACE_FORMAT = '%(message)s'

#   -- write trace into a temporary file, if None - into stdout
TRACE_FILE = 'yupp.trace'

#   ---------------------------------------------------------------------------
def _create_trace( default_stage ):
    _to_file = TRACE_FILE is not None
    if _to_file:
        try:
            fn = os.path.join( tempfile.gettempdir(), TRACE_FILE )
            hl = logging.FileHandler( fn, mode = 'w' )
        except ( OSError, NotImplementedError ):
#           -- e.g. permission denied
            _to_file = False
    if not _to_file:
        hl = logging.StreamHandler( sys.stdout )                                                                       #pylint: disable=redefined-variable-type

    _trace = _create_logger( 'trace', hl, TRACE_FORMAT )
    _trace.to_file = _to_file
#   -- default trace
    _trace.stage = default_stage
    _trace.enabled = False
    _trace.TEMPL_DEEPEST = 'deepest call - %d'
    _trace.set_current = _trace_set_current.__get__( _trace, _trace.__class__ )                                        #pylint: disable=no-member
    _trace.set_current( TRACE_STAGE_NONE )
    return _trace

#   ---------------------------------------------------------------------------
def _trace_set_current( self, _stage ):
    if self.stage & _stage:
        self.enabled = True
        self.setLevel( logging.INFO )
    else:
        self.enabled = False
        self.setLevel( logging.WARNING )
    self.deepest = 0

trace = _create_trace( TRACE_STAGE )

TR_INDENT = '.'
TR_DELIMIT  = ' <--\n'
TR_EVAL_IN  = ' E <--\n'
TR_EVAL_ENV = '<< '
TR_EVAL_OUT = ' E -->\n'
TR_SLICE = 64

#   ---------------------------------------------------------------------------
def _ast_pretty( st ):
    """
    AST string beautifying.
    """
    WRAP = 100
    INDENT = '  '
    indent_l = len( INDENT )
    parenth = {}
    p = {}
    depth = 0
    for i, ch in enumerate( st ):
        if ch in ( ')', ']', '}' ):
            if depth:
                depth -= 1
#               -- opening bracket position
                parenth[ p[ depth ]] = ( i, depth )
#               -- closing bracket position
                parenth[ i ] = ( None, depth )
        else:
            if ch in ( '(', '[', '{' ):
                p[ depth ] = i
                depth += 1
    result = ''
    i = 0
    for b in sorted( parenth ):
        if i <= b:
            e, depth = parenth[ b ]
            if e is None:
#               -- closing bracket
                if i == b:
#                   -- ... only
                    result += INDENT * depth + st[ i : b + 1 ] + '\n'
                else:
                    result += INDENT * ( depth + 1 ) + st[ i : b ] + '\n' + INDENT * depth + st[ b ]  + '\n'
            else:
#               -- opening bracket
                if e - b + ( indent_l * depth ) < WRAP:
#                   -- don't prettify short node
                    b = e
                result += INDENT * depth + st[ i : b + 1 ] + '\n'
            i = b + 1
    result += st[ i: ]
    return result


#   * * * * * * * * * * * * * * * * * *
#   *                                 *
#   *              A S T              *
#   *                                 *
#   * * * * * * * * * * * * * * * * * *

LOC_FILE = '\n  File "%s", line %d'
LOC_MACRO = '\n  Macro "%s", line %d'
LOC_LINE = '\n    %s'
LOC_REPR = ': %s'

#   ---------------------------------------------------------------------------
def _loc_repr( x ):
    return LOC_REPR % ( repr( x )[ :ERR_SLICE ])

#   ---------------------------------------------------------------------------
def _loc( input_file, pos, pointer = True ):
    result = ''
    decl, sou = yushell.source[ input_file ]
    if input_file.isdigit():
#       -- location is into macro or eval import
        call = yushell.inclusion[ int( input_file )]
        if call:
#           -- call location
            result += _loc( call.input_file, call.pos, False )
#       -- macro or eval import location
        result += _loc( decl.input_file, decl.pos, False )
        fmt = LOC_MACRO
    else:
        if not decl:
            decl = input_file
        fmt = LOC_FILE
#   -- location of target
    eol = sou.find( EOL, pos )
    if eol == -1:
        eol = len( sou )
    lnlist = sou[ :eol ].splitlines()
    result += fmt % ( decl, len( lnlist ))
    ln = lnlist[ -1 ].lstrip() if lnlist else '<not found>'
    result += LOC_LINE % ( ln )
    if pointer:
#       -- pointer to target
        lnp = ' ' * ( pos - eol + len( ln )) + '^'
        result += LOC_LINE % ( lnp )
    return result

#   ---------------------------------------------------------------------------
class SOURCE( str ):
    """
    Source text.
    """
#   -----------------------------------
    def __new__( cls, val, input_file = None, pos = 0 ):
        obj = str.__new__( cls, val )
        if isinstance( val, SOURCE ):
            obj.input_file = val.input_file
            obj.pos = val.pos
        else:
            obj.input_file = input_file
            obj.pos = pos
        return obj

#   -----------------------------------
    def __getitem__( self, a ):
        d = a if not isinstance( a, slice ) else a.start if a.start else 0
        return SOURCE( str.__getitem__( self, a ), self.input_file, self.pos + d )

#   -----------------------------------
    def __getslice__( self, a, b ):
        return SOURCE( str.__getslice__( self, a, b ), self.input_file, self.pos + a )

#   -----------------------------------
    def loc( self ):
        return _loc( self.input_file, self.pos ) if self.input_file else _loc_repr( self )

#   ---------------------------------------------------------------------------
class BASE_STR( SOURCE ):
    """
    AST: abstract parent for nodes based on string type
    """
#   -----------------------------------
    def __repr__( self ):
        return '%s(%s)' % ( self.__class__.__name__, str.__repr__( self ))

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, str ) and str.__eq__( self, other )

#   ---------------------------------------------------------------------------
class ATOM( BASE_STR ):
    """
    AST: ATOM( str ) <-- atom
    """
#   -----------------------------------
    def is_valid_c_id( self ):
        return '-' not in self

#   ---------------------------------------------------------------------------
class REMARK( BASE_STR ):
    """
    AST: REMARK( str ) <-- /* ___ */
                           // ___
                           # ___
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class STR( BASE_STR ):
    """
    AST: STR( str ) <-- '___'
                        "___"
                        (`___)
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class PLAIN( BASE_STR ):
    """
    AST: PLAIN( str ) <-- all not parsed
    """
#   -----------------------------------
    def __new__( cls, val, indent = False, trim = False ):
        """
        indent (before the next node):
            None  - PLAIN consists of TABs and SPACEs
            str   - indent at the end of PLAIN, e.g. indent equals to '\t  ' for 'foo\n\t  '
            False - no indent, e.g. indent equals to False for 'foo  '
        """
        obj = BASE_STR.__new__( cls, val )
        obj.indent = indent
        obj.trim = trim
        return obj

#   -----------------------------------
    def get_trimmed( self ):
        st = str( self )

        if config.pp_trim_app_indent and self.trim:
#           -- delete spacing after SET or MACRO
            return st.lstrip()

        return st

#   -----------------------------------
    def get_trimmed_with_browse( self ):
        if config.pp_trim_app_indent and self.trim:
#           -- delete spacing after SET or MACRO
            return self[ len( self ) - len( self.lstrip()): ]

        return self

#   -----------------------------------
    def add_indent( self, indent ):
        if self.indent is not None:
            ln = self.splitlines( True )
            if ord( self[ -1 ]) in ps_EOL:
                ln.append( '' )
            return PLAIN( indent.join( ln )
            , ( indent + self.indent ) if isinstance( self.indent, str ) else self.indent, self.trim )

        return self

#   ---------------------------------------------------------------------------
class BASE_LIST( list ):
    """
    AST: abstract parent for nodes based on list type
    """
#   -----------------------------------
    def __repr__( self ):
        return '%s(%s)' % ( self.__class__.__name__, list.__repr__( self ))

#   -----------------------------------
    def loc( self ):
        return _loc_repr( self )

#   ---------------------------------------------------------------------------
class LIST( BASE_LIST ):
    """
    AST: LIST([ form | EMBED( form )]) <-- ( ___ )
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class FLOAT( float ):
    """
    AST: FLOAT( number )
    """
#   -----------------------------------
    def __repr__( self ):
        return '%s(%s)' % ( self.__class__.__name__, float.__repr__( self ))

#   -----------------------------------
    def loc( self ):
        return _loc_repr( self )

#   ---------------------------------------------------------------------------
class INT( long ):
    """
    AST: INT( number )
    """
#   -----------------------------------
    def __repr__( self ):
        return '%s(%s)' % ( self.__class__.__name__, long.__repr__( self ))

#   -----------------------------------
    def loc( self ):
        return _loc_repr( self )

#   ---------------------------------------------------------------------------
class BASE_OBJECT( object ):
    """
    AST: abstract parent for compound nodes
    """
#   -----------------------------------
    def loc( self ):
        return _loc_repr( self )

#   ---------------------------------------------------------------------------
class BASE_OBJECT_LOCATED( object ):
    """
    AST: abstract parent for locatable compound nodes
    """
#   -----------------------------------
    def __init__( self, input_file, pos ):
        self.input_file = input_file
        self.pos = pos

#   -----------------------------------
    def loc( self ):
        return _loc( self.input_file, self.pos ) if self.input_file else _loc_repr( self )

#   ---------------------------------------------------------------------------
class BASE_MARK( BASE_OBJECT ):
    """
    AST: abstract parent for markers
    """
#   -----------------------------------
    def __repr__( self ):
        return '%s()' % ( self.__class__.__name__ )

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ )

#   ---------------------------------------------------------------------------
class LATE_BOUNDED( BASE_MARK ):
    """
    AST: LATE_BOUNDED() <-- &atom
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class COMMENT( BASE_MARK ):
    """
    AST: COMMENT() <-- ($! ___ )
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class IMPORT_BEGIN( BASE_MARK ):
    """
    AST: begin of imported text
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class IMPORT_END( BASE_MARK ):
    """
    AST: end of imported text
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class CAPTION( object ):
    """
    AST: abstract parent for headers
    """
#   -----------------------------------
    def __init__( self, ast ):
        self.ast = ast

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s)' % ( self.__class__.__name__, repr( self.ast ))

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ ) and ( self.ast == other.ast )

#   ---------------------------------------------------------------------------
class EVAL( BASE_OBJECT, CAPTION ):
    """
    AST: EVAL( APPLY ) <-- ($$ ___ )
    """
#   -----------------------------------
    def __init__( self, ast, decl = None, call = None ):
        CAPTION.__init__( self, ast )
        self.decl = decl
        self.call = call

#   ---------------------------------------------------------------------------
class INFIX( BASE_OBJECT_LOCATED, CAPTION ):
    """
    AST: INFIX( expr ) <-- { ___ }
    """
#   -----------------------------------
    def __init__( self, ast, input_file = None, pos = 0 ):
        BASE_OBJECT_LOCATED.__init__( self, input_file, pos )
        CAPTION.__init__( self, ast )

#   ---------------------------------------------------------------------------
class EMBED( BASE_OBJECT, CAPTION ):
    """
    AST: EMBED( form ) <-- * ___
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class TEXT( BASE_OBJECT ):
    """
    AST: TEXT([ SET | MACRO | APPLY | STR | REMARK | PLAIN ]) <-- [ ___ ]
                                                                  ]<EOL> ___ <EOL>[
    """
#   -----------------------------------
    def __init__( self, ast, pth_sq = 0, pth = 0 ):
        self.ast = ast
        self.depth_pth_sq = pth_sq
        self.depth_pth = pth

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %d, %d)' % ( self.__class__.__name__, repr( self.ast ), self.depth_pth_sq, self.depth_pth )

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ ) and ( self.ast == other.ast )

#   -----------------------------------
    def enclose_import( self ):
        if self.ast:
            self.ast.insert( 0, IMPORT_BEGIN())
            self.ast.append( IMPORT_END())

#   -----------------------------------
    def extend_text( self, pos, lst ):
        if self.ast:
            self.ast[ pos:pos ] = lst

#   ---------------------------------------------------------------------------
class VAR( BASE_OBJECT ):
    """
    AST: VAR( LATE_BOUNDED | [ ATOM ], ATOM ) <-- &atom
                                                  atom
                                                  atom::atom
    """
#   -----------------------------------
    def __init__( self, reg, atom ):
        self.reg = reg
        self.atom = atom

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s)' % ( self.__class__.__name__, repr( self.reg ), repr( self.atom ))

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ ) and ( self.reg == other.reg ) and ( self.atom == other.atom )

#   ---------------------------------------------------------------------------
class APPLY( BASE_OBJECT_LOCATED ):
    """
    AST: APPLY( form, [ form ], [ ( ATOM, form ) ]) <-- ($ ___ )
    """
#   -----------------------------------
    def __init__( self, fn, args, named, input_file = None, pos = 0 ):                                                 #pylint: disable=too-many-arguments
        BASE_OBJECT_LOCATED.__init__( self, input_file, pos )
        self.fn = fn
        self.args = args
        self.named = named

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s, %s)' % ( self.__class__.__name__, repr( self.fn ), repr( self.args ), repr( self.named ))

#   -----------------------------------
    def __eq__( self, other ):
        return ( isinstance( other, self.__class__ ) and ( self.fn == other.fn ) and ( self.args == other.args )
        and ( self.named == other.named ))

#   ---------------------------------------------------------------------------
class SET( BASE_OBJECT ):
    """
    AST: SET( ATOM | [ ATOM ], form ) <-- ($set ___ )
    """
#   -----------------------------------
    def __init__( self, lval, ast ):
        self.lval = lval
        self.ast = ast

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s)' % ( self.__class__.__name__, repr( self.lval ), repr( self.ast ))

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ ) and ( self.lval == other.lval ) and ( self.ast == other.ast )

#   ---------------------------------------------------------------------------
class MACRO( BASE_OBJECT ):
    """
    AST: MACRO( ATOM, [ ATOM ], str ) <-- ($macro ___ )
    """
#   -----------------------------------
    def __init__( self, name, pars, text ):
        self.name = name
        self.pars = pars
        self.text = text

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s, %s)' % ( self.__class__.__name__, repr( self.name ), repr( self.pars ), repr( self.text ))

#   -----------------------------------
    def __eq__( self, other ):
        return ( isinstance( other, self.__class__ ) and ( self.name == other.name ) and ( self.pars == other.pars )
        and ( self.text == other.text ))

#   ---------------------------------------------------------------------------
class EMIT( BASE_OBJECT ):
    """
    AST: EMIT( ATOM, form ) <-- ($emit ___ )
    """
#   -----------------------------------
    def __init__( self, var, ast ):
        self.var = var
        self.ast = ast

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s)' % ( self.__class__.__name__, repr( self.var ), repr( self.ast ))

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ ) and ( self.var == other.var ) and ( self.ast == other.ast )

#   ---------------------------------------------------------------------------
class LAMBDA( BASE_OBJECT ):
    r"""
    AST: LAMBDA([ ([ ATOM ], ATOM, form ) ], TEXT | APPLY | LIST | INFIX ) <-- \_:_.\_:_.___
    """
#   -----------------------------------
    def __init__( self, bound, l_form ):
        self.bound = bound
        self.l_form = l_form

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s)' % ( self.__class__.__name__, repr( self.bound ), repr( self.l_form ))

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ ) and ( self.bound == other.bound ) and ( self.l_form == other.l_form )

#   ---------------------------------------------------------------------------
class COND( BASE_OBJECT ):
    """
    AST: COND( former, former, form ) <-- ___ ? ___ | ___
    """
#   -----------------------------------
    def __init__( self, cond, leg_1, leg_0 ):
        self.cond = cond
        self.leg_1 = leg_1
        self.leg_0 = leg_0

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s, %s)' % ( self.__class__.__name__, repr( self.cond ), repr( self.leg_1 ), repr( self.leg_0 ))

#   -----------------------------------
    def __eq__( self, other ):
        return ( isinstance( other, self.__class__ ) and ( self.cond == other.cond ) and ( self.leg_1 == other.leg_1 )
        and ( self.leg_0 == other.leg_0 ))


#   * * * * * * * * * * * * * * * * * *
#   *                                 *
#   *            P A R S E            *
#   *                                 *
#   * * * * * * * * * * * * * * * * * *

#   -----------------------------------
#   Terminal symbols
#   -----------------------------------

#   ---------------------------------------------------------------------------
def ps_term( _ ):
    """
    ANY ::= [ '\n', '\r', '\t', '\x20'..'\xFF' ];
    string ::= '"' { CHAR YIELD | char_code }0... '"';
    char ::= '\'' { CHAR YIELD | char_code }0... '\'';
    CHAR ::= ANY - EOL - [ '\\', '\t' ];
    char_code ::= '\\n' | '\\r' | '\\t' | '\\\\'
        | '\\' { [ '0'..'7' ] }1..4
        | '\\x' { [ '0'..'9', 'A'..'F', 'a'..'f' ] }1..4;
    EMBED ::= '*';
    """
#   ---------------
    pass

#   ---- EOL
EOL = '\n'
ps_EOL = frozenset([ ord( EOL ), ord( '\r' )])
#   ---- SPACE | TAB
ps_SPACE = frozenset([ ord( ' ' ), ord( '\t' )])
#   ---- any Roman letter | _
ps_LETTER = frozenset( range( ord( 'a' ), ord( 'z' ) + 1 ) + range( ord( 'A' ), ord( 'Z' ) + 1 ) + [ ord( '_' )])
#   ---- any figure
ps_FIGURE = frozenset( range( ord( '0' ), ord( '9' ) + 1 ) + [ ord( '-' )])
#   ---- any printable character
ps_ANY = frozenset([ ord( EOL ), ord( '\r' ), ord( '\t' )] + range( ord( ' ' ), 256 ))
#   ---- code mark
ps_CODE = '($code'
l_CODE = len( ps_CODE )
#   ---- code double comma mark
ps_DUALCOMMA = ',,'
l_DUALCOMMA = len( ps_DUALCOMMA )
#   ---- code end mark
ps_DUALSEMI = ';;'
l_DUALSEMI = len( ps_DUALSEMI )
#   ---- infix mark
ps_INFIX = '(${}'
l_INFIX = len( ps_INFIX )
#   ---- set mark
ps_SET = '($set'
l_SET = len( ps_SET )
#   ---- set tag
ps_SET_T = '\\set'
l_SET_T = len( ps_SET_T )
#   ---- import mark
ps_IMPORT = '($import'
l_IMPORT = len( ps_IMPORT )
#   ---- import tag
ps_IMPORT_T = '\\import'
l_IMPORT_T = len( ps_IMPORT_T )
#   ---- quote mark
ps_QUOTE = '($quote'
l_QUOTE = len( ps_QUOTE )
#   ---- backquote mark
ps_BQUOTE = '(`'
l_BQUOTE = len( ps_BQUOTE )
#   ---- macro mark
ps_MACRO = '($macro'
l_MACRO = len( ps_MACRO )
#   ---- comment mark
ps_COMMENT = '($!'
l_COMMENT = len( ps_COMMENT )
#   ---- emit mark
ps_EMIT = '($emit'
l_EMIT = len( ps_EMIT )
#   ---- emit tag
ps_EMIT_T = '\\emit'
l_EMIT_T = len( ps_EMIT_T )
#   ---- embed character
ps_EMBED = '*'
#   ---- integer number
re_INT = re.compile( r"""
^[+-]?[ \t]*(?:
    0[xX][\da-fA-F]+[lL]?  #  hexadecimal
  | 0[bB][01]+             #  binary
  | 0[oO][0-7]+            #  octal
  | 0[0-7]*                #  octal
  | [1-9]\d*               #  decimal
)[lL]?
""", re.VERBOSE )
#   ---- float
re_FLOAT = re.compile( r'^[+-]? *(?:\d+(?:\.\d+))(?:[eE][+-]?\d+)?' )
#   ---- string literal
re_STR = re.compile( r'^"(?:\\.|[^\\"])*"' )
#   ---- character literal
re_CHR = re.compile( r"^'(?:\\.|[^\\'])*'" )
#   ---- coding (Python)
re_CODING = re.compile( r'coding:\s*yupp(\.[\-_a-zA-Z0-9]+)?(?:\W|$)', re.IGNORECASE )
ps_CODING = 'yupp.'
l_CODING = len( ps_CODING )

E_PY = '.py'
#   -----------------------------------
#   Grammar rules
#   -----------------------------------

#   ---------------------------------------------------------------------------
def _ord( sou, pos = 0 ):
    return ord( sou[ pos ]) if pos < len( sou ) else None

#   ---------------------------------------------------------------------------
def _unq( st ):
    if isinstance( st, str ):
        try:
            if st.startswith( '"' ) or st.startswith( "'" ):
                result = str( literal_eval( st ))
                if isinstance( st, STR ):
                    return STR( result, st.input_file, st.pos )

                return result

            result = st.decode( 'string-escape' )
            if isinstance( st, STR ):
                return STR( result, st.input_file, st.pos )

            return result

        except:                                                                                                        #pylint: disable=bare-except
            pass

    return str( st )

#   ---------------------------------------------------------------------------
def _unify_eol( st ):
    return st.replace( '\r\n', EOL ).replace( '\r', EOL )

#   ---------------------------------------------------------------------------
def _import_source( lib, once ):
#   -- prevent libraries re-import
    if once and lib in yushell.source:
#       -- library has already been imported
        return SOURCE_EMPTY

    lpath = lib
    if not os.path.isfile( lpath ):
        for d in yushell.directory:
            lpath = os.path.join( d, lib )
            if os.path.isfile( lpath ):
                break
    try:
        with open( lpath, 'r' ) as f:
            sou = _unify_eol( f.read())
    except:
        e_type, e, tb = sys.exc_info()
        raise e_type, 'ps_import: %s' % ( e ) + lib.loc(), tb

    yushell.source[ lib ] = ( lpath, sou )
    return lib

#   ---------------------------------------------------------------------------
def _import_python( name, script ):
#   -- prevent scripts re-import
    if script in yushell.script:
#       -- script has already been imported
        return

    lpath = script
    if not os.path.isfile( lpath ):
        for d in yushell.directory:
            lpath = os.path.join( d, script )
            if os.path.isfile( lpath ):
                break
    try:
        mod = imp.load_source( name, lpath )
        builtin.update( vars( mod ))
    except:
        e_type, e, tb = sys.exc_info()
        raise e_type, 'ps_import_python: %s' % ( e ) + script.loc(), tb

    yushell.script.append( script )

#   ---------------------------------------------------------------------------
def _import_eval( infix ):
    try:
        code = STR( ''.join( str( x ) for x in infix.ast.ast ), infix.input_file, infix.pos )
        sou = eval( code, dict( globals(), **builtin ))                                                                #pylint: disable=eval-used
    except:
        e_type, e, tb = sys.exc_info()
        raise e_type, 'ps_import_eval: %s' % ( e ) + infix.loc(), tb

    yushell.inclusion.append( None )
    _import = str( len( yushell.inclusion ) - 1 )
    yushell.source[ _import ] = ( code, sou )
    return _import

#   ---------------------------------------------------------------------------
def trace__ps_( name, sou, depth ):
    if depth > trace.deepest:
        trace.deepest = depth
    if trace.enabled:
        trace.info( TR_INDENT * depth + name + TR_DELIMIT + repr( sou[ :TR_SLICE ]))

#   ---------------------------------------------------------------------------
def echo__ps_( fn ):
    def wrapped( sou, depth = 0 ):
        trace__ps_( fn.__name__, sou, depth )
        return fn( sou, depth )

    return wrapped

#   ---------------------------------------------------------------------------
def yuparse( input_file ):
    """
    source ::= { coding_py } text EOF;
    """
#   ---------------
    source = yushell.source[ input_file ][ 1 ]
    if not source:
        return TEXT([])

    sou = SOURCE( source, input_file )
    try:
        if ( yushell.input_file == input_file ) and yushell.output_py:
#   ---- { coding_py }
            ( sou, coding ) = ps_coding_py( sou, 0 )
        else:
            coding = None

#   ---- text
        text = ps_text( sou, 0 )
        while sou:
            ( sou, ast ) = text.next()

        if coding is not None:
            ast.extend_text( 0, coding )

        return ast

    except:                                                                                                            #pylint: disable=bare-except
        e_type, e, tb = sys.exc_info()
#   ---- Python exception
        arg = e.args[ 0 ] if e.args else None
        if not isinstance( arg, str ) or not arg.startswith( 'ps_' ) and not arg.startswith( 'python' ):
            raise e_type, 'python: %s' % ( e ) + sou.loc(), tb

#   ---- raised exception
        else:
            raise e_type, e, tb

#   ---------------------------------------------------------------------------
def ps_text( sou, depth = 0 ):
    """
    text ::= ($set (depth_pth_sq depth_pth) 0) {
          set
        | import
        | macro
        | comment
        | application
        | quote
        | remark_(c|py)
        | YIELD
        | plain
    }0...;
    """
#   ---------------
    ast = []
    depth_pth_sq = depth_pth = 0
    _plain_ret = ''
    while True:
        trace__ps_( 'ps_text', sou, depth )
#   ---- set
        ( sou, leg ) = ps_set( sou, depth + 1 )
        if leg is not None:
            ast.append( leg )
            continue
#   ---- import
        ( sou, leg ) = ps_import( sou, depth + 1 )
        if leg is not None:
            if isinstance( leg, TEXT ):
                ast.extend( leg.ast )
            else:
                ast.append( leg )
            continue
#   ---- macro
        ( sou, leg ) = ps_macro( sou, depth + 1 )
        if leg is not None:
            ast.append( leg )
            continue
#   ---- comment
        ( sou, leg ) = ps_comment( sou, depth + 1 )
        if leg is not None:
            ast.append( leg )
            continue
#   ---- application
        ( sou, leg ) = ps_application( sou, depth + 1 )
        if leg is not None:
            ast.append( leg )
            continue
#   ---- quote
        ( sou, leg ) = ps_quote( sou, depth + 1 )
        if leg is not None:
            ast.append( leg )
            continue
#       -- we have to parse comments to skip
        if yushell.pp_skip_comments == PP_SKIP_C_COMMENTS:
#   ---- remark_c
            ( sou, leg ) = ps_remark_c( sou, depth + 1 )
            if leg is not None:
                ast.append( leg )
                continue
        elif yushell.pp_skip_comments == PP_SKIP_PYTHON_COMMENTS:
#   ---- remark_py
            ( sou, leg ) = ps_remark_py( sou, depth + 1 )
            if leg is not None:
                ast.append( leg )
                continue
#   ---- YIELD
        yield ( sou[ : ], TEXT( ast, depth_pth_sq, depth_pth ))

#   ---- plain
        if sou == _plain_ret and ast:
            ast.pop()
        else:
            plain = ps_plain( sou, depth_pth_sq, depth_pth, None if ast else '', depth + 1 )

        ( sou, leg, depth_pth_sq, depth_pth ) = plain.next()
        ast.append( leg )
        _plain_ret = sou

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_set( sou, depth = 0 ):
    """
    set ::= '($set' ( '(' { atom }1... ')' | atom ) form { '\\set' } ')';
    """
#   ---------------
#   ---- ($set
    if sou[ :l_SET ] != ps_SET:
        return ( sou, None )

#   ---- gap
    ( sou, _ ) = ps_gap( sou[ l_SET: ], depth + 1 )
#   ---- (
    if sou[ :1 ] == '(':
#   ---- gap
        ( sou, _ ) = ps_gap( sou[ 1: ], depth + 1 )
        lval = []
        while True:
#   ---- atom
            ( sou, leg ) = ps_atom( sou, depth + 1 )
            if leg is None:
                raise SyntaxError( '%s: name expected' % ( callee()) + sou.loc())

            lval.append( leg )
#   ---- gap
            ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- )
            if sou[ :1 ] == ')':
                sou = sou[ 1: ]
                break
    else:
#   ---- atom
        ( sou, leg ) = ps_atom( sou, depth + 1 )
        if leg is None:
            raise SyntaxError( '%s: name expected' % ( callee()) + sou.loc())

        lval = leg
#   ---- gap
    ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- form
    ( sou, leg ) = ps_form( sou, depth + 1 )
    if leg is None:
        raise SyntaxError( '%s: form expected' % ( callee()) + sou.loc())

#   ---- gap
    ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- { \set }
    if sou[ :l_SET_T ] == ps_SET_T:
        ( sou, _ ) = ps_gap( sou[ l_SET_T: ], depth + 1 )
#   ---- )
    if sou[ :1 ] != ')':
        raise SyntaxError( '%s: ")" expected' % ( callee()) + sou.loc())

    return ( sou[ 1: ], SET( lval, leg ))

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_import( sou, depth = 0 ):
    """
    import ::= '($import' ( atom | quote | infix ) { '\\import' } ')';
    """
#   ---------------
#   ---- ($import
    if sou[ :l_IMPORT ] != ps_IMPORT:
        return ( sou, None )

#   ---- gap
    ( sou, _ ) = ps_gap( sou[ l_IMPORT: ], depth + 1 )
#   ---- atom
    ( sou, leg ) = ps_atom( sou, depth + 1 )
    if leg is not None:
#       -- import library
        leg = yuparse( _import_source( STR( "%s.yu" % ( leg ), leg.input_file, leg.pos ), True ))
        leg.enclose_import()
    else:
#   ---- quote
        ( sou, leg ) = ps_quote( sou, depth + 1 )
        if leg is not None:
            lpath = STR( _unq( leg ), leg.input_file, leg.pos )
            ( fn, e ) = os.path.splitext( os.path.basename( lpath ))
            if e.lower() == E_PY:
#               -- import Python script
                _import_python( fn, lpath )
                leg = TEXT([])
            else:
#               -- include source text
                leg = yuparse( _import_source( lpath, False ))
                leg.enclose_import()
        else:
#   ---- infix
            ( sou, leg ) = ps_infix( sou, depth + 1 )
            if leg is None:
                raise SyntaxError( '%s: name of imported file expected' % ( callee()) + sou.loc())

            leg = yuparse( _import_eval( leg ))
#   ---- gap
    ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- \import
    if sou[ :l_IMPORT_T ] == ps_IMPORT_T:
        ( sou, _ ) = ps_gap( sou[ l_IMPORT_T: ], depth + 1 )
#   ---- )
    if sou[ :1 ] != ')':
        raise SyntaxError( '%s: ")" expected' % ( callee()) + sou.loc())

    return ( sou[ 1: ], leg )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_macro( sou, depth = 0 ):
    """
    macro ::= '($macro' atom '(' { atom }0... ')' plain ')';
    """
#   ---------------
#   ---- ($macro
    if sou[ :l_MACRO ] != ps_MACRO:
        return ( sou, None )

#   ---- gap
    ( sou, _ ) = ps_gap( sou[ l_MACRO: ], depth + 1 )
#   ---- atom
    ( sou, name ) = ps_atom( sou, depth + 1 )
    if name is None:
        raise SyntaxError( '%s: name expected' % ( callee()) + sou.loc())

#   ---- gap
    ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- (
    if sou[ :1 ] != '(':
        raise SyntaxError( '%s: "(" expected' % ( callee()) + sou.loc())

#   ---- gap
    ( sou, _ ) = ps_gap( sou[ 1: ], depth + 1 )
    pars = []
#   ---- )
    while sou[ :1 ] != ')':
#   ---- atom
        ( sou, leg ) = ps_atom( sou, depth + 1 )
        if leg is None:
            raise SyntaxError( '%s: name expected' % ( callee()) + sou.loc())

        pars.append( leg )
#   ---- gap
        ( sou, _ ) = ps_gap( sou, depth + 1 )

    sou = sou[ 1: ]
    if sou[ :1 ] == ')':
        return ( sou[ 1: ], MACRO( name, pars, '' ))

    plain = ps_plain( sou, 0, 0, None, depth + 1 )
    while True:
#   ---- plain
        ( sou, leg, _, depth_pth ) = plain.next()
#   ---- ) & ($eq depth_pth 0)
        if ( sou[ :1 ] == ')' ) and ( depth_pth == 0 ):
            return ( sou[ 1: ], MACRO( name, pars, str( leg )))

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_emit( sou, depth = 0 ):
    """
    emit ::= '($emit' variable { form } { '\\emit' } ')';
    """
#   ---------------
#   ---- ($emit
    if sou[ :l_EMIT ] != ps_EMIT:
        return ( sou, None )

#   ---- gap
    ( sou, _ ) = ps_gap( sou[ l_EMIT: ], depth + 1 )
#   ---- variable
    ( sou, leg ) = ps_variable( sou, depth + 1 )
    if leg is None:
        raise SyntaxError( '%s: variable expected' % ( callee()) + sou.loc())

    var = leg
#   ---- gap
    ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- { form }
    ( sou, leg ) = ps_form( sou, depth + 1 )
    if leg is not None:
#   ---- gap
        ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- { \emit }
    if sou[ :l_EMIT_T ] == ps_EMIT_T:
        ( sou, _ ) = ps_gap( sou[ l_EMIT_T: ], depth + 1 )
#   ---- )
    if sou[ :1 ] != ')':
        raise SyntaxError( '%s: ")" expected' % ( callee()) + sou.loc())

    return ( sou[ 1: ], EMIT( var, leg ))

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_application( sou, depth = 0 ):
    """
    application ::= '($' function ($set fn ::function::text) { argument }0... { tag } ')';
    argument ::= { name ! '.' | EMBED } form;
    tag ::= name & ($eq fn ::name::atom::text);
    name ::= '\\' atom GAP;
    """
#   ---------------
#   ---- ($
    if sou[ :2 ] != '($':
        return ( sou, None )

#   ---- ($quote
    if sou[ :l_QUOTE ] == ps_QUOTE:
        return ( sou, None )

#   ---- ($code
    if sou[ :l_CODE ] == ps_CODE:
        return ps_code( sou, depth + 1 )

#   ---- ($emit
    if sou[ :l_EMIT ] == ps_EMIT:
        return ps_emit( sou, depth + 1 )

#   ---- (${}
    if sou[ :l_INFIX ] == ps_INFIX:
        return ps_infix( sou, depth + 1 )

    sou = sou[ 2: ]
    pos = sou.pos - 1
#   ---- $
    _eval = sou[ :1 ] == '$'
    if _eval:
        sou = sou[ 1: ]
#   ---- gap
    ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- function
    ( sou, func ) = ps_function( sou, depth + 1 )
    if func is None:
        raise SyntaxError( '%s: function expected' % ( callee()) + sou.loc())

#   ---- ($set fn ::function::text)
    fn = ( func.atom if isinstance( func, VAR ) else None )
    named = []
    args = []
#   ---- {
    while True:
#   ---- gap
        ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- name -- \
        name = None
        if sou[ :1 ] == '\\':
#   ---- name -- atom
            ( look, name ) = ps_atom( sou[ 1: ], depth + 1 )
            if name is not None:
#   ---- name -- gap
                ( look, _ ) = ps_gap( look, depth + 1 )
#   ---- '.'
                if look[ :1 ] == '.':
#                   -- lambda
                    name = None
                else:
                    sou = look

        if name is not None:
#   ---- ($eq fn ::name::atom::text)
            if fn != name:
#   ---- argument -- name
#   ---- gap
                ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- argument -- form
                ( sou, form ) = ps_form( sou, depth + 1 )
                if form is None:
                    raise SyntaxError( '%s: form expected' % ( callee()) + sou.loc())

                named.append(( name, form ))
            else:
#   ---- }0... tag -- name
                break
        else:
#   ---- argument -- EMBED
            embed = sou[ :1 ] == ps_EMBED
            if embed:
#   ---- gap
                ( sou, _ ) = ps_gap( sou[ 1: ], depth + 1 )
#   ---- argument -- form
            ( sou, form ) = ps_form( sou, depth + 1 )
            if form is not None:
                args.append( EMBED( form ) if embed else form )
            else:
#   ---- }0...
                if embed:
                    raise SyntaxError( '%s: unexpected "*"' % ( callee()) + sou.loc())

                break
#   ---- gap
    ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- )
    if sou[ :1 ] != ')':
        raise SyntaxError( '%s: ")" expected' % ( callee()) + sou.loc())

    _apply = APPLY( func, args, named, sou.input_file, pos )
    return ( sou[ 1: ], EVAL( _apply, SOURCE( '<string>', sou.input_file, pos + 1 )) if _eval else _apply )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_remark_c( sou, depth = 0 ):
    """
    remark_c ::=
          '//' { ANY YIELD }0... >> EOL <<
        | '/*' { ANY YIELD }0... '*/';
    """
#   ---------------
    del depth
#   ---- //
    if sou[ :2 ] == '//':
        i = 2
        l = len( sou )
        while i < l:
#   ---- EOL
            if ord( sou[ i ]) in ps_EOL:
#               -- leave EOL
                break
            i += 1
        return ( sou[ i: ], REMARK( sou[ :i ]))

#   ---- /*
    elif sou[ :2 ] == '/*':
        i = 2
        l = len( sou ) - 1
        while i < l:
#   ---- */
            if sou[ i:( i + 2 )] == '*/':
                return ( sou[( i + 2 ): ], REMARK( sou[ :( i + 2 )]))

            i += 1

        raise SyntaxError( '%s: unclosed comment' % ( callee()) + sou.loc())

    return ( sou, None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_remark_py( sou, depth = 0 ):
    """
    remark_py ::= '#' { ANY YIELD }0... >> EOL <<;
    """
#   ---------------
    del depth
#   ---- #
    if sou[ :1 ] == '#':
        i = 1
        l = len( sou )
        while i < l:
#   ---- EOL
            if ord( sou[ i ]) in ps_EOL:
#               -- leave EOL
                break
            i += 1
        return ( sou[ i: ], REMARK( sou[ :i ]))

    return ( sou, None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_coding_py( sou, depth = 0 ):
    """
    coding_py ::= { EOL } remark_py & ( 'coding:' 'yupp' { '.' encoding } );
    encoding ::= name;
    """
#   ---------------
#   ---- { EOL }
    ( rest, _ ) = ps_space( sou, depth + 1 )
    ( rest, eol ) = ps_eol( rest, depth + 1 )
    ( rest, _ ) = ps_space( rest, depth + 1 )
#   ---- remark_py
    ( rest, leg ) = ps_remark_py( rest, depth + 1 )
    if leg is not None:
#   ---- ( 'coding:' 'yupp' { '.' encoding } )
        mch = re_CODING.search( str( leg ))
        if mch:
            yushell.shrink = 2 if eol else 1
            if mch.group( 1 ) is None:
#               -- encoding is absent - delete the magic comment
                return ( rest, None )

#           -- delete 'yupp.' from the magic comment
            i = leg.find( ps_CODING )
            return ( rest, [ REMARK( leg[ :i ]), REMARK( leg[( i + l_CODING ): ])])

    return ( sou, None )

#   ---------------------------------------------------------------------------
def ps_plain( sou, pth_sq, pth, indent, depth = 0 ):
    """
    plain ::= { ANY
        ($switch ::prev::text
            "[" ($inc depth_pth_sq)
            "]" ($dec depth_pth_sq)
            "(" ($inc depth_pth)
            ")" ($dec depth_pth)
        )
        YIELD }1...;
    """
#   ---------------
    depth_pth_sq = pth_sq
    depth_pth = pth
    i = 0
    while True:
        trace__ps_( 'ps_plain', sou[ i: ], depth )

        symbol = _ord( sou, i )
#   ---- ANY
        if symbol is None:
            raise EOFError( '%s: unexpected EOF:' % ( callee()))

        if symbol not in ps_ANY:
            raise SyntaxError( '%s: forbidden character' % ( callee()) + sou.loc())

#   ---- ($switch ...
        if symbol == ord( '[' ):
            depth_pth_sq += 1
        elif symbol == ord( ']' ):
            if depth_pth_sq:
                depth_pth_sq -= 1
        elif symbol == ord( '(' ):
            depth_pth += 1
        elif symbol == ord( ')' ):
            if depth_pth:
                depth_pth -= 1
#       -- calculate indent
        if symbol in ps_EOL:
            indent = ''
        elif symbol in ps_SPACE:
            if isinstance( indent, str ):
                indent += sou[ i ]
        else:
            indent = False                                                                                             #pylint: disable=redefined-variable-type
        i += 1
#   ---- YIELD
        yield ( sou[ i: ], PLAIN( sou[ :i ], indent ), depth_pth_sq, depth_pth )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_function( sou, depth = 0 ):
    """
    function ::= form;
    """
#   ---------------
#   ---- form
    ( sou, leg ) = ps_form( sou, depth + 1 )
    return ( sou, leg )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_variable( sou, depth = 0 ):
    """
    variable ::= { region '::' }0... atom | '&' late-bounded;
    region ::= atom;
    late-bounded ::= atom;
    """
#   ---------------
#   ---- &
    if sou[ :1 ] == '&':
#   ---- atom
        ( sou, leg ) = ps_atom( sou[ 1: ], depth + 1 )
        if leg is not None:
            return ( sou, VAR( LATE_BOUNDED(), leg ))

        raise SyntaxError( '%s: late-bounded expected' % ( callee()) + sou.loc())

    else:
#   ---- atom
        ( sou, leg ) = ps_atom( sou, depth + 1 )
        if leg is None:
            return ( sou, None )

        region = []
#   ---- ::
        while sou[ :2 ] == '::':
            region.append( leg )
#   ---- atom
            ( sou, leg ) = ps_atom( sou[ 2: ], depth + 1 )
            if leg is None:
                raise SyntaxError( '%s: atom expected' % ( callee()) + sou.loc())

        return ( sou, VAR( region, leg ))

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_lambda( sou, depth = 0 ):
    """
    lambda ::= ( { bound }1... | l-bound ) l-form;
    bound ::=  { late '..' }0... name { ':' default } '.' | '\\...';
    late ::= name;
    default :: = form;
    l-bound ::= '\\' '(' variable ')' '.';
    """
#   ---------------
#   ---- \
    if sou[ :1 ] == '\\':
#   ---- (
        if sou[ 1:2 ] == '(':
#   ---- gap
            ( sou, _ ) = ps_gap( sou[ 2: ], depth + 1 )
#   ---- variable
            ( sou, bound ) = ps_variable( sou, depth + 1 )
            if bound is None:
                raise SyntaxError( '%s: variable expected' % ( callee()) + sou.loc())
#   ---- gap
            ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- )
            if sou[ :2 ] != ').':
                raise SyntaxError( '%s: ")." expected' % ( callee()) + sou.loc())

#   ---- gap
            ( sou, _ ) = ps_gap( sou[ 2: ], depth + 1 )
        else:
#   ---- bound
            bound = []
            late = []
            while sou[ :1 ] == '\\':
#   ---- ...
                if sou[ 1:4 ] == '...':
                    if late:
                        raise SyntaxError( '%s: late bound with refuge' % ( callee()) + sou.loc())

                    bound.append(( [], ATOM( '...' ), None ))
#   ---- gap
                    ( sou, _ ) = ps_gap( sou[ 4: ], depth + 1 )
                    continue

#   ---- name -- atom
                ( sou, leg ) = ps_atom( sou[ 1: ], depth + 1 )
                if leg is None:
                    raise SyntaxError( '%s: name expected' % ( callee()) + sou.loc())
#   ---- :
                if sou[ :1 ] == ':':
#   ---- form
                    ( sou, form ) = ps_form( sou[ 1: ], depth + 1 )
                    if form is None:
                        raise SyntaxError( '%s: form expected' % ( callee()) + sou.loc())
                else:
                    form = None
#   ---- .
                if sou[ :1 ] != '.':
                    raise SyntaxError( '%s: "." expected' % ( callee()) + sou.loc())
#   ---- ..
                if sou[ :2 ] == '..':
                    late.append( leg )
#   ---- gap
                    ( sou, _ ) = ps_gap( sou[ 2: ], depth + 1 )
                    continue

                bound.append(( late, leg, form ))
                late = []
#   ---- gap
                ( sou, _ ) = ps_gap( sou[ 1: ], depth + 1 )

#   ---- l-form
        ( sou, leg ) = ps_l_form( sou, depth + 1 )
        if leg is None:
            raise SyntaxError( '%s: l-form expected' % ( callee()) + sou.loc())

        return ( sou, LAMBDA( bound, leg ))

    return ( sou, None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_value( sou, depth = 0 ):
    """
    value ::=
          quote
        | number;
    """
#   ---------------
    ( sou, leg ) = ps_quote( sou, depth + 1 )
    if leg is not None:
        return ( sou, leg )

    ( sou, leg ) = ps_number( sou, depth + 1 )
    if leg is not None:
        return ( sou, leg )

    return ( sou, None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_form( sou, depth = 0 ):
    """
    form ::= former { '?' cond { '|' form } };
    cond ::= former;
    """
#   ---------------
#   ---- former
    ( sou, leg ) = ps_former( sou, depth + 1 )
    if leg is not None:
#   ---- gap
        ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- ?
        if sou[ :1 ] == '?':
#   ---- gap
            ( sou, _ ) = ps_gap( sou[ 1: ], depth + 1 )
#   ---- cond
            ( sou, cond ) = ps_former( sou, depth + 1 )
            if cond is None:
                raise SyntaxError( '%s: former expected' % ( callee()) + sou.loc())

            form = None
#   ---- gap
            ( sou, _ ) = ps_gap( sou, depth + 1 )
#   ---- |
            if sou[ :1 ] == '|':
#   ---- gap
                ( sou, _ ) = ps_gap( sou[ 1: ], depth + 1 )
#   ---- form
                ( sou, form ) = ps_form( sou, depth + 1 )
                if form is None:
                    raise SyntaxError( '%s: form expected' % ( callee()) + sou.loc())

            return ( sou, COND( cond, leg, form ))

    return ( sou, leg )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_former( sou, depth = 0 ):
    """
    former ::=
          variable
        | lambda
        | value
        | l-form;
    """
#   ---------------
#   ---- value
    ( sou, leg ) = ps_value( sou, depth + 1 )
    if leg is not None:
        return ( sou, leg )

#   ---- variable
    ( sou, leg ) = ps_variable( sou, depth + 1 )
    if leg is not None:
        return ( sou, leg )

#   ---- lambda
    ( sou, leg ) = ps_lambda( sou, depth + 1 )
    if leg is not None:
        return ( sou, leg )

#   ---- l-form
    ( sou, leg ) = ps_l_form( sou, depth + 1 )

    return ( sou, leg )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_l_form( sou, depth = 0 ):
    """
    l-form ::=
          code
        | infix
        | application
        | list;
    """
#   ---------------
#   ---- code
    ( sou, leg ) = ps_code( sou, depth + 1 )
    if leg is not None:
        return ( sou, leg )

#   ---- infix
    ( sou, leg ) = ps_infix( sou, depth + 1 )
    if leg is not None:
        return ( sou, leg )

#   ---- application
    ( sou, leg ) = ps_application( sou, depth + 1 )
    if leg is not None:
        return ( sou, leg )

#   ---- list
    ( sou, leg ) = ps_list( sou, depth + 1 )

    return ( sou, leg )

#   ---------------------------------------------------------------------------
def _open_sq_bracket( sou ):
    return 1 if sou[ :1 ] == '[' else 2 if sou[ :2 ] == '\\[' else 0

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_code( sou, depth = 0 ):                                                                                         #pylint: disable=too-many-return-statements,too-many-branches
    """
    code ::=
          ']' EOL text EOL { '\\' } '['
        | ']' text { '\\' } '[' >> { tag } ')' <<
        | '[' text ']' & ($eq depth_pth_sq 0)
        | ',,' text ( ';;' | >> ( ',,' | { tag } ')' & ($eq depth_pth 0) ) << )
        | '($code' text ')' & ($eq depth_pth 0);
    """
#   ---------------
#   ---- ]
    if sou[ :1 ] == ']':                                                                                               #pylint: disable=too-many-nested-blocks
#   ---- EOL
        ( rest, _ ) = ps_space( sou[ 1: ], depth + 1 )
        ( rest, eol ) = ps_eol( rest, depth + 1 )
        if eol:
            text = ps_text( rest, depth + 1 )
            while True:
#   ---- text
                ( rest, leg ) = text.next()
#   ---- EOL
                ( rest, eol ) = ps_eol( rest, depth + 1 )
                if eol:
                    ( rest, _ ) = ps_space( rest, depth + 1 )
#   ---- [
                    pos = _open_sq_bracket( rest )
                    if pos:
                        return ( rest[ pos: ], leg )

#               -- show warning in case of empty code without EOL before ending [
                elif not leg.ast:
                    ( rest, _ ) = ps_space( rest, depth + 1 )
#   ---- [
                    pos = _open_sq_bracket( rest )
                    if pos:
                        log.warn( 'there is no EOL before "["' + sou.loc())
        else:
            text = ps_text( sou[ 1: ], depth + 1 )
            while True:
#   ---- text
                ( rest, leg ) = text.next()
#   ---- [ >>
                pos = _open_sq_bracket( rest )
                if pos:
#   ---- gap
                    ( look, _ ) = ps_gap( rest[ pos: ], depth + 1 )
#   ---- \
                    if look[ :1 ] == '\\':
#   ---- atom
                        ( look, name ) = ps_atom( look[ 1: ], depth + 1 )
                        if name is None:
                            continue
#   ---- gap
                    ( look, _ ) = ps_gap( look, depth + 1 )
#   ---- ) <<
                    if look[ :1 ] == ')':
                        return ( rest[ pos: ], leg )

#   ---- [
    elif sou[ :1 ] == '[':
        text = ps_text( sou[ 1: ], depth + 1 )
        while True:
#   ---- text
            ( rest, leg ) = text.next()
#   ---- ] & ($eq depth_pth_sq 0)
            if ( rest[ :1 ] == ']' ) and ( leg.depth_pth_sq == 0 ):
                return ( rest[ 1: ], leg )

#   ---- ($code
    elif sou[ :l_CODE ] == ps_CODE:
        text = ps_text( sou[ l_CODE: ], depth + 1 )
        while True:
#   ---- text
            ( rest, leg ) = text.next()
#   ---- ) & ($eq depth_pth 0)
            if ( rest[ :1 ] == ')' ) and ( leg.depth_pth == 0 ):
                return ( rest[ 1: ], leg )

#   ---- ,,
    elif sou[ :l_DUALCOMMA ] == ps_DUALCOMMA:
#       -- (syntactic sugar) e.g. ($func,,text,,text) equals to ($func [text] [text])
        text = ps_text( sou[ l_DUALCOMMA: ], depth + 1 )
        while True:
#   ---- text
            ( rest, leg ) = text.next()
#   ---- ;;
            if rest[ :l_DUALSEMI ] == ps_DUALSEMI:
                return ( rest[ l_DUALSEMI: ], leg )

#   ---- >>
            look = rest
#   ---- ,, <<
            if look[ :l_DUALCOMMA ] == ps_DUALCOMMA:
                return ( rest, leg )
#   ---- \
            elif look[ :1 ] == '\\':
#   ---- atom
                ( look, name ) = ps_atom( look[ 1: ], depth + 1 )
                if name is None:
                    continue
#   ---- gap
                ( look, _ ) = ps_gap( look, depth + 1 )
#   ---- ) & ($eq depth_pth 0) <<
            if ( look[ :1 ] == ')' )  and ( leg.depth_pth == 0 ):
                return ( rest, leg )

    return ( sou, None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_list( sou, depth = 0 ):
    """
    list ::= '(' { { EMBED } form }0... ')';
    """
#   ---------------
#   ---- (
    if sou[ :1 ] == '(':
#   ---- gap
        ( sou, _ ) = ps_gap( sou[ 1: ], depth + 1 )
        lst = []
#   ---- )
        while sou[ :1 ] != ')':
#   ---- EMBED
            embed = sou[ :1 ] == ps_EMBED
            if embed:
#   ---- gap
                ( sou, _ ) = ps_gap( sou[ 1: ], depth + 1 )
#   ---- form
            ( sou, leg ) = ps_form( sou, depth + 1 )
            if leg is None:
                raise SyntaxError( '%s: form expected' % ( callee()) + sou.loc())

            lst.append( EMBED( leg ) if embed else leg )
#   ---- gap
            ( sou, _ ) = ps_gap( sou, depth + 1 )

        return( sou[ 1: ], LIST( lst ))

    return ( sou, None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_infix( sou, depth = 0 ):
    """
    infix ::=
          '{' text '}'
        | '(${}' text ')' & ($eq depth_pth 0);
    """
#   ---------------
#   -- infix was released as a expression in Python
#   ---- {
    if sou[ :1 ] == '{':
        text = ps_text( sou[ 1: ], depth + 1 )
        while True:
#   ---- text
            ( rest, leg ) = text.next()
#   ---- }
            if rest[ :1 ] == '}':
                return ( rest[ 1: ], INFIX( leg, sou.input_file, sou.pos ))

#   ---- (${}
    elif sou[ :l_INFIX ] == ps_INFIX:
        text = ps_text( sou[ l_INFIX: ], depth + 1 )
        while True:
#   ---- text
            ( rest, leg ) = text.next()
#   ---- ) & ($eq depth_pth 0)
            if ( rest[ :1 ] == ')' ) and ( leg.depth_pth == 0 ):
                return ( rest[ 1: ], INFIX( leg, sou.input_file, sou.pos + 1 ))

    return ( sou, None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_atom( sou, depth = 0 ):
    """
    atom ::= LETTER { LETTER | FIGURE }0...;
    """
#   ---------------
    del depth
    i = 0
    if _ord( sou, 0 ) in ps_LETTER:
        i = 1
        while _ord( sou, i ) in ps_LETTER | ps_FIGURE:
            i += 1

    return ( sou[ i: ], ATOM( sou[ :i ]) if i else None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_space( sou, depth = 0 ):
    """
    SPACE ::= [ '\t', ' ' ];
    """
#   ---------------
    del depth
    i = 0
    while _ord( sou, i ) in ps_SPACE:
        i += 1

    return ( sou[ i: ], sou[ :i ] or None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_eol( sou, depth = 0 ):
    """
    EOL ::= [ '\n', '\r' ];
    """
#   ---------------
    del depth
    if _ord( sou, 0 ) in ps_EOL:
        return ( sou[ 1: ], sou[ :1 ])

    return ( sou, None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_gap( sou, depth = 0 ):
    """
    GAP ::= EOL + SPACE;
    """
#   ---------------
    del depth
    i = 0
    while _ord( sou, i ) in ps_EOL | ps_SPACE:
        i += 1

    return ( sou[ i: ], sou[ :i ] or None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_quote( sou, depth = 0 ):
    """
    quote ::=
          string
        | char
        | ( '($quote' | '(`' ) plain ')' & ($eq depth_pth 0);
    """
#   ---------------
    if yushell.output_py:
#   ---- Python string
        ( sou, leg ) = ps_string_py( sou, depth + 1 )
        if leg is not None:
            return ( sou, leg )

    else:
#   ---- C string
        mch = re_STR.match( sou )
        if mch:
            leg = mch.group( 0 )
            return ( sou[ mch.end(): ], STR( leg ))

#   ---- chr
        mch = re_CHR.match( sou )
        if mch:
            leg = mch.group( 0 )
            return ( sou[ mch.end(): ], STR( leg ))

#   ---- (` | ($quote
    pos = ( l_BQUOTE if sou[ :l_BQUOTE ] == ps_BQUOTE else l_QUOTE if sou[ :l_QUOTE ] == ps_QUOTE else 0 )
    if pos:
        sou = sou[ pos: ]
        if sou[ :1 ] == ')':
            return ( sou[ 1: ], STR( '' ))

        plain = ps_plain( sou, 0, 0, None, depth + 1 )
        while True:
#   ---- plain
            ( sou, leg, _, depth_pth ) = plain.next()
#   ---- ) & ($eq depth_pth 0)
            if ( sou[ :1 ] == ')' ) and ( depth_pth == 0 ):
                return ( sou[ 1: ], STR( leg ))

    return ( sou, None )

#   ---------------------------------------------------------------------------
def _getline( st, _from = 0 ):
    _end = st.find( '\n', _from ) + 1
    if not _end:
        _end = len( st )
    return ( _from, _end )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_string_py( sou, depth = 0 ):
    del depth
    #   -- the first line
    ln_start, ln_end = _getline( sou )
    ln = sou[ ln_start:ln_end ]
#   -- look for head
    mch_head = ps_string_py.re_STR_HEAD.match( ln )
    if mch_head:
        p = mch_head.end()
        head = ln[ :p ]
        if mch_head.group( ps_string_py.group_3x ) is not None:
#           -- head of ''' or """ string
            re_tail = ps_string_py.re_STR_3x1_TAIL if "'" in head else ps_string_py.re_STR_3x2_TAIL
#           -- look for tail
            mch_tail = re_tail.match( ln, p )
            if mch_tail:
#               -- tail on the same line
                p = mch_tail.end()
                return ( sou[ p: ], STR( sou[ :p ]))

#           -- tail on other line
            _1x = False
        else:
#           -- head of ' or " string
            if head[ -1 ] != '\n':
#               -- tail on the same line
                return ( sou[ p: ], STR( sou[ :p ]))

#           -- tail on other line
            re_tail = ps_string_py.re_STR_1x1_TAIL if "'" in head else ps_string_py.re_STR_1x2_TAIL
            _1x = True
    else:
        return ( sou, None )

#   -- look for tail on the following lines
    sou_p = len( ln )
    while True:
#       -- the next line
        ln_start, ln_end = _getline( sou, ln_end )
        ln = sou[ ln_start:ln_end ]
        if not ln:
            raise EOFError( '%s: unexpected EOF into multi-line string:' % ( callee()))

        mch_tail = re_tail.match( ln )
        if mch_tail:
#           -- tail is found
            sou_p += mch_tail.end( 0 )
            return ( sou[ sou_p: ], STR( sou[ :sou_p ]))

#       -- look for line continuation
        elif _1x and ln[ -2: ] != '\\\n':
            raise SyntaxError( '%s: multi-line string continuation expected' % ( callee()) + sou[ sou_p: ].loc())

        sou_p += len( ln )

# -- regexes will be initialized in the yuinit(), if required
ps_string_py.initialized = False

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_comment( sou, depth = 0 ):
    """
    comment ::= '($!' plain ')' & ($eq depth_pth 0);
    """
#   ---------------
#   ---- ($!
    if sou[ :l_COMMENT ] == ps_COMMENT:
        sou = sou[ l_COMMENT: ]
        if sou[ :1 ] == ')':
            return ( sou[ 1: ], COMMENT())

        plain = ps_plain( sou, 0, 0, None, depth + 1 )
        while True:
#   ---- plain
            ( sou, _leg, _, depth_pth ) = plain.next()
#   ---- ) & ($eq depth_pth 0)
            if ( sou[ :1 ] == ')' ) and ( depth_pth == 0 ):
                return ( sou[ 1: ], COMMENT())

    return ( sou, None )

#   ---------------------------------------------------------------------------
@echo__ps_
def ps_number( sou, depth = 0 ):
    """
    number ::=
          float
        | hex
        | oct
        | dec;
    """
#   ---------------
    del depth
#   ---- float
    mch = re_FLOAT.match( sou )
    if mch:
        leg = mch.group( 0 )
        return ( sou[ mch.end(): ], FLOAT( leg ))

#   ---- integer
    mch = re_INT.match( sou )
    if mch:
        leg = mch.group( 0 )
        return ( sou[ mch.end(): ], INT( leg, 0 ))

    return ( sou, None )


#   * * * * * * * * * * * * * * * * * *
#   *                                 *
#   *             E V A L             *
#   *                                 *
#   * * * * * * * * * * * * * * * * * *

#   -----------------------------------
#   AST extension
#   -----------------------------------

#   ---------------------------------------------------------------------------
class BOUND( BASE_MARK ):
    """
    AST: marker of bounded unassigned variable
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class LAMBDA_CLOSURE( BASE_OBJECT ):
    """
    AST: abstract parent for lambda and macro closures
    """
#   -----------------------------------
    def __init__( self, l_form, env, late = None, default = None ):
        self.l_form = l_form
        self.env = env
        self.env.parent = None
        self.late = late or {}
        self.default = default or {}
        self.call = None

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s, %s, %s)' % ( self.__class__.__name__, repr( self.l_form ), repr( self.env )
        , repr( self.late ), repr( self.default ))

#   -----------------------------------
    def __eq__( self, other ):
        return ( isinstance( other, self.__class__ ) and ( self.l_form == other.l_form ) and ( self.env == other.env )
        and ( self.late == other.late ) and ( self.default == other.default ))

#   ---------------------------------------------------------------------------
class L_CLOSURE( LAMBDA_CLOSURE ):
    """
    AST: L_CLOSURE( form, ENV, { var: [( late, BOUND )] }, { var: form } ) <-- LAMBDA
                                                                               late
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class M_CLOSURE( LAMBDA_CLOSURE ):
    """
    AST: M_CLOSURE( text, ENV( { par: BOUND } ), decl ) <-- MACRO( name, pars, text )
    """
#   -----------------------------------
    def __init__( self, l_form, env, decl ):
        LAMBDA_CLOSURE.__init__( self, l_form, env )
        self.decl = decl

#   ---------------------------------------------------------------------------
class INFIX_CLOSURE( BASE_OBJECT_LOCATED ):
    """
    AST: INFIX_CLOSURE( tree, ENV ) <-- INFIX
    """
#   -----------------------------------
    def __init__( self, tree, env, text, input_file = None, pos = None ):                                              #pylint: disable=too-many-arguments
        BASE_OBJECT_LOCATED.__init__( self, input_file, pos )
        self.tree = tree
        self.env = env
        self.text = text

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s)' % ( self.__class__.__name__, repr( self.text ), repr( self.env ))

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ ) and ( self.tree == other.tree ) and ( self.env == other.env )

#   ---------------------------------------------------------------------------
class COND_CLOSURE( BASE_OBJECT ):
    """
    AST: COND_CLOSURE( former, former, form ) <-- COND
    """
#   -----------------------------------
    def __init__( self, cond, leg_1, leg_0 ):
        self.cond = cond
        self.leg_1 = leg_1
        self.leg_0 = leg_0

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s, %s)' % ( self.__class__.__name__, repr( self.cond ), repr( self.leg_1 ), repr( self.leg_0 ))

#   -----------------------------------
    def __eq__( self, other ):
        return ( isinstance( other, self.__class__ ) and ( self.cond == other.cond ) and ( self.leg_1 == other.leg_1 )
        and ( self.leg_0 == other.leg_0 ))

#   ---------------------------------------------------------------------------
class SET_CLOSURE( BASE_OBJECT ):
    """
    AST: SET_CLOSURE( form, ENV ) <-- SET
    """
#   -----------------------------------
    def __init__( self, form, env ):
        self.form = form
        self.env = env
        self.env.parent = None

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s)' % ( self.__class__.__name__, repr( self.form ), repr( self.env ))

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ ) and ( self.form == other.form ) and ( self.env == other.env )

#   ---------------------------------------------------------------------------
class BUILTIN( BASE_OBJECT ):
    """
    AST: BUILTIN( ATOM, fn )
    """
#   -----------------------------------
    def __init__( self, atom, fn = None ):
        self.atom = atom
        self.fn = fn

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s)' % ( self.__class__.__name__, repr( self.atom ))

#   -----------------------------------
    def __eq__( self, other ):
        return isinstance( other, self.__class__ ) and ( self.atom == other.atom )

#   ---------------------------------------------------------------------------
class BUILTIN_SPECIAL( BUILTIN ):
    """
    AST: BUILTIN_SPECIAL( ATOM, fn )
    """
#   -----------------------------------
    pass

#   ---------------------------------------------------------------------------
class T( BASE_LIST ):
    """
    AST: T([ form ]) <-- TEXT
    """
#   -----------------------------------
    def __init__( self, val, indent = '' ):
        BASE_LIST.__init__( self, val )
        self.indent = indent

#   ---------------------------------------------------------------------------
def _bisect( a, x, lo = 0 ):
    """
    Modified 'bisect_right' from the Python standard library.
    """
    hi = len( a )
    while lo < hi:
        mid = ( lo + hi ) // 2
        if x < a[ mid ][ 0 ]:
            hi = mid
        else:
            lo = mid + 1
    return lo

#   ---------------------------------------------------------------------------
def _merge_offset( p_offset, offset ):
    result = []
    _delta = 0
    _inx = 0
    for pos, delta in offset:
        inx = _bisect( p_offset, pos + delta )
        p_delta = p_offset[ inx - 1 ][ 1 ] if inx else 0
        for i in range( _inx, inx ):
            p, d = p_offset[ i ]
            if p - _delta < pos:
                result.append(( p - _delta, d + _delta ))
            _inx += 1
        result.append(( pos, p_delta + delta ))
        _delta = delta

    for i in range( _inx, len( p_offset )):
        p, d = p_offset[ i ]
        result.append(( p - _delta, d + _delta ))

    return result

#   ---------------------------------------------------------------------------
class TRIM( BASE_OBJECT, CAPTION ):
    """
    AST: TRIM( form, indent )
    """
#   -----------------------------------
    def __init__( self, ast, indent ):
        CAPTION.__init__( self, ast )
        self.indent = indent if indent else ''

#   -----------------------------------
    def trim( self, plain ):
        if not plain or not config.pp_trim_app_indent:
            return plain

        return self.indent.join( dedent( plain ).splitlines( True ))

#   -----------------------------------
    def trim_with_browse( self, plain ):
        if not plain or not config.pp_trim_app_indent:
            return plain

        lnlist = plain.splitlines( True )

#       -- find shared indent, mark empty lines
        cutting = ''
        empty = set()
        for i, ln in enumerate( lnlist ):
            ( rest, indent ) = ps_space( ln )
            if rest == EOL:
#               -- skip empty line
                empty.add( i )
                continue

            if cutting is None:
#               -- no common indent
                continue

            if indent is None:
#               -- no indent
                cutting = None
                continue

            if not cutting:
#               -- first not empty line
                cutting = indent
            elif indent.startswith( cutting ):
#               -- line more deeply indented
                pass
            elif cutting.startswith( indent ):
#               -- line less deeply indented
                cutting = indent
            else:
#               -- no common indent
                cutting = None

#       -- remove shared indent, add specified indent
        c = len( cutting ) if cutting is not None else 0
        result = ''
        for i, ln in enumerate( lnlist ):
            result += ln if i in empty else (( self.indent if i else '' ) + ln[ c: ])

#       -- calculate offsets
        offset = []
        d = c - len( self.indent )
        total = 0
        pos = 0
        for i, ln in enumerate( lnlist ):
            if i not in empty:
                delta = d if i else c  # no additional indent for first line
                if delta > 0:
#                   -- removed indent
                    total += delta
                    offset.append(( pos, total ))
                    pos -= delta
                elif delta < 0:
#                   -- added indent
                    for _ in xrange( -delta ):
                        total -= 1
                        offset.append(( pos, total ))
                        pos += 1
            pos += len( ln )

#       -- merge with previous offsets
        if plain.offset:
            offset = _merge_offset( plain.offset, offset )

        return RESULT( result, plain.browse, offset )

#   -----------------------------------
#   Environment
#   -----------------------------------

#   ---- name of variable argument list
__va_args__ = ATOM( '__va_args__' )

#   ---------------------------------------------------------------------------
class NOT_FOUND( object ):
    """
    Mark of negative result.
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class ENV( dict ):
    """
    Environment.
    AST: ENV( ENV, [ ( var, value ) ])
    """
#   -----------------------------------
    def __init__( self, parent = None, local = None ):
        dict.__init__( self )
        self.parent = parent
        self.order = []
        if local:
            for key, value in local:
                self.__setitem__( key, value )

#   -----------------------------------
    def __setitem__( self, key, value ):
        if key in self.order:
            self.order.remove( key )
        self.order.append( key )

        dict.__setitem__( self, key, value )

#   -----------------------------------
    def __getitem__( self, key ):
        return dict.__getitem__( self, key )

#   -----------------------------------
    def __contains__( self, key ):
        return dict.__contains__( self, key )

#   -----------------------------------
    def __delitem__( self, key ):
        self.order.remove( key )
        dict.__delitem__( self, key )

#   -----------------------------------
    def eval_local( self, env, depth ):
        result = True
        for key in self.order:
            val = yueval( self.__getitem__( key ), env, depth )
            if result and not _is_term( val ):
                result = False
            dict.__setitem__( self, key, val )
        return result

#   -----------------------------------
    def xlocal( self ):
        for key in list( self.order ):
            yield key, self.__getitem__( key )

#   -----------------------------------
    def lookup( self, reg, var ):                                                                                      #pylint: disable=unused-argument
        del reg
        env = self
        while env is not None:
            if env.__contains__( var ):
                return env.__getitem__( var )

            env = env.parent

        return NOT_FOUND

#   -----------------------------------
    def update_variable( self, reg, var, value ):                                                                      #pylint: disable=unused-argument
        del reg
        env = self
        while env is not None:
            if env.__contains__( var ):
                dict.__setitem__( env, var, value )
                return var

            env = env.parent

        return NOT_FOUND

#   -----------------------------------
    def unassigned( self ):
        for key in self.order:
            if isinstance( self.__getitem__( key ), BOUND ):
                return key

        return NOT_FOUND

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s)' % ( self.__class__.__name__, dict.__repr__( self ), repr( self.parent ))

#   -----------------------------------
    def __eq__( self, other ):
        return ( isinstance( other, self.__class__ ) and ( dict.__eq__( self, other ))
        and ( self.parent == other.parent ) and ( self.order == other.order ))

#   -----------------------------------
    def __deepcopy__( self, memo = None ):
        return ENV( copy.deepcopy( self.parent, memo )
        , [( key, copy.deepcopy( self.__getitem__( key ), memo )) for key in self.order ])

#   -----------------------------------
#   -- debug message
    def _keylist( self ):
        result = []
        env = self
        while env is not None:
            for key, value in env.items():
                result.append( str( key ) if isinstance( value, BOUND ) else key.upper())
            env = env.parent
        return '%s(%s)' % ( self.__class__.__name__, ' '.join( result ))

#   -----------------------------------
    def loc( self ):
        return self.order[ 0 ].loc() if self.order else _loc_repr( self )

#   ---------------------------------------------------------------------------
class INFIX_VISITOR( NodeVisitor ):
    """
    Get identifiers from expression in Python.
    """
#   -----------------------------------
    def __init__( self ):
        self.names = set()

#   -----------------------------------
    def visit_Name( self, node ):
        self.names.add( node.id )

#   ---------------------------------------------------------------------------
class LAZY( BASE_OBJECT, CAPTION ):
    """
    AST: LAZY( form ) <-- ($lazy ___ )
    """
#   ---------------
    pass

#   ---------------------------------------------------------------------------
class SKIP( BASE_MARK ):
    """
    Skip the rest of text.
    """
#   ---------------
    pass

#   -----------------------------------
#   Built-in functions and consts
#   -----------------------------------

SOURCE_EMPTY = '<null>'
STEADY_SPACE = '\xFE'
STEADY_TAB = '\xFF'

#   ---------------------------------------------------------------------------
def yushell( text, _input = None, _output = None ):
    yushell.input_file = os.path.basename( _input ) if _input else '<stdin>'
    yushell.output_file = os.path.basename( _output ) if _output else '<stdout>'
#   -- output file is in Python
    yushell.output_py = os.path.splitext( yushell.output_file )[ 1 ].lower() == E_PY
    yushell.source = { SOURCE_EMPTY: ( '', '' ), yushell.input_file: ( _input, _unify_eol( text ))}
    yushell.script = []
    yushell.inclusion = []
    yushell.module = os.path.splitext( yushell.input_file )[ 0 ].replace( '-', '_' ).upper() if _input else 'UNTITLED'
    yushell.directory = []
#   -- list of built-in functions that can lead to a failed translation
    yushell.hazard = []
#   -- input file directory
    if _input:
        yushell.directory.append( os.path.dirname( _input ))
#   -- specified directories
    yushell.directory.extend( config.directory )
#   -- yupp lib directory
    if '__file__' in globals():
        yushell.directory.append( os.path.join( os.path.dirname( os.path.realpath( __file__ )), 'lib' ))
    else:
        yushell.directory.append( './lib' )
#   -- to skip comments we have to parse them
    yushell.pp_skip_comments = config.pp_skip_comments
    if yushell.pp_skip_comments == PP_SKIP_COMMENTS_AUTO:
        yushell.pp_skip_comments = PP_SKIP_PYTHON_COMMENTS if yushell.output_py else PP_SKIP_C_COMMENTS
#   -- the number of deleted lines at the beginning (Python)
    yushell.shrink = 0

_title_template_c = r"""/*  %(output)s was generated by %(app)s %(version)s
    out of %(input)s %(datetime)s
 */"""

_title_template_py = """#  %(output)s was generated by %(app)s %(version)s
#  out of %(input)s %(datetime)s"""

builtin = dict()
builtin.update( vars( string ))
builtin.update( vars( operator ))
builtin.update( vars( math ))
builtin.update({
    '__FILE__': lambda : '"%s"' % yushell.input_file,
    '__OUTPUT_FILE__': lambda : '"%s"' % yushell.output_file,
    '__MODULE_NAME__': lambda : ATOM( yushell.module ),
    '__TITLE__': lambda dt=True : PLAIN(( _title_template_py if yushell.output_py else _title_template_c ) % {
      'app': APP, 'version': VERSION
    , 'input': yushell.input_file, 'output': yushell.output_file
    , 'datetime': 'at ' + datetime.datetime.now().strftime( '%Y-%m-%d %H:%M' ) if dt else ''
    }),
    'abs': abs,
    'and': operator.and_,
    'car': lambda l : l[ :1 ],
    'cdr': lambda l : l[ 1: ],
    'chr': chr,
    'cmp': cmp,
    'crc32': lambda val : ( zlib.crc32( str( val )) & 0xffffffff ),
    'dec': lambda val : ( val - 1 ),
    'getslice': lambda l, *sl : l[ slice( *( None if x == '' else x for x in sl ))],
    'hex': hex,
    'inc': lambda val : ( val + 1 ),
    'index': lambda l, val : l.index( val ) if val in l else -1,
    'isdigit': lambda val : str( val ).isdigit(),
    'islist': lambda l : isinstance( l, list ),
    'len': len,
    'list': lambda *l : LIST( l ),
    'not': operator.not_,
    'oct': oct,
    'or': operator.or_,
    'ord': lambda val : ord( val ) if isinstance( val, STR ) else ord( str( val )),
    'print': lambda *l : sys.stdout.write( ' '.join(( _unq( x ) if isinstance( x, STR ) else str( x )) for x in l )),
    'q': lambda val : STR( '"%s"' % str( val ).encode( 'string-escape' )),
    'qs': lambda val : STR( "'%s'" % str( val ).encode( 'string-escape' )),
    'range': lambda *l : LIST( range( *l )),
    'reversed': lambda l : l[ ::-1 ],
    're-split': lambda regex, val : LIST( filter( None, re.split( regex, val ))),
    'rindex': lambda l, val : ( len( l ) - 1 ) - l[ ::-1 ].index( val ) if val in l else -1,
    'round': round,
    'SPACE': lambda : STEADY_SPACE,
    'str': str,
    'strlen': lambda val : len( _unq( val ) if isinstance( val, STR ) else str( val )),
    'sum': sum,
    'TAB': lambda : STEADY_TAB,
    'typeof': lambda val : ATOM( val.__class__.__name__ ),
    'unique': lambda l, s=set() : LIST( x for x in l if not ( x in s or s.add( x ))),
    'unq': _unq,
})

builtin_special = dict()
builtin_special.update({
    'isatom': None,
    'lazy': lambda val : LIST( LAZY( x ) for x in val ) if isinstance( val, list ) else LAZY( val ),
    'skip': SKIP(),
    'reduce': reduce,
    'repr': repr,
})

#   ---------------------------------------------------------------------------
def _plain_back( st ):
    return '()' if st == [] else str( st )

#   ---------------------------------------------------------------------------
def _is_term( node ):                                                                                                  #pylint: disable=too-many-return-statements
    """
    Check AST is term.
    """
#   ---------------
    if node is None:
        return True

#   ---- TRIM
    if isinstance( node, TRIM ):
        return _is_term( node.ast )

#   ---- list
    if isinstance( node, list ):
        for i in node:
            if not _is_term( i ):
                return False

        return True

#   ---- LAZY
    if isinstance( node, LAZY ):
        return True

#   ---- str based | int | float | long
    if isinstance( node, str ) or isinstance( node, int ) or isinstance( node, long ) or isinstance( node, float ):
        return True

    return False

#   ---------------------------------------------------------------------------
def _plain( node ):                                                                                                    #pylint: disable=too-many-return-statements
    """
    Represent terminal AST as plain text.
    """
#   ---------------
    if node is None:
        return ''

#   ---- TRIM
    if isinstance( node, TRIM ):
        return node.trim( _plain( node.ast ))

#   ---- list
    if isinstance( node, list ):
        return ''.join( map( _plain, node ))

#   ---- LAZY
    if isinstance( node, LAZY ):
        return _plain( node.ast )

#   ---- PLAIN
    if isinstance( node, PLAIN ):
        return node.get_trimmed()

#   ---- str based | int | float | long
    return str( node )

#   ---------------------------------------------------------------------------
class RESULT( str ):
    """
    Result text.
    """
#   -----------------------------------
    files = {}

#   -----------------------------------
    def __new__( cls, val, browse = None, offset = None ):
        obj = str.__new__( cls, val )
        obj.browse = browse if browse else []
        obj.offset = offset if offset else []
        return obj

#   -----------------------------------
    def __repr__( self ):
        return '%s(%s, %s)' % ( self.__class__.__name__, str.__repr__( self ), repr( self.browse ))

#   -----------------------------------
    @classmethod
    def clean( cls ):
        cls.files = {}

#   -----------------------------------
    @classmethod
    def loc( cls, input_file, pos ):
        decl = yushell.source[ input_file ][ 0 ]
        if input_file.isdigit():
            result = []
#           -- location is into macro or eval import
            call = yushell.inclusion[ int( input_file )]
            if call:
#               -- call location
                result.extend( cls.loc( call.input_file, call.pos ))
#           -- macro or eval import location, negative position means - not to do relative shift
            result.extend( cls.loc( decl.input_file, -decl.pos ))
            return result

        fn = str( decl if decl else input_file )
        if fn not in cls.files:
            cls.files[ fn ] = len( cls.files )
        return [( 0, cls.files[ fn ], pos )]

#   -----------------------------------
    def add_text( self, other ):
        if other:
            browse = self.browse
            offset = self.offset
            l = len( self )
            base = offset[ -1 ][ 1 ] if offset else 0
            for p, val in other.offset:
                offset.append(( p + l, val + base ))

            l += base
            for p, sou, sou_p in other.browse:
                browse.append(( p + l, sou, sou_p ))

            return RESULT( str( self ) + str( other ), browse, offset )

        return self

#   ---------------------------------------------------------------------------
def _plain_with_browse( node ):                                                                                        #pylint: disable=too-many-return-statements
    """
    Represent terminal AST as plain text and create reference list.
    """
#   ---------------

    if node is None:
        return RESULT( '' )

#   ---- RESULT
    if isinstance( node, RESULT ):
        return node

#   ---- TRIM
    if isinstance( node, TRIM ):
        return node.trim_with_browse( _plain_with_browse( node.ast ))

#   ---- list
    if isinstance( node, list ):
        return reduce( RESULT.add_text, map( _plain_with_browse, node )) if node else RESULT( '' )

#   ---- LAZY
    if isinstance( node, LAZY ):
        return _plain_with_browse( node.ast )

#   ---- PLAIN
    if isinstance( node, PLAIN ):
        node = node.get_trimmed_with_browse()

#   ---- SOURCE
    if isinstance( node, SOURCE ):
        return RESULT( str( node ), RESULT.loc( node.input_file, node.pos ) if node and node.input_file else [])

#   ---- str based | int | float | long
    return RESULT( str( node ))

#   ---------------------------------------------------------------------------
def _list_to_bound( node ):
    """
    Convert list of atoms to list of parameters.
    """
#   ---------------
    if isinstance( node, list ):
        bound = []
        for i in node:
            if not isinstance( i, ATOM ):
                return NOT_FOUND

            bound.append(( [], i, None ))

        return bound

    return NOT_FOUND

#   ---------------------------------------------------------------------------
def _list_eval_1( args, env, depth = 0 ):
    """
    Evaluate first argument of list.
    """
#   ---------------
    if not args:
        return ( None, [])

    arg = yueval( args[ 0 ], env, depth + 1 )
#   ---- EMBED
    if isinstance( arg, EMBED ):
        if isinstance( arg.ast, list ):
            if arg.ast:
                return ( arg.ast[ 0 ], arg.ast[ 1: ] + args[ 1: ])

            return _list_eval_1( args[ 1: ], env, depth + 1 )

#   ---- EMBED -- VAR | APPLY
        if isinstance( arg.ast, VAR ) or isinstance( arg.ast, APPLY ):
#           -- unreducible
            return ( NOT_FOUND, args )

        return ( arg.ast, args[ 1: ])

    return ( arg, args[ 1: ])

#   ---------------------------------------------------------------------------
def trace__eval_in_( node, env, depth ):
    if trace.enabled:
        trace.info( TR_INDENT * depth + TR_EVAL_IN + _ast_pretty( repr( node )))
        trace.info( TR_EVAL_ENV + _ast_pretty( repr( env )))

#   ---------------------------------------------------------------------------
def trace__eval_out_( node, depth ):
    if trace.enabled:
        trace.info( TR_INDENT * depth + TR_EVAL_OUT + _ast_pretty( repr( node )))

#   ---------------------------------------------------------------------------
def echo__eval_( fn ):
    def wrapped( node, env = ENV(), depth = 0 ):
        if depth > trace.deepest:
            trace.deepest = depth
        trace__eval_in_( node, env, depth )
        result = fn( node, env, depth )
        trace__eval_out_( result, depth )
        return result

    return wrapped

#   ---------------------------------------------------------------------------
@echo__eval_
def yueval( node, env = ENV(), depth = 0 ):                                                                            #pylint: disable=too-many-statements,too-many-branches,too-many-return-statements,too-many-locals
    """
    AST reduction.
    """
#   -----------------------------------
    def _callee():
        return 'yueval'

#   ---------------
#   TODO: This is an experimental release of the eval-apply cycle, it's slightly theoretically incorrect and unstable,
#   you may run into problems using a recursion or to face with a wrong scope of a name binding.
                                                                                                                       #pylint: disable=too-many-nested-blocks,redefined-variable-type
    try:
        tr = False
        while True:
            if tr:
#               -- trace eliminated tail recursion
                trace__eval_in_( node, env, depth )
            else:
                tr = True
#   ---- TEXT --> T
            if isinstance( node, TEXT ):
                node = T( node.ast )
                # fall through -- yueval( node )
#   ---- T
            elif isinstance( node, T ):
                t = T([], node.indent )
                skip_level = 0
                for i, x in enumerate( node ):
                    nx = i + 1
                    x_apply = isinstance( x, APPLY )
#                   -- skip text upto the end of module
                    if skip_level:
                        if isinstance( x, IMPORT_BEGIN ):
                            skip_level += 1
                        elif isinstance( x, IMPORT_END ):
                            skip_level -= 1
#                       -- skip node
                        continue
#   ---- T -- PLAIN
                    if isinstance( x, PLAIN ):
                        if x.indent is None:
#                           -- prior value
                            x_indent = node.indent
                        else:
#                           -- plain's value
                            x_indent = x.indent
                    else:
                        x_indent = False
#   ---- T -- COMMENT
                    if isinstance( x, COMMENT ):
                        if isinstance( node.indent, str ) and ( nx < len( node )) and isinstance( node[ nx ], PLAIN ):
#                           -- delete spacing
                            node[ nx ].trim = True
#                       -- skip node
                        continue

                    x = yueval( x, env, depth + 1 )
                    if x is None:
#                       -- skip node
                        continue

#   ---- T -- SKIP
                    if isinstance( x, SKIP ):
                        skip_level = 1
#                       -- skip node
                        continue

#   ---- T -- IMPORT_BEGIN | IMPORT_END
                    if isinstance( x, IMPORT_BEGIN ) or isinstance( x, IMPORT_END ):
#                       -- skip node
                        continue

#   ---- T -- ENV
                    if isinstance( x, ENV ):
#                       -- !? SET scope is limited with current TEXT block...
                        if nx < len( node ):
                            if isinstance( node.indent, str ) and isinstance( node[ nx ], PLAIN ):
#                               -- delete spacing
                                node[ nx ].trim = True
                            del node[ :nx ]
#                           -- !? extend
                            t.append( yueval( SET_CLOSURE( node, x ), env, depth + 1 ))
                        else:
#                           -- item is ignored
                            log.warn( 'useless assign' + x.loc())
                        break

#   ---- T -- EMBED --> T
                    if isinstance( x, EMBED ):
                        if isinstance( x.ast, T ):
#                           -- add indent of application to each line of substituting text
                            if node.indent:
                                for ii, xx in enumerate( x.ast ):
                                    if isinstance( xx, PLAIN ):
                                        x.ast[ ii ] = xx.add_indent( node.indent )
#                           -- insert the embedded AST in the beginning of remaining nodes and evaluate them together
#                           -- it's necessary because ($macro) can contain ($set)
                            del node[ :nx ]
                            node[ 0:0 ] = x.ast
                            tail = yueval( node, env, depth + 1 )

                            if isinstance( tail, list ):
                                t.extend( tail )
                            else:
                                t.append( tail )
                            break

                        else:
                            x = x.ast
#                   -- indent mimicry
                    t.append( TRIM( x, node.indent ) if x_apply else x )
                    node.indent = x_indent

                if _is_term( t ):
                    return _plain_with_browse( t ) if config.pp_browse else _plain( t )

#               -- unreducible
                return t

#   ---- APPLY
            elif isinstance( node, APPLY ):
                _call = node.fn.atom if isinstance( node.fn, VAR ) else None

                node.fn = yueval( node.fn, env, depth + 1 )
                node.args = yueval( node.args, env, depth + 1 )

#   ---- APPLY -- BUILTIN
                if isinstance( node.fn, BUILTIN ):
                    if node.named:
                        raise TypeError( '%s: unexpected named argument of built-in function' % ( _callee())
                        + node.named[ 0 ][ 0 ].loc())

#   ---- APPLY -- BUILTIN_SPECIAL
                    if isinstance( node.fn, BUILTIN_SPECIAL ):
                        if node.fn.atom in [ 'lazy', 'repr' ]:
                            if len( node.args ) != 1:
                                raise TypeError( '%s: only one argument expected' % ( _callee())
                                + node.fn.atom.loc())

                            if not isinstance( node.args[ 0 ], VAR ):
#                               -- argument is substituted
                                return node.fn.fn( node.args[ 0 ])
#                           -- unreducible
                            return node

                        if node.fn.atom == 'reduce':
                            if len( node.args ) < 2 and not isinstance( node.args[ 0 ], BUILTIN ):
                                raise TypeError( '%s: unexpected arguments of "reduce"' % ( _callee())
                                + node.fn.atom.loc())

                            if _is_term( node.args[ 1: ]):
                                return node.fn.fn( node.args[ 0 ].fn, *node.args[ 1: ])

                        if node.fn.atom == 'isatom':
                            if len( node.args ) != 1:
                                raise TypeError( '%s: only one argument expected' % ( _callee())
                                + node.fn.atom.loc())

                            if isinstance( node.args[ 0 ], ATOM ) or isinstance( node.args[ 0 ], VAR ):
#                               -- undefined or LATE_BOUNDED variable
                                return 1

                            return 0

#   ---- APPLY -- BUILTIN -- function
                    if callable( node.fn.fn ):
                        if _is_term( node.args ):
                            try:
                                val = node.fn.fn( *node.args )
                            except:
                                e_type, e, tb = sys.exc_info()
                                raise e_type, '%s: python: %s' % ( _callee(), e ) + node.loc(), tb

                            return int( val ) if isinstance( val, bool ) else val

#                       -- unreducible
                        return node

#   ---- APPLY -- BUILTIN -- const
                    if node.args:
                        raise TypeError( '%s: no arguments of constant expected' % ( _callee())
                        + node.fn.atom.loc())

                    return node.fn.fn

#   ---- APPLY -- int | float | long (subscripting)
                elif isinstance( node.fn, int ) or isinstance( node.fn, long ) or isinstance( node.fn, float ):
                    if node.named:
                        raise TypeError( '%s: unexpected named argument of index function' % ( _callee())
                        + node.named[ 0 ][ 0 ].loc())

                    if node.args:
                        if _is_term( node.args ):
                            pos = int( node.fn )
#                           -- (syntactic sugar) if only one argument and it's a list - apply operation to it
                            if len( node.args ) == 1 and isinstance( node.args[ 0 ], list ):
                                return node.args[ 0 ][ pos ] if pos < len( node.args[ 0 ]) else None
                            else:
                                return node.args[ pos ] if pos < len( node.args ) else None

#                       -- unreducible
                        return node

                    return node.fn

#   ---- APPLY -- TEXT | T
                elif isinstance( node.fn, TEXT ) or isinstance( node.fn, T ):
#                   -- !? (unreachable code)
                    if node.args or node.named:
                        raise TypeError( '%s: no arguments of text expected' % ( _callee())
                        + node.loc())

                    node = node.fn
                    # fall through -- yueval( node )

#   ---- APPLY -- L_CLOSURE -- e.g. APPLY( form, arg0, arg1 )
#                           --> yueval( apply( yueval( apply( yueval( form ) yueval( arg0 ))) yueval( arg1 )))
#   ---- APPLY -- M_CLOSURE
                elif isinstance( node.fn, LAMBDA_CLOSURE ):
                    node.fn.call = _call
#                   -- apply named arguments
                    if node.named:
                        var, val = node.named.pop( 0 )
                        if var in node.fn.env:
                            if not isinstance( node.fn.env[ var ], BOUND ):
                                log.warn( 'parameter "%s" is already assigned with value' % ( str( var )) + var.loc())
                            val = yueval( val, env, depth + 1 )
                        else:
                            raise TypeError( '%s: function has no parameter "%s"' % ( _callee(), str( var ))
                            + var.loc())

#                   -- apply anonymous arguments
                    elif node.args:
                        var = node.fn.env.unassigned()
                        if var is NOT_FOUND:
                            log.warn( 'unused argument(s) %s' % ( repr( node.args )) + node.loc())
                            return yueval( node.fn, env, depth + 1 )

                        if var == __va_args__:
#   TODO: handle if refuge is not the last parameter...
                            val = LIST( node.args )
                            node.args = []
                        else:
                            val, node.args = _list_eval_1( node.args, env, depth + 1 )

#                       -- unreducible -- EMBED
                        if val is NOT_FOUND:
                            return node

#                   -- no arguments
                    else:
                        var = node.fn.env.unassigned()
#                       -- no parameters
                        if var is NOT_FOUND:
                            return yueval( node.fn, env, depth + 1 )

#                       -- no default
                        if var not in node.fn.default:
#                           -- result is LAMBDA_CLOSURE (BOUND)
                            return node.fn

#                       -- apply default
                        val = yueval( node.fn.default[ var ], env, depth + 1 )
#                   -- late bounded -- second yueval()
                    if var in node.fn.late:
                        val = yueval( L_CLOSURE( val, ENV( None, node.fn.late[ var ])), env, depth + 1 )
                    node.fn.env[ var ] = val
#                   -- have no more arguments and default
                    if not node.named and not node.args and node.fn.env.unassigned() not in node.fn.default:
                        node = node.fn
                    # fall through -- yueval( node ) -- apply next argument

#   ---- APPLY -- LAZY
                elif isinstance( node.fn, LAZY ):
                    node.fn = node.fn.ast
                    # fall through -- yueval( node )

#   ---- APPLY -- ATOM
                elif isinstance( node.fn, ATOM ):
                    if node.named or node.args:
                        raise TypeError( '%s: no arguments of unbound atom expected' % ( _callee())
                        + node.fn.loc())
                    if config.warn_unbound_application:
                        log.warn( 'application of unbound atom "%s"' % ( node.fn ) + node.fn.loc())
                    return node.fn

#   ---- APPLY -- str
                elif isinstance( node.fn, str ):
#                   -- have no arguments
                    if not node.named and not node.args:
                        return node.fn

#                   -- format string
                    term = True
                    for i, ( var, val ) in enumerate( node.named ):
                        val = yueval( val, env, depth + 1 )
                        node.named[ i ] = ( var, val )
                        term = term and _is_term( val )
                    if not term or not _is_term( node.args ):
#                       -- unreducible
                        return node

                    for i, val in enumerate( node.args ):
                        node.fn = node.fn.replace( '($' + str( i ) + ')', _plain( val ))
                    for var, val in node.named:
                        node.fn = node.fn.replace( '($' + str( var ) + ')', _plain( val ))
                    return STR( node.fn )

#   ---- APPLY -- list ("for each" loop)
                elif isinstance( node.fn, list ):
                    if node.named:
                        raise TypeError( '%s: unexpected named argument of foreach function' % ( _callee())
                        + node.named[ 0 ][ 0 ].loc())

#                   -- !? is it right without
#                   if not _is_term( node.fn ):
#                       -- unreducible
#                       return node

                    lst = LIST()
                    for x in node.fn:
                        for arg in node.args:
                            fn = copy.deepcopy( arg )
                            x = yueval( APPLY( fn, [ x ], []), env, depth + 1 )
                        if x is not None:
                            lst.append( x )
                    return lst

#   ---- APPLY -- SKIP
                elif isinstance( node.fn, SKIP ):
                    return node.fn

#   ---- APPLY -- None
                elif node.fn is None:
                    return None

#   ---- APPLY -- ...
                else:
#                   -- unreducible
                    return node

#   ---- VAR
            elif isinstance( node, VAR ):
                val = env.lookup( node.reg, node.atom )
                if val is NOT_FOUND:
#   ---- VAR -- LATE_BOUNDED
                    if isinstance( node.reg, LATE_BOUNDED ):
#                       -- unreducible
                        return node

                    if not node.reg:
#   ---- VAR -- BUILTIN
                        if node.atom in builtin:
                            return BUILTIN( node.atom, builtin[ node.atom ])

#   ---- VAR -- BUILTIN_SPECIAL
                        if node.atom in builtin_special:
                            return BUILTIN_SPECIAL( node.atom, builtin_special[ node.atom ])

#                       -- if not valid C identifier mark as LATE_BOUNDED
                        if not node.atom.is_valid_c_id():
                            node.reg = LATE_BOUNDED()
#                           -- unreducible
                            return node

                        return node.atom

                    raise TypeError( '%s: undefined variable "%s"' % ( _callee(), str( node.atom ))
                    + node.atom.loc())

#   ---- VAR -- BOUND
                if isinstance( val, BOUND ):
#                   -- unreducible
                    return node

                return copy.deepcopy( val )

#   ---- LAMBDA --> L_CLOSURE
            elif isinstance( node, LAMBDA ):
#   ---- LAMBDA -- VAR
                if isinstance( node.bound, VAR ):
                    val = env.lookup( node.bound.reg, node.bound.atom )
                    if isinstance( val, BOUND ):
#                       -- unreducible
                        return node

                    bound_atom = node.bound.atom
                    node.bound = _list_to_bound( val )
                    if node.bound is NOT_FOUND:
                        raise TypeError( '%s: illegal parameters list' % ( _callee()) + bound_atom.loc())

#   ---- LAMBDA -- VAR | list
                d_late = {}
                d_default = {}
                env_l = ENV()
#               -- convert to L_CLOSURE
                for late, var, default in node.bound:
                    if late:
                        d_late[ var ] = [( key, BOUND()) for key in late ]
                    if default is not None:
                        d_default[ var ] = yueval( default, env, depth + 1 )
                    if var == ATOM( '...' ):
                        var = __va_args__
                    env_l[ var ] = BOUND()
#               -- eval L_CLOSURE
                node = L_CLOSURE( node.l_form, env_l, d_late, d_default )                                              #pylint: disable=redefined-variable-type
                # fall through -- yueval( node )

#   ---- L_CLOSURE
            elif isinstance( node, L_CLOSURE ):
                node.env.parent = env
                if node.env.unassigned() is not NOT_FOUND:
                    node.l_form = yueval( node.l_form, node.env, depth + 1 )
#                   -- unreducible
                    return node

                env = node.env
                node = node.l_form
                # fall through -- yueval( node )

#   ---- SET --> ENV
            elif isinstance( node, SET ):
                env_l = ENV( env )
                if isinstance( node.lval, ATOM ):
                    env_l[ node.lval ] = BOUND()
                else:
                    for i, var in enumerate( node.lval ):
                        env_l[ var ] = BOUND()
#               -- circular reference
                val = yueval( node.ast, env_l, depth + 1 )
                if isinstance( node.lval, ATOM ):
                    env_l[ node.lval ] = val
                else:
                    if isinstance( val, list ):
                        for i, var in enumerate( node.lval ):
                            if len( val ) > i:
                                env_l[ var ] = val[ i ]
                            else:
                                log.warn( 'there is nothing to assign to "%s"' % ( str( var )) + node.loc())
                                env_l[ var ] = None
                    else:
                        for var in node.lval:
                            env_l[ var ] = val
                return env_l

#   ---- SET_CLOSURE
            elif isinstance( node, SET_CLOSURE ):
                node.env.parent = env
                node.form = yueval( node.form, node.env, depth + 1 )
                if _is_term( node.form ):
                    return node.form

#               -- unreducible
                return node

#   ---- MACRO --> ENV( None, ( name, M_CLOSURE( text, ENV( None, [( par, BOUND )]))))
            elif isinstance( node, MACRO ):
                return ENV( None, [( node.name, M_CLOSURE( node.text, ENV( None
                , zip( node.pars, [ BOUND()] * len( node.pars ))), node.name ))])

#   ---- M_CLOSURE --> EVAL
            elif isinstance( node, M_CLOSURE ):
                if not node.env.eval_local( env, depth + 1 ):
#                   -- unreducible
                    return node

                for var, val in node.env.xlocal():
                    node.l_form = node.l_form.replace( '($' + str( var ) + ')', _plain_back( val ))
                node = EVAL( node.l_form, node.decl, node.call )
                # fall through -- yueval( node )

#   ---- EVAL --> EMBED
            elif isinstance( node, EVAL ):
                node.ast = yueval( node.ast, env, depth + 1 )
                if not isinstance( node.ast, str ):
#                   -- unreducible
                    return node

                if isinstance( node.ast, STR ):
                    node.ast = _unq( node.ast ).strip()
#                   -- (syntactic sugar) enclose string into ($ )
                    if not node.ast.startswith( '($' ):
                        node.ast = '($' + node.ast + ')'

                yushell.inclusion.append( node.call )
                _macro = str( len( yushell.inclusion ) - 1 )
                yushell.source[ _macro ] = ( node.decl, node.ast )
                node = yuparse( _macro )
                if not node.ast:
                    return None

                if any( isinstance( x, SET ) for x in node.ast ):
                    return EMBED( T( node.ast ))

#               -- !? e.g. ($ \p.($...))
                node = T( node.ast ) if len( node.ast ) > 1 else node.ast[ 0 ]
                # fall through -- yueval( node )

#   ---- COND --> COND_CLOSURE
            elif isinstance( node, COND ):
                node.cond = yueval( node.cond, env, depth + 1 )
                if not _is_term( node.cond ):
#                   -- unreducible
                    return COND_CLOSURE( node.cond, node.leg_1, node.leg_0 )

                node = node.leg_1 if node.cond else node.leg_0
                # fall through -- yueval( node )

#   ---- COND_CLOSURE
            elif isinstance( node, COND_CLOSURE ):
                node.cond = yueval( node.cond, env, depth + 1 )
                if not _is_term( node.cond ):
#                   -- FIXME !? potential problem of infinite recursion...
#                   -- also it makes impossible to perform operations with side effect such as raising an exception
                    node.leg_1 = yueval( node.leg_1, env, depth + 1 )
                    node.leg_0 = yueval( node.leg_0, env, depth + 1 )
#                   -- unreducible
                    return node

                node = yueval( node.leg_1 if node.cond else node.leg_0, env, depth + 1 )
                # fall through -- yueval( node )

#   ---- INFIX --> INFIX_CLOSURE
            elif isinstance( node, INFIX ):
                node.ast = yueval( node.ast, env, depth + 1 )
                if not isinstance( node.ast, str ):
#                   -- unreducible
                    return node

                try:
                    tree = parse( node.ast.lstrip(), mode = 'eval' )
                except:
                    e_type, e, tb = sys.exc_info()
                    raise e_type, '%s: python: %s' % ( _callee(), e ) + node.loc(), tb

                infix_visitor = INFIX_VISITOR()
                infix_visitor.visit( tree )

                env_l = ENV()
                for name in infix_visitor.names:
                    val = env.lookup( [], name )
                    if val is not NOT_FOUND:
                        env_l[ ATOM( name )] = VAR( [], ATOM( name ))

                input_file = node.input_file
                pos = node.pos
                node = INFIX_CLOSURE( tree, env_l, node.ast, input_file, pos )
                # fall through -- yueval( node )

#   ---- INFIX_CLOSURE
            elif isinstance( node, INFIX_CLOSURE ):

                if not node.env.eval_local( env, depth + 1 ):
#                   -- unreducible
                    return node

                try:
                    code = compile( node.tree, '', 'eval' )
                    return eval( code, dict( globals(), **builtin ), node.env )                                        #pylint: disable=eval-used

                except:
                    e_type, e, tb = sys.exc_info()
                    raise e_type, '%s: python: %s' % ( _callee(), e ) + node.loc(), tb

#   ---- EMIT
            elif isinstance( node, EMIT ):
                val = env.lookup( node.var.reg, node.var.atom )
                if val is NOT_FOUND:
                    raise TypeError( '%s: undefined variable "%s"' % ( _callee(), str( node.var.atom ))
                    + node.var.atom.loc())

#   ---- EMIT -- VAR -- BOUND
                if isinstance( val, BOUND ):
#                   -- unreducible
                    return node

                if isinstance( val, list ):
                    if len( val ):
                        result = val[ 0 ]
                        del val[ 0 ]
                    else:
                        result = None
                else:
                    result = val

                if node.ast:
                    val = yueval( APPLY( node.ast, [ val ], []), env, depth + 1 )
                    env.update_variable( node.var.reg, node.var.atom, val )
                return result

#   ---- LIST | list
            elif isinstance( node, list ):
                lst = LIST()
                for i, x in enumerate( node ):
                    x = yueval( x, env, depth + 1 )
#                   -- !? also LAMBDA_CLOSURE
                    if isinstance( x, BUILTIN ):
                        yushell.hazard.append( x.atom )

                    if x is None:
                        continue
#   ---- LIST -- EMBED
                    if isinstance( x, EMBED ):
                        if isinstance( x.ast, list ):
                            lst.extend( x.ast )
                        else:
#   ---- LIST -- EMBED -- VAR | APPLY
                            if isinstance( x.ast, VAR ) or isinstance( x.ast, APPLY ):
#                               -- unreducible
                                lst.append( x )
                            else:
                                lst.append( x.ast )
                    else:
                        lst.append( x )
                return lst

#   ---- EMBED | TRIM
            elif isinstance( node, EMBED ) or isinstance( node, TRIM ):
                node.ast = yueval( node.ast, env, depth + 1 )
                return node

#   ---- INT
#   ---- FLOAT
#   ---- STR
#   ---- REMARK
#   ---- PLAIN
            else:
                return node

    except:                                                                                                            #pylint: disable=bare-except
        e_type, e, tb = sys.exc_info()
#   ---- Python or recursive exception
        arg = e.args[ 0 ] if e.args else None
        if ( not isinstance( arg, str )
        or not arg.startswith( 'yueval' ) and not arg.startswith( 'python' ) and not arg.startswith( 'ps_' )):
            if isinstance( arg, str ) and arg.startswith( 'maximum recursion depth' ):
                raise e_type, 'yueval: %s' % ( e ), tb
            else:
#               -- this 'raise' expr. could be cause of new exception when maximum recursion depth is exceeded
                raise e_type, 'python: %s' % ( e ) + node.loc(), tb

#   ---- raised exception
        else:
            raise e_type, e, tb

#   ---------------------------------------------------------------------------
def yuinit():
    RESULT.clean()

    if yushell.output_py and not ps_string_py.initialized:
#       -- initialize regexes for ps_string_py()
        ps_string_py.initialized = True
#       -- head of any string
        ps_string_py.re_STR_HEAD = re.compile( r"""
        ^[uU]?[rR]?(?:
            ( '''
            | \"\"\"
            )
          | ( '[^\n'\\]*(?:\\.[^\n'\\]*)*(?:'|\\\n)
            | "[^\n"\\]*(?:\\.[^\n"\\]*)*(?:"|\\\n)
            )
        )
        """, re.VERBOSE )
        ps_string_py.group_3x = 1
#       -- tail of ' string
        ps_string_py.re_STR_1x1_TAIL = re.compile( r"[^'\\]*(?:\\.[^'\\]*)*'" )
#       -- tail of " string
        ps_string_py.re_STR_1x2_TAIL = re.compile( r'[^"\\]*(?:\\.[^"\\]*)*"' )
#       -- tail of ''' string
        ps_string_py.re_STR_3x1_TAIL = re.compile( r"[^'\\]*(?:(?:\\.|'(?!''))[^'\\]*)*'''" )
#       --  tail of """ string
        ps_string_py.re_STR_3x2_TAIL = re.compile( r'[^"\\]*(?:(?:\\.|"(?!""))[^"\\]*)*"""' )


#   * * * * * * * * * * * * * * * * * *
#   *                                 *
#   *       F I N A L   T E X T       *
#   *       P R O C E S S I N G       *
#   *                                 *
#   * * * * * * * * * * * * * * * * * *

#   ---------------------------------------------------------------------------
def make_ast_readable( node ):                                                                                         #pylint: disable=too-many-return-statements
    """
    Represent AST as readable text.
    """
#   ---- SET_CLOSURE
    if isinstance( node, SET_CLOSURE ):
#       -- node.env will be included into children
        return make_ast_readable( node.form )

#   ---- TRIM
    if isinstance( node, TRIM ):
        return node.trim( make_ast_readable( node.ast ))

#   ---- list
    if isinstance( node, list ):
        return ''.join( map( make_ast_readable, node ))

#   ---- LAZY
    if isinstance( node, LAZY ):
        return make_ast_readable( node.ast )

#   ---- PLAIN
    if isinstance( node, PLAIN ):
        return node.get_trimmed()

#   ---- str based | int | float | long
    if isinstance( node, str ) or isinstance( node, int ) or isinstance( node, long ) or isinstance( node, float ):
        return str( node )

    return _ast_pretty( repr( node ))

#   ---------------------------------------------------------------------------
def reduce_emptiness( text ):
    """
    Reduce number of successive empty lines up to one
    and trim tailing white space (depends on options).
    """
#   ---------------
    if not config.pp_reduce_emptiness:
        return text

    if isinstance( text, RESULT ):
        lnlist = text.splitlines( True )

#       -- find empty lines
        empty = set()
        for i, ln in enumerate( lnlist ):
            ( rest, _ ) = ps_space( ln )
            if rest == EOL:
                empty.add( i )

#       -- only reduce number of empty lines
        result = ''
        prev_empty = False
        for i, ln in enumerate( lnlist ):
            if i in empty:
                if not prev_empty:
                    result += ln
                    prev_empty = True
            else:
                result += ln
                prev_empty = False

#       -- calculate offsets
        offset = []
        total = 0
        _pos = pos = 0
        prev_empty = False
        for i, ln in enumerate( lnlist ):
            if i in empty:
                if prev_empty:
#                   -- reduce number of empty lines
                    total += len( ln )
                    if pos == _pos:
                        offset[ -1 ] = ( pos, total )
                    else:
                        offset.append(( pos, total ))
                        _pos = pos
                else:
                    pos += len( ln )
                    prev_empty = True
            else:
                pos += len( ln )
                prev_empty = False

#       -- merge with previous offsets
        if text.offset:
            offset = _merge_offset( text.offset, offset )

        return RESULT( result, text.browse, offset )

    def _filter( ln ):
        _empty = _filter.empty
        _filter.empty = not ln.strip()
        return not _empty or not _filter.empty

    _filter.empty = False

    return '\n'.join([ x.rstrip() for x in text.splitlines() if _filter( x )]) + '\n'

#   ---------------------------------------------------------------------------
def replace_steady( text ):
    result = text.replace( STEADY_TAB, '\t' ).replace( STEADY_SPACE, ' ' )
    if isinstance( text, RESULT ):
        return RESULT( result, text.browse, text.offset )

    return result
