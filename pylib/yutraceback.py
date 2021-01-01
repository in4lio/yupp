"""
Extract, format and print information about Python stack traces.

This module contains, compatible with yupp preprocessor, implementation
of 'print_tb', 'extract_tb' and 'extract_stack' functions, also
'sys.excepthook' function is replaced here.
Based on traceback.py @ 102173
"""

import linecache
import sys
import traceback
import functools

def _print(file, str='', terminator='\n'):
    file.write(str+terminator)

@functools.wraps(traceback.print_tb)
def print_tb(tb, limit=None, file=None):
    """Print up to 'limit' stack trace entries from the traceback 'tb'.

    If 'limit' is omitted or None, all entries are printed.  If 'file'
    is omitted or None, the output goes to sys.stderr; otherwise
    'file' should be an open file or file-like object with a write()
    method.
    """
    if file is None:
        file = sys.stderr
    if limit is None:
        if hasattr(sys, 'tracebacklimit'):
            limit = sys.tracebacklimit
    n = 0
    while tb is not None and (limit is None or n < limit):
        f = tb.tb_frame
        lineno = tb.tb_lineno
        co = f.f_code
#       -- filename = co.co_filename
        if co.co_filename in fn_subst:
            filename, shrink = fn_subst[co.co_filename]
        else:
            filename = co.co_filename
            shrink = 0
        lineno -= shrink
        if lineno < 1: lineno = 1
#       --
        name = co.co_name
        _print(file,
               '  File "%s", line %d, in %s' % (filename, lineno, name))
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)
        if line: _print(file, '    ' + line.strip())
        tb = tb.tb_next
        n = n+1

@functools.wraps(traceback.extract_tb)
def extract_tb(tb, limit = None):
    """Return list of up to limit pre-processed entries from traceback.

    This is useful for alternate formatting of stack traces.  If
    'limit' is omitted or None, all entries are extracted.  A
    pre-processed stack trace entry is a quadruple (filename, line
    number, function name, text) representing the information that is
    usually printed for a stack trace.  The text is a string with
    leading and trailing whitespace stripped; if the source is not
    available it is None.
    """
    if limit is None:
        if hasattr(sys, 'tracebacklimit'):
            limit = sys.tracebacklimit
    list = []
    n = 0
    while tb is not None and (limit is None or n < limit):
        f = tb.tb_frame
        lineno = tb.tb_lineno
        co = f.f_code
#       -- filename = co.co_filename
        if co.co_filename in fn_subst:
            filename, shrink = fn_subst[co.co_filename]
        else:
            filename = co.co_filename
            shrink = 0
        lineno -= shrink
        if lineno < 1: lineno = 1
#       --
        name = co.co_name
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)
        if line: line = line.strip()
        else: line = None
        list.append((filename, lineno, name, line))
        tb = tb.tb_next
        n = n+1
    return list

@functools.wraps(traceback.extract_stack)
def extract_stack(f=None, limit = None):
    """Extract the raw traceback from the current stack frame.

    The return value has the same format as for extract_tb().  The
    optional 'f' and 'limit' arguments have the same meaning as for
    print_stack().  Each item in the list is a quadruple (filename,
    line number, function name, text), and the entries are in order
    from oldest to newest stack frame.
    """
    if f is None:
        try:
            raise ZeroDivisionError
        except ZeroDivisionError:
            f = sys.exc_info()[2].tb_frame.f_back
    if limit is None:
        if hasattr(sys, 'tracebacklimit'):
            limit = sys.tracebacklimit
    list = []
    n = 0
    while f is not None and (limit is None or n < limit):
        lineno = f.f_lineno
        co = f.f_code
#       -- filename = co.co_filename
        if co.co_filename in fn_subst:
            filename, shrink = fn_subst[co.co_filename]
        else:
            filename = co.co_filename
            shrink = 0
        lineno -= shrink
        if lineno < 1: lineno = 1
#       --
        name = co.co_name
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)
        if line: line = line.strip()
        else: line = None
        list.append((filename, lineno, name, line))
        f = f.f_back
        n = n+1
    list.reverse()
    return list

@functools.wraps(traceback.print_exc)
def print_exc(limit=None, file=None):
    traceback.print_exc(limit, file)

@functools.wraps(sys.excepthook)
def excepthook(etype, value, tb):
    if issubclass(etype, KeyboardInterrupt):
        sys.__excepthook__(etype, value, tb)
    else:
        traceback.print_exception(etype, value, tb)


fn_subst = dict()

traceback.print_tb = print_tb
traceback.extract_tb = extract_tb
traceback.extract_stack = extract_stack
sys.excepthook = excepthook
