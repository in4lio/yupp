from pathlib import Path

import pytest

from pp import yugen, yup


REPO_ROOT = Path(__file__).resolve().parents[1]


def parse_source(source, input_file=None, output_file=None):
    yugen.yushell(source, input_file, output_file)
    yugen.yuinit()
    return yugen.yuparse(yugen.yushell.input_file)


def evaluate_source(source, input_file=None, output_file=None):
    ast = parse_source(source, input_file, output_file)
    value = yugen.yueval(ast, yugen.ENV())
    if isinstance(value, str):
        value = yugen.replace_steady(yugen.reduce_emptiness(value))
    return ast, value


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
    yield
    for name, value in config_snapshot.items():
        setattr(yugen.config, name, value)
    yugen.builtin.clear()
    yugen.builtin.update(builtin_snapshot)
    for name in set(vars(yup.shell)) - set(shell_snapshot):
        delattr(yup.shell, name)
    for name, value in shell_snapshot.items():
        setattr(yup.shell, name, value)
    yugen.RESULT.clean()
