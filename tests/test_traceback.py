import os
import sys
import traceback

import pytest

from tests.conftest import parse_source, run_source
from yupp.pp import yugen
from yupp import _traceback


@pytest.fixture(autouse=True)
def reset_traceback_state():
    _traceback._reset_for_tests()
    yield
    _traceback._reset_for_tests()


def test_runtime_traceback_maps_source_to_generated_file_and_line(tmp_path):
    source = tmp_path / "runtime.py"
    source.write_bytes(
        b"#!/usr/bin/env python\n"
        b"# coding: yupp\n"
        b"def fail():\n"
        b"    return 1 / 0\n"
        b"fail()\n"
    )

    process = run_source(source)

    assert process.returncode == 1
    assert "runtime.yugen.py" in process.stderr
    assert "runtime.py\", line" not in process.stderr
    assert "runtime.yugen.py\", line 4, in <module>" in process.stderr
    assert "runtime.yugen.py\", line 3, in fail" in process.stderr
    assert "return 1 / 0" in process.stderr
    assert "ZeroDivisionError" in process.stderr


def test_cached_coding_equals_traceback_keeps_first_run_line_delta(tmp_path):
    source = tmp_path / "equals.py"
    source.write_bytes(
        b"# coding=yupp\n"
        b"def fail():\n"
        b"    return 1 / 0\n"
        b"fail()\n"
    )

    first = run_source(source)
    generated = tmp_path / "equals.yugen.py"
    older = generated.stat().st_mtime - 2
    os.utime(source, (older, older))
    cached = run_source(source)

    for process in (first, cached):
        assert process.returncode == 1
        assert 'equals.yugen.py", line 4, in <module>' in process.stderr
        assert 'equals.yugen.py", line 3, in fail' in process.stderr
        assert "ZeroDivisionError" in process.stderr


@pytest.mark.skipif(sys.version_info < (3, 11), reason="ExceptionGroup requires Python 3.11")
def test_traceback_preserves_chains_notes_columns_and_nested_groups(tmp_path):
    source = tmp_path / "grouped.py"
    source.write_bytes(
        b"# coding: yupp\n"
        b"def make_error():\n"
        b"    try:\n"
        b"        value = {'answer': 42}['missing']\n"
        b"    except KeyError as cause:\n"
        b"        error = ValueError('outer')\n"
        b"        error.add_note('keep this note')\n"
        b"        error.__cause__ = cause\n"
        b"        return error\n"
        b"raise ExceptionGroup('group', [ExceptionGroup('nested', [make_error()])])\n"
    )

    process = run_source(source)

    assert process.returncode == 1
    assert "grouped.yugen.py" in process.stderr
    assert "keep this note" in process.stderr
    assert "KeyError" in process.stderr
    assert "ValueError: outer" in process.stderr
    assert "ExceptionGroup: nested" in process.stderr
    assert "^" in process.stderr


def test_traceback_keeps_stdlib_classes_and_functions_unmodified():
    stack_summary = traceback.StackSummary
    extract_tb = traceback.extract_tb
    print_exception = traceback.print_exception

    _traceback.install_mapping("source.py", "generated.py", 1)

    assert traceback.StackSummary is stack_summary
    assert traceback.extract_tb is extract_tb
    assert traceback.print_exception is print_exception


def test_unmapped_exception_delegates_to_prior_hook(monkeypatch):
    calls = []

    def previous(exc_type, value, tb):
        calls.append((exc_type, value, tb))

    monkeypatch.setattr(sys, "excepthook", previous)
    _traceback._reset_for_tests()
    _traceback.install_mapping("mapped.py", "generated.py", 1)
    error = ValueError("unmapped")

    sys.excepthook(ValueError, error, None)

    assert calls == [(ValueError, error, None)]


def test_keyboard_interrupt_always_delegates_to_prior_hook(monkeypatch):
    calls = []

    def previous(exc_type, value, tb):
        calls.append(exc_type)

    monkeypatch.setattr(sys, "excepthook", previous)
    _traceback._reset_for_tests()
    _traceback.install_mapping(__file__, "generated.py", 1)

    try:
        raise KeyboardInterrupt()
    except KeyboardInterrupt as error:
        sys.excepthook(KeyboardInterrupt, error, error.__traceback__)

    assert calls == [KeyboardInterrupt]


def test_installation_is_idempotent(monkeypatch):
    previous = sys.excepthook
    _traceback._reset_for_tests()
    monkeypatch.setattr(sys, "excepthook", previous)

    _traceback.install_mapping("one.py", "one.generated.py", 1)
    hook = sys.excepthook
    _traceback.install_mapping("two.py", "two.generated.py", 2)

    assert sys.excepthook is hook


def test_recursive_traceback_keeps_stdlib_compression(tmp_path):
    source = tmp_path / "recursive.py"
    source.write_bytes(
        b"# coding: yupp\n"
        b"import sys\n"
        b"sys.setrecursionlimit(80)\n"
        b"def recurse():\n"
        b"    recurse()\n"
        b"recurse()\n"
    )

    process = run_source(source)

    assert process.returncode == 1
    assert "recursive.yugen.py" in process.stderr
    assert "Previous line repeated" in process.stderr
    assert "RecursionError" in process.stderr


def test_evaluator_residual_keeps_source_location_across_resumptions():
    gate_1 = yugen.ATOM("gate_1")
    gate_2 = yugen.ATOM("gate_2")
    env = yugen.ENV()
    env.predeclare(gate_1)
    env.predeclare(gate_2)
    ast = parse_source("($div gate_1 gate_2)", "residual.yu")

    first = yugen.yueval(ast, env)
    env.publish(gate_1, yugen.INT(1))
    second = yugen.yueval(first, yugen.ENV())
    env.publish(gate_2, yugen.INT(0))

    with pytest.raises(ZeroDivisionError) as error:
        yugen.yueval(second, yugen.ENV())

    message = str(error.value)
    assert message.startswith("yueval: python: division by zero")
    assert 'File "residual.yu", line 1' in message
    assert "($div gate_1 gate_2)" in message
    assert "^" in message


@pytest.mark.parametrize(
    "source,filename,provenance",
    [
        (
            "($macro fail () ($div 1 0))($fail)",
            "macro-error.yu",
            'Macro "fail", line 1',
        ),
        (
            '($$ "($$ \\"($div 1 0)\\")")',
            "eval-error.yu",
            'Macro "<string>", line 1',
        ),
    ],
)
def test_dynamic_operation_errors_keep_declaration_and_inclusion_provenance(
    source, filename, provenance
):
    ast = parse_source(source, filename)

    with pytest.raises(ZeroDivisionError) as error:
        yugen.yueval(ast, yugen.ENV())

    message = str(error.value)
    assert message.startswith("yueval: python: division by zero")
    assert f'File "{filename}", line 1' in message
    assert provenance in message
    assert "($div 1 0)" in message
