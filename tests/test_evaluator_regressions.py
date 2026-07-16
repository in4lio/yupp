import os
import subprocess
import sys
import textwrap

import pytest

from tests.conftest import REPO_ROOT
from yupp.pp import yugen


def _preprocess(tmp_path, name, source, timeout=2):
    input_path = tmp_path / name
    input_path.write_text(textwrap.dedent(source).lstrip(), encoding="utf8")
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPO_ROOT / "src")
    environment["PYTHON_COLORS"] = "0"

    try:
        process = subprocess.run(
            [
                sys.executable,
                "-S",
                "-m",
                "yupp",
                "-q",
                "--no-read-only",
                str(input_path),
            ],
            cwd=tmp_path,
            env=environment,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        pytest.fail(
            f"yupp did not terminate within {timeout} seconds for {name}",
            pytrace=False,
        )

    assert process.returncode == 0, process.stdout + process.stderr
    output_path = input_path.with_name(input_path.name.replace(".yu-", ".", 1))
    return output_path.read_text(encoding="utf8")


def _without_whitespace(value):
    return "".join(value.split())


@pytest.mark.integration
def test_false_row_condition_skips_non_character_range_value(tmp_path):
    output = _preprocess(
        tmp_path,
        "conditional-row.yu-txt",
        r"""
        ($import stdlib)
        ($set IDS (input output (`) mux))
        ($set VALUES ('1' 'A' 254 '2'))
        ($($range ($len IDS)) \i.]
            ($set VALUE ($i VALUES))
            ($if ($i IDS) ]
                ($ord ($unq VALUE))|
            [ )
        [ )
        """,
    )

    assert _without_whitespace(output) == "49|65|50|"


@pytest.mark.integration
def test_finite_recursive_tree_walk_with_local_set_terminates(tmp_path):
    output = _preprocess(
        tmp_path,
        "recursive-walk.yu-txt",
        r"""
        ($import stdlib)
        ($set PARENTS ("" "" "in" "in" "i2c" "i2c" "i2c"))
        ($set NAMES ("in" "out" "i2c" "wedo" "mux" "servo" "motor"))
        ($set walk \parent.\indent.($($range ($len PARENTS)) \i.]
            ($if ($eq parent ($i PARENTS)) ]
                ($set INDENT_COPY indent)
                ($unq ($i NAMES)):($unq INDENT_COPY)|
                ($walk ($i NAMES) ($inc indent))
            [ )
        [ ))
        ($walk "" 0)
        """,
    )

    assert _without_whitespace(output) == (
        "in:0|i2c:1|mux:2|servo:2|motor:2|wedo:1|out:0|"
    )


@pytest.mark.integration
def test_deferred_conditional_eval_uses_original_call_site(tmp_path):
    output = _preprocess(
        tmp_path,
        "deferred-eval-caller.yu-txt",
        r"""
        ($import stdlib)
        ($set CLASS_TYPE_MODES ("first" "second"))
        ($set attr mode)
        ($set i 0)
        ($if 1 ]
            ($unq ($i ($$'CLASS_TYPE_($0)S' ($upper attr))))
        [ )
        """,
    )

    assert _without_whitespace(output) == "first"


@pytest.mark.integration
def test_deferred_conditional_named_branches_skip_unselected_error(tmp_path):
    output = _preprocess(
        tmp_path,
        "deferred-named-branches.yu-txt",
        r"""
        ($import stdlib)
        ($if 1 \then 7 \else ($div 1 0))
        """,
    )

    assert _without_whitespace(output) == "7"


def test_deferred_conditional_resumes_with_original_call_site():
    condition = yugen.ATOM("condition")
    selected = yugen.ATOM("selected")
    rejected = yugen.ATOM("rejected")
    gate = yugen.ATOM("gate")
    value = yugen.ATOM("value")
    closure = yugen.yueval(
        yugen.LAMBDA(
            [
                ([], condition, None),
                ([], selected, None),
                ([], rejected, None),
            ],
            yugen.APPLY(
                yugen.COND(
                    yugen.VAR([], condition),
                    yugen.VAR([], selected),
                    yugen.VAR([], rejected),
                ),
                [],
                [],
            ),
        ),
        yugen.ENV(),
    )
    original_caller = yugen.ENV(None, [(value, yugen.INT(1))])
    checkpoint = yugen.yueval(
        yugen.APPLY(
            closure,
            [
                yugen.VAR(yugen.LATE_BOUND(), gate),
                yugen.VAR([], value),
                yugen.APPLY(
                    yugen.VAR([], yugen.ATOM("div")),
                    [yugen.INT(1), yugen.INT(0)],
                    [],
                ),
            ],
            [],
        ),
        original_caller,
    )

    assert isinstance(checkpoint, yugen.APPLY)

    resume_caller = yugen.ENV(
        None,
        [(gate, yugen.INT(1)), (value, yugen.INT(2))],
    )

    assert yugen.yueval(checkpoint, resume_caller) == 1


@pytest.mark.integration
def test_plain_text_accepts_unicode_codepoints(tmp_path):
    output = _preprocess(
        tmp_path,
        "unicode-plain.yu-txt",
        "Привет – café\n",
    )

    assert output == "Привет – café\n"
