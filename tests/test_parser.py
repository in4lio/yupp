import hashlib

import pytest

from pp import yugen
from tests.conftest import parse_source
from tests.fixtures.legacy_cases import PARSER_AST_SHA256, PARSER_CASES


def test_legacy_parser_records_are_the_original_oracle():
    from test_yup import t_parse_kit

    assert len(PARSER_CASES) == 8
    assert all(actual is original for actual, original in zip(PARSER_CASES, t_parse_kit))


@pytest.mark.parametrize(
    "trace_stage,source,expected_ast,_,ast_sha256",
    [record + (digest,) for record, digest in zip(PARSER_CASES, PARSER_AST_SHA256)],
    ids=[f"legacy-parser-{index:02d}" for index in range(1, 9)],
)
def test_legacy_parser_ast_is_exact(trace_stage, source, expected_ast, _, ast_sha256):
    yugen.trace.stage = trace_stage
    actual = parse_source(source)

    assert actual == expected_ast
    assert hashlib.sha256(repr(actual).encode()).hexdigest() == ast_sha256


@pytest.mark.parametrize(
    "literal,expected",
    [("1L", 1), ("2l", 2), ("0x10L", 16)],
)
def test_legacy_integer_suffix_is_macro_syntax(literal, expected):
    ast = parse_source(f"($list {literal})")

    value = ast.ast[0].args[0]
    assert isinstance(value, yugen.INT)
    assert int(value) == expected


def test_parser_error_type_and_location_are_stable():
    with pytest.raises(SyntaxError) as error:
        parse_source("($set a")

    assert str(error.value) == (
        "ps_binding: form expected\n"
        '  File "<stdin>", line 1\n'
        "    ($set a\n"
        "           ^"
    )
