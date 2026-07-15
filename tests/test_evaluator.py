import hashlib

import pytest

from yupp.pp import yugen
from tests.conftest import parse_source
from tests.fixtures.legacy_cases import EVALUATOR_AST_SHA256, EVALUATOR_CASES


def test_legacy_evaluator_records_exclude_only_the_empty_sentinel():
    from tests.fixtures.legacy_harness import t_eval_kit

    assert len(EVALUATOR_CASES) == 13
    assert all(actual is original for actual, original in zip(EVALUATOR_CASES, t_eval_kit))
    assert not t_eval_kit[-1][1].strip()


@pytest.mark.parametrize(
    "trace_stage,source,expected_ast,expected,ast_sha256",
    [record + (digest,) for record, digest in zip(EVALUATOR_CASES, EVALUATOR_AST_SHA256)],
    ids=[f"legacy-evaluator-{index:02d}" for index in range(1, 14)],
)
def test_legacy_evaluator_result_is_exact(trace_stage, source, expected_ast, expected, ast_sha256):
    yugen.trace.stage = trace_stage
    ast = parse_source(source)

    assert ast == expected_ast
    assert hashlib.sha256(repr(ast).encode()).hexdigest() == ast_sha256

    actual = yugen.yueval(ast, yugen.ENV())
    if isinstance(actual, str):
        actual = yugen.replace_steady(yugen.reduce_emptiness(actual))
    assert actual == expected


@pytest.mark.parametrize(
    "source,error_type,message",
    [
        ("($unknown 1)", TypeError, "yueval: no arguments of unbound atom expected"),
        ("($div 1 0)", ZeroDivisionError, "yueval: python: division by zero"),
    ],
)
def test_evaluator_errors_keep_type_and_diagnostic_prefix(source, error_type, message):
    ast = parse_source(source)
    with pytest.raises(error_type) as error:
        yugen.yueval(ast, yugen.ENV())

    assert str(error.value).startswith(message)
    assert 'File "<stdin>", line 1' in str(error.value)


def test_evaluator_reuses_explicit_environment_ast_without_mutation():
    ast = parse_source("($add 1 2)")
    before = repr(ast)

    assert yugen.yueval(ast, yugen.ENV()) == "3"
    assert yugen.yueval(ast, yugen.ENV()) == "3"
    assert repr(ast) == before


def test_atol_has_integer_contract():
    assert yugen.builtin["atol"]("10") == 10


def test_maketrans_is_available_to_the_dsl():
    assert yugen.builtin["maketrans"]("a", "x") == str.maketrans("a", "x")


def test_translate_accepts_a_python3_translation_table():
    table = str.maketrans("a", "x")
    assert yugen.builtin["translate"]("abc", table) == "xbc"


@pytest.mark.parametrize(
    "literal,expected",
    [
        ("é\\n", "é\n"),
        ("😀\\t", "😀\t"),
        ("'é😀\\n'", "é😀\n"),
    ],
)
def test_unq_preserves_unicode_while_decoding_escapes(literal, expected):
    assert yugen.builtin["unq"](literal) == expected


def test_translate_supports_legacy_dsl_deletions_and_none_table():
    table = str.maketrans("a", "x")

    assert yugen.builtin["translate"]("abc", table, "b") == "xc"
    assert yugen.builtin["translate"]("abc", None, "b") == "ac"


def test_translate_supports_a_legacy_256_character_table():
    table = "".join(chr(index) for index in range(256))
    table = table[: ord("a")] + "x" + table[ord("a") + 1 :]

    assert yugen.builtin["translate"]("abcé😀", table, "b") == "xcé😀"


def test_unq_keeps_source_location_on_string_subclasses():
    literal = yugen.STR("é\\n", "sample.yu", 7)

    actual = yugen.builtin["unq"](literal)

    assert actual == "é\n"
    assert isinstance(actual, yugen.STR)
    assert actual.input_file == "sample.yu"
    assert actual.pos == 7
