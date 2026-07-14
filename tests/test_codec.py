import codecs
import io
import os
import subprocess
import sys

import pytest

from tests.conftest import REPO_ROOT
from yupp import _codec


BOOTSTRAP = (
    "import runpy, sys, yupp; "
    "sys.argv[:] = sys.argv[1:]; "
    "runpy.run_path(sys.argv[0], run_name='__main__')"
)


@pytest.fixture(autouse=True)
def reset_traceback_hook_after_codec_tests():
    yield
    module = sys.modules.get("yupp._traceback")
    if module is not None:
        module._reset_for_tests()


def run_source(source, *arguments):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    environment["PYTHON_COLORS"] = "0"
    return subprocess.run(
        [sys.executable, "-S", "-c", BOOTSTRAP, str(source), *arguments],
        cwd=source.parent,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


@pytest.mark.parametrize(
    "name",
    ["yupp", "YUPP", "yupp.utf-8", "Yupp.CP1252"],
)
def test_codec_lookup_accepts_only_exact_yupp_names(name):
    assert codecs.lookup(name).name.startswith("yupp")


@pytest.mark.parametrize("name", ["yuppx", "xyupp", "yupp_cp1252"])
def test_codec_lookup_rejects_near_miss_names(name):
    with pytest.raises(LookupError):
        codecs.lookup(name)


@pytest.mark.parametrize(
    "header",
    [
        b"# coding: yupp\n",
        b"# coding=yupp\n",
        b"#!/usr/bin/env python\n# coding: yupp\n",
    ],
)
def test_verified_decoder_preserves_header_shape_and_expands_macros(tmp_path, header):
    source = tmp_path / "hello.py"
    raw = header + b'($set answer 42)\nprint(($answer))\n'
    source.write_bytes(raw)

    text, consumed = _codec.decode_verified(raw, source)

    assert consumed == len(raw)
    assert "print(42)" in text
    assert text.count("#!/usr/bin/env python") == header.count(b"#!/usr/bin/env python")
    assert text.count("coding") <= 1


def test_verified_decoder_accepts_crlf_and_missing_final_newline(tmp_path):
    source = tmp_path / "shape.py"
    raw = b"#!/usr/bin/env python\r\n# coding: yupp\r\nprint('ok')"
    source.write_bytes(raw)

    text, consumed = _codec.decode_verified(raw, source)

    assert consumed == len(raw)
    assert text.startswith("#!/usr/bin/env python\n")
    assert text.count("#!/usr/bin/env python") == 1
    assert "print('ok')" in text

    process = run_source(source)
    assert process.returncode == 0, process.stderr
    assert process.stdout == "ok\n"


def test_direct_main_runs_utf8_and_cp1252_sources(tmp_path):
    utf8_source = tmp_path / "utf8.py"
    utf8_source.write_bytes(
        "# coding: yupp\nprint('Привет')\n".encode("utf8")
    )
    cp1252_source = tmp_path / "cp1252.py"
    cp1252_source.write_bytes(
        "# coding: yupp.cp1252\nprint('café')\n".encode("cp1252")
    )
    uppercase_source = tmp_path / "uppercase.py"
    uppercase_source.write_bytes(
        "# coding: YUPP.CP1252\nprint('olé')\n".encode("cp1252")
    )

    utf8 = run_source(utf8_source)
    cp1252 = run_source(cp1252_source)
    uppercase = run_source(uppercase_source)

    assert utf8.returncode == 0, utf8.stderr
    assert utf8.stdout == "Привет\n"
    assert cp1252.returncode == 0, cp1252.stderr
    assert cp1252.stdout == "café\n"
    assert uppercase.returncode == 0, uppercase.stderr
    assert uppercase.stdout == "olé\n"


def test_incremental_and_stream_decoders_buffer_complete_source(tmp_path, monkeypatch):
    source = tmp_path / "chunked.py"
    raw = b"# coding: yupp\nprint('chunked')\n"
    source.write_bytes(raw)
    monkeypatch.setattr(sys, "argv", [str(source)])

    decoder = codecs.getincrementaldecoder("yupp")()
    assert decoder.decode(raw[:7], final=False) == ""
    assert decoder.decode(raw[7:19], final=False) == ""
    assert "print('chunked')" in decoder.decode(raw[19:], final=True)

    reader = codecs.getreader("yupp")(io.BytesIO(raw))
    assert "print('chunked')" in reader.read()


def test_empty_incremental_and_stream_decoder_contracts():
    decoder = codecs.getincrementaldecoder("yupp")()
    assert decoder.decode(b"", final=False) == ""
    assert decoder.decode(b"", final=True) == ""
    assert codecs.getreader("yupp")(io.BytesIO()).read() == ""


def test_decoder_rejects_bom_unknown_base_and_preprocessor_failure(tmp_path):
    bom = tmp_path / "bom.py"
    bom_raw = codecs.BOM_UTF8 + b"# coding: yupp\nprint('no')\n"
    bom.write_bytes(bom_raw)
    with pytest.raises((SyntaxError, UnicodeError), match="BOM|encoding"):
        _codec.decode_verified(bom_raw, bom)

    with pytest.raises(LookupError):
        codecs.lookup("yupp.no_such_encoding")

    broken = tmp_path / "broken.py"
    broken_raw = b"# coding: yupp\n($set missing\n"
    broken.write_bytes(broken_raw)
    with pytest.raises(UnicodeError, match="preprocess"):
        _codec.decode_verified(broken_raw, broken)

    for source in (bom, broken):
        process = run_source(source)
        assert process.returncode != 0
        assert source.name in process.stderr

    unknown = tmp_path / "unknown.py"
    unknown.write_bytes(b"# coding: yupp.no_such_encoding\nprint('no')\n")
    process = run_source(unknown)
    assert process.returncode != 0
    assert "unknown encoding" in process.stderr.lower()


def test_generated_syntax_error_names_generated_artifact(tmp_path):
    source = tmp_path / "syntax.py"
    source.write_bytes(b"# coding: yupp\nif True print('bad')\n")

    process = run_source(source)

    assert process.returncode != 0
    assert "syntax.yugen.py" in process.stderr
    assert "SyntaxError" in process.stderr


@pytest.mark.parametrize("argv0", ["", "-", "-c"])
def test_decoder_rejects_non_filesystem_main_contexts(argv0, monkeypatch):
    monkeypatch.setattr(sys, "argv", [argv0])
    with pytest.raises(UnicodeError, match="direct filesystem main"):
        codecs.decode(b"# coding: yupp\nprint('no')\n", "yupp")


def test_decoder_rejects_mismatched_argv_without_preprocessing(tmp_path, monkeypatch):
    main = tmp_path / "main.py"
    main.write_bytes(b"print('unrelated')\n")
    victim = b"# coding: yupp\nprint('victim')\n"
    called = False

    def fail_if_called(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("preprocessor must not run")

    monkeypatch.setattr(sys, "argv", [str(main)])
    monkeypatch.setattr(_codec, "_preprocess", fail_if_called)

    with pytest.raises(UnicodeError, match="does not match"):
        codecs.decode(victim, "yupp")
    assert called is False
    assert not (tmp_path / "main.yugen.py").exists()


@pytest.mark.parametrize(
    "decoder_input",
    [
        b"# coding: yupp\nprint('changed')\n",
        b"# coding: yupp\nprint('ok')\nprint('extra')\n",
        b"# coding: yupp.cp1252\nprint('ok')\n",
    ],
    ids=["body", "length", "cookie"],
)
def test_canonical_identity_fallback_rejects_every_content_change(
    tmp_path, monkeypatch, decoder_input
):
    source = tmp_path / "canonical.py"
    source.write_bytes(b"# coding: yupp\r\nprint('ok')")
    called = False

    def fail_if_called(*args, **kwargs):
        nonlocal called
        called = True
        raise AssertionError("preprocessor must not run")

    monkeypatch.setattr(sys, "argv", [str(source)])
    monkeypatch.setattr(_codec, "_preprocess", fail_if_called)

    with pytest.raises(UnicodeError, match="does not match"):
        codecs.decode(decoder_input, "yupp")
    assert called is False


def test_decoder_rejects_zipapp_like_argv_without_preprocessing(tmp_path, monkeypatch):
    archive = tmp_path / "application.pyz"
    archive.write_bytes(b"PK\x03\x04not-a-source-module")
    module = b"# coding: yupp\nprint('inside archive')\n"
    called = False

    def fail_if_called(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(sys, "argv", [str(archive)])
    monkeypatch.setattr(_codec, "_preprocess", fail_if_called)

    with pytest.raises(UnicodeError, match="does not match"):
        codecs.decode(module, "yupp")
    assert called is False


def test_imported_yupp_module_is_rejected_without_touching_main(tmp_path):
    main = tmp_path / "main.py"
    main.write_text("import yupp\nimport victim\n", encoding="utf8")
    victim = tmp_path / "victim.py"
    victim.write_bytes(b"# coding: yupp\nprint('victim')\n")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join((str(REPO_ROOT / "src"), str(tmp_path)))

    process = subprocess.run(
        [sys.executable, "-S", str(main)],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )

    assert process.returncode != 0
    assert "direct filesystem main" in process.stderr
    assert not (tmp_path / "main.yugen.py").exists()
    assert not (tmp_path / "victim.yugen.py").exists()
