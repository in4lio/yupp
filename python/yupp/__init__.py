from __future__ import absolute_import
import codecs
import encodings
from encodings import utf_8
from . import yulic

__pp_name__      = 'yupp'
__version__      = yulic.VERSION
__description__  = yulic.DESCRIPTION
__author__       = yulic.HOLDER
__author_email__ = yulic.EMAIL
__url__          = 'http://github.com/in4lio/yupp/'

def yuppReaderFactory( BaseReader ):

    class yuppReader( BaseReader ):
        def __init__( self, *args, **kwargs ):
            import cStringIO
            import ast
            from . import yup
            from . import yutraceback

            BaseReader.__init__( self, *args, **kwargs )
            fn = self.stream.name                                                                                      #pylint: disable=access-member-before-definition
            ok, code, fn_o, shrink = yup.proc_stream( self.stream, fn )                                                #pylint: disable=access-member-before-definition
            if ok:
#               -- replace the filename of source file in traceback
                yutraceback.fn_subst[ fn ] = ( fn_o, shrink )
#               -- check syntax of the preprocessed code
                try:
                    ast.parse( code, fn_o )
                except SyntaxError:
                    yutraceback.print_exc( 0 )
                    code = ''
#               -- or just use dirty hack: execfile( fn_o ); code = ''
            else:
                code = ''
            self.stream = cStringIO.StringIO( code )

    return yuppReader

def search_function( coding ):
    if not coding.lower().startswith( __pp_name__ ):
        return None

    dot = coding.find( '.' )
    if dot != -1:
#       -- coding: yupp.<encoding>
        if dot != len( __pp_name__ ):
#           -- wrong coding format
            return None

        codec = encodings.search_function( coding[( dot + 1 ): ])
        if codec is None:
#           -- unknown <encoding>
            return None

        basereader = codec.streamreader
    else:
        if len( coding ) != len( __pp_name__ ):
#           -- wrong coding format
            return None

#       -- default encoding: UTF-8
        basereader = utf_8.StreamReader

    utf8 = encodings.search_function( 'utf8' )
    return codecs.CodecInfo(
        name=__pp_name__,
        encode=utf8.encode,
        decode=utf8.decode,
        incrementalencoder=utf8.incrementalencoder,
        incrementaldecoder=utf8.incrementaldecoder,
        streamreader=yuppReaderFactory( basereader ),
        streamwriter=utf8.streamwriter
    )

codecs.register( search_function )
