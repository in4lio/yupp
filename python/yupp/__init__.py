import codecs, encodings, cStringIO
from encodings import utf_8
import sys
import yup

__library__      = 'yupp'
__version__      = yup.VERSION
__description__  = yup.DESCRIPTION
__author__       = yup.HOLDER
__author_email__ = yup.EMAIL
__url__          = 'http://github.com/in4lio/yupp/'

class yuppStreamReader( utf_8.StreamReader ):
    def __init__( self, *args, **kwargs ):
        codecs.StreamReader.__init__( self, *args, **kwargs )
        data = _yupp( self.stream.read )
        self.stream = cStringIO.StringIO( data )

def _yupp( _read ):
    result, plain, fn_o = yup.pp_stream( _read, sys.argv[ 0 ])
    return plain if result else ''

def search_function( s ):
    if s != __library__: return None

    utf8 = encodings.search_function( 'utf8' )
    return codecs.CodecInfo(
        name=__library__,
        encode=utf8.encode,
        decode=utf8.decode,
        incrementalencoder=utf8.incrementalencoder,
        incrementaldecoder=utf8.incrementaldecoder,
        streamreader=yuppStreamReader,
        streamwriter=utf8.streamwriter
    )

codecs.register( search_function )
