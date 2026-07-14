"""Public package API and source-codec bootstrap."""

from . import _codec
from ._metadata import DESCRIPTION, EMAIL, HOLDER, VERSION


__pp_name__ = 'yupp'
__version__ = VERSION
__description__ = DESCRIPTION
__author__ = HOLDER
__author_email__ = EMAIL
__url__ = 'http://github.com/in4lio/yupp/'

__all__ = [ 'cli', 'translate' ]


_codec.register()


def __getattr__( name ):
    if name == 'cli':
        from .pp.yup import cli

        globals()[ name ] = cli
        return cli
    if name == 'translate':
        from .pp.yup import proc_file

        globals()[ name ] = proc_file
        return proc_file
    raise AttributeError( "module %r has no attribute %r" % ( __name__, name ))


def __dir__():
    return sorted( set( globals()) | set( __all__ ))
