"""Bootstrap for the ``yupp`` source codec.

The decoder itself still delegates to the legacy preprocessor. Keeping that
import inside decoding makes ordinary ``import yupp`` safe and stdlib-only.
"""

import codecs
from encodings import search_function, utf_8


_PP_NAME = 'yupp'
_registered = False


def read_header( filename ):
    """Read the shebang and source encoding comment from *filename*."""
    header = ''
    try:
        with open( filename, 'r' ) as stream:
            header = stream.readline()
            if 'coding:' not in header:
                header += stream.readline()
    except Exception:
        pass
    return header


def decode_stream( filename, stream ):
    from ast import parse

    from .pp.yup import proc_stream
    from .pylib import yutraceback

    try:
        ok, code, output_filename, shrink = proc_stream( stream, filename )
    except Exception:
        yutraceback.print_exc( None )
        ok = False
    if not ok:
        return ''

    yutraceback.substitution( filename, output_filename, shrink )
    try:
        parse( code, output_filename )
    except SyntaxError:
        yutraceback.print_exc( 0 )
        code = ''
    return code


def decoder_factory( basecodec ):
    def decode( input_, errors='strict' ):
        from io import StringIO
        from sys import argv

        data, bytesencoded = basecodec.decode( input_, errors )
        filename = argv[ 0 ]
        source = StringIO( read_header( filename ) + data )
        return decode_stream( filename, source ), bytesencoded

    return decode


def incremental_decoder_factory( basecodec ):
    class IncrementalDecoder( codecs.BufferedIncrementalDecoder ):
        def _buffer_decode( self, input_, errors, final ):
            if input_ and final:
                return decoder_factory( basecodec )( input_, errors )
            return '', 0

    return IncrementalDecoder


def stream_decoder_factory( basecodec ):
    class StreamReader( basecodec.StreamReader ):
        def __init__( self, *args, **kwargs ):
            from io import StringIO

            basecodec.StreamReader.__init__( self, *args, **kwargs )
            self.stream = StringIO( decode_stream( self.stream.name, self.stream ))

    return StreamReader


def yupp_search_function( coding ):
    if not coding.lower().startswith( _PP_NAME ):
        return None

    dot = coding.find( '.' )
    if dot != -1:
        if dot != len( _PP_NAME ):
            return None
        basecodec = search_function( coding[( dot + 1 ): ] )
        if basecodec is None:
            return None
    else:
        if len( coding ) != len( _PP_NAME ):
            return None
        basecodec = utf_8

    return codecs.CodecInfo(
        name=_PP_NAME,
        encode=basecodec.encode,
        decode=decoder_factory( basecodec ),
        incrementalencoder=basecodec.IncrementalEncoder,
        incrementaldecoder=incremental_decoder_factory( basecodec ),
        streamwriter=basecodec.StreamWriter,
        streamreader=stream_decoder_factory( basecodec ),
    )


def register():
    """Register the source codec once per interpreter process."""
    global _registered
    if not _registered:
        codecs.register( yupp_search_function )
        _registered = True
