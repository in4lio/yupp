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
            ok, code, fn_o, lnno = yup.proc_stream( self.stream, fn )                                                  #pylint: disable=access-member-before-definition
            if ok:
#               -- replace the filename of source file in traceback
                yutraceback.fn_subst[ fn ] = ( fn_o, lnno )
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

def search_function( s ):
    if not s.lower().startswith( __pp_name__ ):
        return None

    basereader = utf_8.StreamReader
    pos = s.find( '.' ) + 1
    if pos:
        codec = encodings.search_function( s[ pos: ])
        if codec is None:
            return None

        basereader = codec.streamreader

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
