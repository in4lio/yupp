r"""
http://github.com/in4lio/yupp/
 __    __    _____ _____
/\ \  /\ \  /\  _  \  _  \
\ \ \_\/  \_\/  \_\ \ \_\ \
 \ \__  /\____/\  __/\  __/
  \/_/\_\/___/\ \_\/\ \_\/
     \/_/      \/_/  \/_/

Python 'yupp' Codec Support
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from builtins import str

from future import standard_library
standard_library.install_aliases()

import codecs
from encodings import utf_8, search_function

from .pp.yulic import VERSION, DESCRIPTION, HOLDER, EMAIL
from .pp.yup import cli
from .pp.yup import proc_file as translate

#   ---------------------------------------------------------------------------
__pp_name__      = 'yupp'
__version__      = VERSION
__description__  = DESCRIPTION
__author__       = HOLDER
__author_email__ = EMAIL
__url__          = 'http://github.com/in4lio/yupp/'

#   ---------------------------------------------------------------------------
def read_header( fn ):
    '''
    Read shebang and magic comment from the source file.
    '''
    header = ''
    try:
        with open( fn, 'r' ) as f:
            header = f.readline()
            if 'coding:' not in header:
                header += f.readline()
    except:
        pass
    return header

#   ---------------------------------------------------------------------------
def decode_stream( fn, _stream ):
    from ast import parse
    from .pp.yup import proc_stream
    from .pylib import yutraceback

    try:
        ok, code, fn_o, shrink = proc_stream( _stream, fn )
    except Exception:
        yutraceback.print_exc( None )
        ok = False
    if not ok:
        return ''

#   -- replace the filename of source file in traceback
    yutraceback.substitution( fn, fn_o, shrink )
#   -- check syntax of the preprocessed code
    try:
        parse( code, fn_o )
    except SyntaxError:
        yutraceback.print_exc( 0 )
        code = ''
    return code

#   -- or using a dirty hack
    execfile( fn_o )
    return ''

#   ---------------------------------------------------------------------------
def decoder_factory( basecodec ):

#   -----------------------------------
    def decode( input, errors='strict' ):
        from io import StringIO
        from sys import argv

        data, bytesencoded = basecodec.decode( input, errors )
        fn = argv[ 0 ]
        return decode_stream( fn, StringIO( read_header( fn ) + data )), bytesencoded

    return decode

#   ---------------------------------------------------------------------------
def incremental_decoder_factory( basecodec ):

#   -----------------------------------
    class IncrementalDecoder( codecs.BufferedIncrementalDecoder ):

        def _buffer_decode( self, input, errors, final ):
            if input and final:
                return decoder_factory( basecodec )( input, errors )

#           -- we don't support incremental decoding
            return '', 0

    return IncrementalDecoder

#   ---------------------------------------------------------------------------
def stream_decoder_factory( basecodec ):

#   -----------------------------------
    class StreamReader( basecodec.StreamReader ):

        def __init__( self, *args, **kwargs ):
            from io import StringIO

            basecodec.StreamReader.__init__( self, *args, **kwargs )
            self.stream = StringIO( decode_stream( self.stream.name, self.stream ))

    return StreamReader

#   ---------------------------------------------------------------------------
def yupp_search_function( coding ):
    if not coding.lower().startswith( __pp_name__ ):
        return None

    dot = coding.find( '.' )
    if dot != -1:
#       -- coding: yupp.<encoding>
        if dot != len( __pp_name__ ):
#           -- wrong coding format
            return None

        basecodec = search_function( coding[( dot + 1 ): ])
        if basecodec is None:
#           -- unknown <encoding>
            return None

    else:
        if len( coding ) != len( __pp_name__ ):
#           -- wrong coding format
            return None

#       -- default encoding: UTF-8
        basecodec = utf_8

    return codecs.CodecInfo(
        name=__pp_name__,
        encode=basecodec.encode,
        decode=decoder_factory( basecodec ),
        incrementalencoder=basecodec.IncrementalEncoder,
        incrementaldecoder=incremental_decoder_factory( basecodec ),
        streamwriter=basecodec.StreamWriter,
        streamreader=stream_decoder_factory( basecodec )
    )

#   ---------------------------------------------------------------------------
codecs.register( yupp_search_function )
