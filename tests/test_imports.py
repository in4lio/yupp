import sys

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
