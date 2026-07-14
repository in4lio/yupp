"""Registration and direct-main implementation of the ``yupp`` source codec.

Python's codec API does not pass a source filename to a decoder.  Yupp only
preprocesses a real direct-main file whose complete contents match the decoder
input, either byte-for-byte or after CPython's deterministic newline
canonicalization.  Imported modules, stdin, ``-c`` and archive loaders
therefore fail closed instead of accidentally preprocessing ``sys.argv[0]``.
"""

import codecs
from io import StringIO
import os
import re
import sys


_PP_NAME = "yupp"
_COOKIE_RE = re.compile(
    rb"^[ \t\f]*#.*?coding[:=][ \t]*([-_.a-zA-Z0-9]+)"
)
_COOKIE_TEXT_RE = re.compile(
    r"(^[ \t\f]*#.*?coding[:=][ \t]*)([-_.a-zA-Z0-9]+)",
    re.IGNORECASE | re.MULTILINE,
)
_SECOND_LINE_ALLOWED_RE = re.compile(rb"^[ \t\f]*(?:[#\r\n]|$)")
_registered = False
_authorized_header_probes = {}


class YuppCodecError(UnicodeError):
    """A source cannot safely or successfully pass through the yupp codec."""


def _cookie_details(raw):
    if raw.startswith(codecs.BOM_UTF8):
        raise YuppCodecError("UTF-8 BOM conflicts with the yupp source encoding")

    lines = raw.splitlines(keepends=True)
    first = lines[0] if lines else b""
    match = _COOKIE_RE.match(first)
    cookie_line = 0
    if match is None and len(lines) > 1 and _SECOND_LINE_ALLOWED_RE.match(first):
        match = _COOKIE_RE.match(lines[1])
        cookie_line = 1
    if match is None:
        raise YuppCodecError("yupp source encoding cookie must be on line 1 or 2")
    cookie_bytes = lines[cookie_line]
    if cookie_bytes.endswith(b"\r\n"):
        cookie_content = cookie_bytes[:-2]
    elif cookie_bytes.endswith((b"\r", b"\n")):
        cookie_content = cookie_bytes[:-1]
    else:
        cookie_content = cookie_bytes
    prefix_length = sum(len(line) for line in lines[:cookie_line]) + len(
        cookie_content
    )
    return match.group(1).decode("ascii"), prefix_length, cookie_line


def _cookie(raw):
    return _cookie_details(raw)[0]


def _base_codec(cookie):
    lowered = cookie.lower()
    if lowered == _PP_NAME:
        return codecs.lookup("utf-8")
    if not lowered.startswith(_PP_NAME + "."):
        raise YuppCodecError("source encoding must be exactly yupp or yupp.<base>")
    base_name = cookie[len(_PP_NAME) + 1 :]
    if not base_name:
        raise YuppCodecError("yupp source encoding has an empty base encoding")
    return codecs.lookup(base_name)


def _read_candidate(filename):
    try:
        path = os.fspath(filename)
    except TypeError as error:
        raise YuppCodecError("yupp requires a direct filesystem main file") from error
    if not path or path in {"-", "-c"}:
        raise YuppCodecError("yupp requires a direct filesystem main file")

    path = os.path.abspath(path)
    if not os.path.isfile(path):
        raise YuppCodecError("yupp requires a readable direct filesystem main file")
    try:
        with open(path, "rb") as source:
            candidate = source.read()
    except (OSError, ValueError) as error:
        raise YuppCodecError(
            "yupp requires a readable direct filesystem main file"
        ) from error
    return path, candidate


def _normalize_newlines(raw):
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _canonical(raw):
    canonical = _normalize_newlines(raw)
    if canonical and not canonical.endswith(b"\n"):
        canonical += b"\n"
    return canonical


def _byte_variants(raw):
    """Return exact and CPython-canonicalized forms in stable order."""
    normalized = _normalize_newlines(raw)
    canonical = normalized
    if canonical and not canonical.endswith(b"\n"):
        canonical += b"\n"
    return tuple(dict.fromkeys((raw, normalized, canonical)))


def _verify_file_input(raw, filename):
    path, candidate = _read_candidate(filename)
    if candidate == raw:
        return path

    # CPython applies universal-newline conversion and appends one terminal
    # newline before invoking a source codec.  Scan the real candidate's raw
    # cookie first, then allow only that deterministic full-file transform.
    # The filename-less codec API still cannot distinguish two paths whose
    # complete files have identical raw/canonical bytes; no identity protocol
    # available to a decoder can resolve that collision.
    try:
        _cookie(candidate)
    except YuppCodecError as error:
        raise YuppCodecError(
            "yupp decoder input does not match the direct filesystem main file"
        ) from error
    canonical = _canonical(candidate)
    if canonical != raw:
        raise YuppCodecError(
            "yupp decoder input does not match the direct filesystem main file"
        )
    return path


