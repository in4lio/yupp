import sys
import traceback
import types

import pytest

from yupp.pp import yugen
from tests.conftest import evaluate_source, parse_source


@pytest.mark.integration
def test_atom_source_import_is_once_only(tmp_path):
    (tmp_path / "characterized.yu").write_text("FROM_LIBRARY", encoding="utf8")
    source = "($import characterized)($import characterized)"

    _, result = evaluate_source(source, str(tmp_path / "main.yu-c"), str(tmp_path / "main.c"))

    assert result.count("FROM_LIBRARY") == 1
    assert yugen.yushell.source["characterized.yu"][0] == str(tmp_path / "characterized.yu")


@pytest.mark.integration
def test_quoted_source_import_repeats_by_contract(tmp_path):
    library = tmp_path / "quoted.yu"
    library.write_text("QUOTED_LIBRARY", encoding="utf8")
    source = f'($import "{library}")($import "{library}")'

    _, result = evaluate_source(source, str(tmp_path / "main.yu-c"), str(tmp_path / "main.c"))

    assert result.count("QUOTED_LIBRARY") == 2


def test_computed_import_parses_the_expression_result_as_source():
    ast, result = evaluate_source("($import { '($set computed 3)($computed)' })")

    assert result == "3\n"
    assert "SET(ATOM('computed'), INT(3))" in repr(ast)
    assert yugen.yushell.source["0"][1] == "($set computed 3)($computed)"


@pytest.mark.integration
def test_python_import_keeps_module_identity_and_runs_once(tmp_path):
    module_name = "characterized_python_import"
    script = tmp_path / f"{module_name}.py"
    script.write_text(
        "import_count = 1\n"
        "module_token = object()\n"
        "python_value = 41\n",
        encoding="utf8",
    )
    source = f'($import "{script}")($import "{script}")($python_value)'
    try:
        ast = parse_source(source, str(tmp_path / "main.yu-c"), str(tmp_path / "main.c"))
        result = yugen.yueval(ast, yugen.ENV())

        module = sys.modules[module_name]
        assert str(result) == "41"
        assert module.import_count == 1
        assert yugen.builtin["module_token"] is module.module_token
        assert yugen.yushell.script == [str(script)]
    finally:
        sys.modules.pop(module_name, None)


@pytest.mark.integration
def test_same_named_python_import_collision_is_last_import_wins(tmp_path):
    module_name = "characterized_collision"
    first = tmp_path / "first" / f"{module_name}.py"
    second = tmp_path / "second" / f"{module_name}.py"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_text("collision_value = 'first'\nmodule_token = object()\n", encoding="utf8")
    second.write_text("collision_value = 'second'\nmodule_token = object()\n", encoding="utf8")
    source = f'($import "{first}")($import "{second}")'
    try:
        parse_source(source, str(tmp_path / "main.yu-c"), str(tmp_path / "main.c"))

        module = sys.modules[module_name]
        assert module.collision_value == "second"
        assert yugen.builtin["collision_value"] == "second"
        assert yugen.builtin["module_token"] is module.module_token
        assert yugen.yushell.script == [str(first), str(second)]
    finally:
        sys.modules.pop(module_name, None)


@pytest.mark.integration
def test_python_import_is_staged_for_recursive_self_import(tmp_path):
    module_name = "characterized_recursive_import"
    script = tmp_path / f"{module_name}.py"
    script.write_text(
        "import importlib\n"
        "import sys\n"
        "self_module = importlib.import_module(__name__)\n"
        "identity_preserved = self_module is sys.modules[__name__]\n",
        encoding="utf8",
    )
    try:
        parse_source(f'($import "{script}")', str(tmp_path / "main.yu-c"))

        module = sys.modules[module_name]
        assert module.self_module is module
        assert module.identity_preserved is True
        assert yugen.builtin["self_module"] is module
    finally:
        sys.modules.pop(module_name, None)


@pytest.mark.integration
@pytest.mark.parametrize(
    "has_previous", [False, True], ids=["without-prior-module", "with-prior-module"]
)
def test_failed_python_import_rolls_back_and_can_be_retried(
    tmp_path, has_previous
):
    module_name = "characterized_failed_import"
    script = tmp_path / f"{module_name}.py"
    script.write_text(
        "published_before_failure = object()\n"
        "def explode():\n"
        "    raise RuntimeError('module exploded')\n"
        "explode()\n",
        encoding="utf8",
    )
    previous = None
    if has_previous:
        previous = types.ModuleType(module_name)
        previous.sentinel = object()
        sys.modules[module_name] = previous
    else:
        sys.modules.pop(module_name, None)
    try:
        with pytest.raises(RuntimeError, match="ps_import_python: module exploded") as error:
            parse_source(f'($import "{script}")', str(tmp_path / "main.yu-c"))

        if has_previous:
            assert sys.modules[module_name] is previous
        else:
            assert module_name not in sys.modules
        assert "published_before_failure" not in yugen.builtin
        assert yugen.yushell.script == []
        frames = traceback.extract_tb(error.value.__traceback__)
        assert any(
            frame.filename == str(script) and frame.name == "explode"
            for frame in frames
        )

        script.write_text("retry_value = 73\n", encoding="utf8")
        parse_source(f'($import "{script}")', str(tmp_path / "retry.yu-c"))

        assert sys.modules[module_name].retry_value == 73
        assert yugen.builtin["retry_value"] == 73
        assert yugen.yushell.script == [str(script)]
    finally:
        sys.modules.pop(module_name, None)


def test_unknown_python_import_keeps_type_and_source_location(tmp_path):
    missing = tmp_path / "not-there.py"

    with pytest.raises(FileNotFoundError) as error:
        parse_source(f'($import "{missing}")', str(tmp_path / "main.yu-c"))

    assert str(error.value).startswith("ps_import_python:")
    assert "not-there.py" in str(error.value)
