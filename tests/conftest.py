from contextlib import contextmanager
from dataclasses import dataclass
import logging
import os
from pathlib import Path
import subprocess
import sys

import pytest

from yupp.pp import yugen, yup


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_BOOTSTRAP = (
    "import runpy, sys, yupp; "
    "sys.argv[:] = sys.argv[1:]; "
    "runpy.run_path(sys.argv[0], run_name='__main__')"
)


@dataclass(frozen=True)
class EvaluationRecord:
    """Public-observation snapshot around one legacy evaluator call."""

    value: object
    ast_repr_before: str
    ast_repr_after: str


class _RecordHandler(logging.Handler):
    def __init__(self, records):
        super().__init__()
        self.records = records

    def emit(self, record):
        self.records.append((record.name, record.levelname, record.getMessage()))


def run_source(source, *arguments):
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    environment["PYTHON_COLORS"] = "0"
    return subprocess.run(
        [sys.executable, "-S", "-c", SOURCE_BOOTSTRAP, str(source), *arguments],
        cwd=source.parent,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )


def parse_source(source, input_file=None, output_file=None):
    yugen.yushell(source, input_file, output_file)
    yugen.yuinit()
    return yugen.yuparse(yugen.yushell.input_file)


def normalize_evaluator_value(value):
    if isinstance(value, str):
        return yugen.replace_steady(yugen.reduce_emptiness(value))
    return value


def evaluate_ast(ast, env=None):
    """Evaluate with an explicit fresh top-level environment and record AST drift."""
    ast_repr_before = repr(ast)
    value = yugen.yueval(ast, yugen.ENV() if env is None else env)
    return EvaluationRecord(
        normalize_evaluator_value(value),
        ast_repr_before,
        repr(ast),
    )


def evaluate_source(source, input_file=None, output_file=None):
    ast = parse_source(source, input_file, output_file)
    return ast, evaluate_ast(ast).value


@contextmanager
def capture_evaluator_logs():
    """Collect legacy ``log`` and ``trace`` records without private evaluator hooks."""
    records = []
    handler = _RecordHandler(records)
    for logger in (yugen.log, yugen.trace):
        logger.addHandler(handler)
    try:
        yield records
    finally:
        for logger in (yugen.log, yugen.trace):
            logger.removeHandler(handler)


@pytest.fixture(autouse=True)
def restore_runtime_configuration():
    """Keep the legacy module globals deterministic; tests must remain serial."""
    config_snapshot = {
        name: value.copy() if isinstance(value, list) else value
        for name, value in vars(yugen.config).items()
        if not name.startswith("__")
    }
    builtin_snapshot = dict(yugen.builtin)
    shell_snapshot = dict(vars(yup.shell))
    trace_snapshot = {
        "stage": yugen.trace.stage,
        "enabled": yugen.trace.enabled,
        "level": yugen.trace.level,
        "deepest": yugen.trace.deepest,
    }
    yield
    for name, value in config_snapshot.items():
        setattr(yugen.config, name, value)
    yugen.builtin.clear()
    yugen.builtin.update(builtin_snapshot)
    for name in set(vars(yup.shell)) - set(shell_snapshot):
        delattr(yup.shell, name)
    for name, value in shell_snapshot.items():
        setattr(yup.shell, name, value)
    yugen.trace.stage = trace_snapshot["stage"]
    yugen.trace.enabled = trace_snapshot["enabled"]
    yugen.trace.setLevel(trace_snapshot["level"])
    yugen.trace.deepest = trace_snapshot["deepest"]
    yugen.RESULT.clean()