def _decoder_inputs(candidate):
    """Return valid decoder streams and generated-prefix lines to omit.

    ``tokenize`` consumes the physical encoding-cookie line(s) before it starts
    an incremental source decoder.  Explicit codec users instead pass the
    complete file.  Candidate bytes from ``argv[0]`` remain authoritative in
    both cases; only exact or CPython-canonicalized complete streams/suffixes
    are accepted.
    """
    _, prefix_length, preceding_lines = _cookie_details(candidate)
    suffix = candidate[prefix_length:]
    inputs = []
    seen = set()
    for variants, omitted_lines in (
        (_byte_variants(candidate), 0),
        (_byte_variants(suffix), preceding_lines),
    ):
        for raw in variants:
            if raw in seen:
                continue
            seen.add(raw)
            inputs.append((raw, omitted_lines))
    return inputs


def _header_probe_inputs(candidate):
    _, _, preceding_lines = _cookie_details(candidate)
    lines = candidate.splitlines(keepends=True)
    header = b"".join(lines[: preceding_lines + 1])
    return _byte_variants(header)


def _authorize_header_probes(filename, candidate):
    _authorized_header_probes[os.path.realpath(filename)] = _header_probe_inputs(
        candidate
    )


def _decode_authorized_header_probe(raw, basecodec, errors):
    """Decode CPython 3.14's post-transform cookie probe, if authorized.

    After the incremental decoder has verified and preprocessed the complete
    main source, CPython 3.14 asks the stateless decoder to decode its cookie
    header in isolation (twice).  That fragment is returned as plain text and
    can never trigger preprocessing.  No header fragment is accepted before a
    complete stream for the same ``argv[0]`` has authorized it.
    """
    if not sys.argv:
        return None
    try:
        path = os.path.realpath(os.path.abspath(os.fspath(sys.argv[0])))
    except (OSError, TypeError, ValueError):
        return None
    if raw not in _authorized_header_probes.get(path, ()):
        return None
    _, candidate = _read_candidate(path)
    requested = _base_codec(_cookie(candidate))
    if requested.name != basecodec.name:
        raise YuppCodecError(
            "yupp cookie base encoding does not match the selected codec"
        )
    return basecodec.decode(raw, errors)


def _match_decoder_input(raw, filename, prefix=False):
    path, candidate = _read_candidate(filename)
    try:
        inputs = _decoder_inputs(candidate)
    except YuppCodecError as error:
        raise YuppCodecError(
            "yupp decoder input does not match the direct filesystem main file"
        ) from error
    matches = (
        omitted_lines
        for candidate_input, omitted_lines in inputs
        if (candidate_input.startswith(raw) if prefix else candidate_input == raw)
    )
    try:
        omitted_lines = next(matches)
    except StopIteration:
        raise YuppCodecError(
            "yupp decoder input does not match the direct filesystem main file"
        ) from None
    return path, candidate, omitted_lines


def _direct_main_input(raw, prefix=False):
    if not sys.argv:
        raise YuppCodecError("yupp requires a direct filesystem main file")
    return _match_decoder_input(raw, sys.argv[0], prefix=prefix)


def _preprocess(text, filename):
    from .pp.yup import proc_stream

    # The legacy header parser recognizes the encoding case-insensitively but
    # removes the ``yupp.`` prefix case-sensitively.  Canonicalize just the
    # already-validated cookie token before handing it over.
    text = _COOKIE_TEXT_RE.sub(
        lambda match: match.group(1) + match.group(2).lower(), text, count=1
    )
    ok, code, output_filename, shrink = proc_stream(StringIO(text), filename)
    if not ok or not isinstance(code, str):
        raise YuppCodecError("yupp preprocessing failed for %s" % filename)
    return code, output_filename, shrink


def _decode(raw, filename, errors, requested_base=None):
    if not raw:
        return "", 0

    cookie = _cookie(raw)
    base = _base_codec(cookie)
    if requested_base is not None and base.name != requested_base.name:
        raise YuppCodecError(
            "yupp cookie base encoding does not match the selected codec"
        )
    text, consumed = base.decode(raw, errors)
    code, output_filename, shrink = _preprocess(text, filename)

    # Surface generated syntax with the artifact name, rather than letting the
    # interpreter later report it against the macro source filename.
    try:
        compile(code, output_filename, "exec")
    except SyntaxError as error:
        # Python 3.14 rewrites a SyntaxError escaping a source decoder to the
        # original macro filename.  Keep the generated artifact explicit in
        # the codec error while preserving the SyntaxError as its cause.
        raise YuppCodecError(
            "generated Python SyntaxError in %s:%s: %s"
            % (output_filename, error.lineno or 1, error.msg)
        ) from error

    from ._traceback import install_mapping

    install_mapping(filename, output_filename, shrink)
    return code, consumed


def _without_prefix_lines(text, count):
    if not count:
        return text
    return "".join(text.splitlines(keepends=True)[count:])


def _decode_candidate(candidate, filename, errors, requested_base, omitted_lines):
    code, _ = _decode(candidate, filename, errors, requested_base)
    return _without_prefix_lines(code, omitted_lines)


def decode_verified(input_, filename, errors="strict"):
    """Decode bytes after explicitly verifying them against *filename*.

    This helper is intended for tests and trusted internal callers.  The
    production codec obtains the candidate only from ``sys.argv[0]``.
    """
    raw = bytes(input_)
    filename = _verify_file_input(raw, filename)
    return _decode(raw, filename, errors)


def decoder_factory(basecodec):
    def decode(input_, errors="strict"):
        raw = bytes(input_)
        if not raw:
            return "", 0
        probe = _decode_authorized_header_probe(raw, basecodec, errors)
        if probe is not None:
            return probe
        filename, candidate, omitted_lines = _direct_main_input(raw)
        code = _decode_candidate(
            candidate, filename, errors, basecodec, omitted_lines
        )
        return code, len(raw)

    return decode


def incremental_decoder_factory(basecodec):
    class IncrementalDecoder(codecs.BufferedIncrementalDecoder):
        def _buffer_decode(self, input_, errors, final):
            raw = bytes(input_)
            if not final:
                if raw:
                    # Validate the accumulated prefix without preprocessing or
                    # writing a generated artifact.  BufferedIncrementalDecoder
                    # retains every byte because the consumed count is zero.
                    _direct_main_input(raw, prefix=True)
                return "", 0
            if not raw:
                return "", 0
            filename, candidate, omitted_lines = _direct_main_input(raw)
            code = _decode_candidate(
                candidate, filename, errors, basecodec, omitted_lines
            )
            _authorize_header_probes(filename, candidate)
            return code, len(raw)

    return IncrementalDecoder


def stream_decoder_factory(basecodec):
    decode = decoder_factory(basecodec)

    class StreamReader:
        def __init__(self, stream, errors="strict"):
            self.stream = stream
            self.errors = errors
            raw = stream.read()
            text, _ = decode(raw, errors) if raw else ("", 0)
            self._decoded = StringIO(text)

        def read(self, size=-1, chars=-1, firstline=False):
            del firstline
            limit = chars if chars is not None and chars >= 0 else size
            if limit is None:
                limit = -1
            return self._decoded.read(limit)

        def readline(self, size=-1, keepends=True):
            del keepends
            if size is None:
                size = -1
            return self._decoded.readline(size)

        def readlines(self, sizehint=-1, keepends=True):
            del keepends
            if sizehint is None:
                sizehint = -1
            return self._decoded.readlines(sizehint)

        def reset(self):
            self._decoded.seek(0)

        def __iter__(self):
            return self

        def __next__(self):
            line = self.readline()
            if not line:
                raise StopIteration
            return line

    return StreamReader


def yupp_search_function(coding):
    lowered = coding.lower()
    if lowered != _PP_NAME and not lowered.startswith(_PP_NAME + "."):
        return None
    try:
        basecodec = _base_codec(coding)
    except YuppCodecError:
        return None
    codec_name = _PP_NAME
    if lowered != _PP_NAME:
        codec_name += "." + basecodec.name

    return codecs.CodecInfo(
        name=codec_name,
        encode=basecodec.encode,
        decode=decoder_factory(basecodec),
        incrementalencoder=basecodec.incrementalencoder,
        incrementaldecoder=incremental_decoder_factory(basecodec),
        streamwriter=basecodec.streamwriter,
        streamreader=stream_decoder_factory(basecodec),
    )


def register():
    """Register the stdlib-only source codec once per interpreter process."""
    global _registered
    if not _registered:
        codecs.register(yupp_search_function)
        _registered = True


__all__ = ["YuppCodecError", "decode_verified", "register"]
