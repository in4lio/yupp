import copy

import pytest

from tests.conftest import (
    capture_evaluator_logs,
    evaluate_ast,
    evaluate_source,
    normalize_evaluator_value,
    parse_source,
)
from yupp.pp import yugen


def test_reusable_and_partial_closures_keep_independent_arguments():
    source = (
        "($set add3 \\a.\\b.\\c.($add ($add a b) c))"
        "($set add10 ($add3 10))"
        "($list ($add10 1 2) ($add10 3 4))"
    )

    _, value = evaluate_source(source)

    assert value == "1317\n"


def test_default_is_evaluated_at_definition_time_before_shadowing():
    _, value = evaluate_source("($set x 1)($set f \\a:x.($a))($set x 2)($f)")

    assert value == "1\n"


@pytest.mark.parametrize(
    "surface,source,expected",
    [
        ("computed-callee", "($add ? 0 | sub 10 ? 1 | 5 0 ? 0 | 3)", "7"),
        ("macro", "($macro double (n) ($mul ($n) 2))($double 4)", "8"),
        ("eval", '($$ "($add 3 4)")', "7"),
        ("list-application", "($(1 2 3) \\x.($mul x 2))", "246"),
        ("numeric-subscript", "($1 (10 20 30))", "20"),
        ("variadic", "($ \\a.\\...($list a *__va_args__) 1 2 3)", "123"),
        ("named-default", "($ \\a:1.\\b:2.($add a b) \\b 5)", "6"),
        (
            "late-binding",
            "($set k 10)"
            "($set app \\p1..\\p2..\\f.\\i.($f k i))"
            "($set l 3)"
            "($list ($app \\f ($mul &p1 &p2) 2)"
            " ($app \\f ($mul &p1 &p2) l))",
            "2030",
        ),
    ],
)
def test_preserved_dynamic_and_application_surfaces(surface, source, expected):
    del surface

    _, value = evaluate_source(source)

    assert value == expected + "\n"


def test_list_lookup_copies_value_while_emit_consumes_bound_list():
    name = yugen.ATOM("items")
    items = yugen.LIST([yugen.INT(1), yugen.INT(2)])
    env = yugen.ENV(None, [(name, items)])

    looked_up = yugen.yueval(yugen.VAR([], name), env)
    emitted = yugen.yueval(yugen.EMIT(yugen.VAR([], name), None), env)

    assert looked_up == yugen.LIST([yugen.INT(1), yugen.INT(2)])
    assert looked_up is not items
    assert emitted == 1
    assert items == yugen.LIST([yugen.INT(2)])


def test_emit_source_observation_is_ordered_and_exhausts_list():
    _, value = evaluate_source(
        "($set l (1 2 3))($emit l),($emit l),($emit l),($emit l)"
    )

    assert value == "1,2,3,\n"


def test_non_recursive_closure_repr_equality_and_copy_contract():
    atom = yugen.ATOM("x")
    closure = yugen.yueval(
        yugen.LAMBDA([([], atom, None)], yugen.VAR([], atom)),
        yugen.ENV(),
    )
    clone = copy.deepcopy(closure)

    assert repr(closure) == (
        "L_CLOSURE(VAR([], ATOM('x')), "
        "ENV({ATOM('x'): BOUND()}, ENV({}, None)), {}, {})"
    )
    assert clone == closure
    assert clone is not closure


def test_trace_records_inputs_environments_and_outputs():
    ast = parse_source("($add 1 2)")
    yugen.trace.stage = yugen.TRACE_STAGE_EVAL
    yugen.trace.set_current(yugen.TRACE_STAGE_EVAL)

    with capture_evaluator_logs() as records:
        result = evaluate_ast(ast)

    trace_messages = [message for name, _, message in records if name == "trace"]
    assert result.value == "3\n"
    assert any("<-- TEXT([APPLY(VAR([], ATOM('add'))" in message for message in trace_messages)
    assert any(message.startswith("ENV(") for message in trace_messages)
    assert any(message.endswith("--> 3") for message in trace_messages)


def test_source_error_keeps_filename_line_and_diagnostic_prefix():
    ast = parse_source("($div 1 0)", "characterization.yu")

    with pytest.raises(ZeroDivisionError) as error:
        yugen.yueval(ast, yugen.ENV())

    message = str(error.value)
    assert message.startswith("yueval: python: division by zero")
    assert 'File "characterization.yu", line 1' in message


def test_repeated_omitted_environment_calls_leave_ast_unchanged():
    ast = parse_source("($add 1 2)")
    before = repr(ast)

    first = normalize_evaluator_value(yugen.yueval(ast))
    second = normalize_evaluator_value(yugen.yueval(ast))

    assert first == second == "3\n"
    assert repr(ast) == before


def test_deferred_regular_reference_stays_in_lexical_closure_u2():
    name_x = yugen.ATOM("x")
    name_condition = yugen.ATOM("condition")
    definition_env = yugen.ENV(None, [(name_x, yugen.INT(1))])
    deferred = yugen.yueval(
        yugen.LAMBDA(
            [],
            yugen.COND(
                yugen.VAR(yugen.LATE_BOUND(), name_condition),
                yugen.VAR([], name_x),
                yugen.INT(0),
            ),
        ),
        definition_env,
    )
    caller_env = yugen.ENV(
        None,
        [(name_x, yugen.INT(2)), (name_condition, yugen.INT(1))],
    )

    result = yugen.yueval(yugen.APPLY(deferred, [], []), caller_env)

    assert isinstance(deferred, yugen.L_CLOSURE)
    assert deferred.env.parent is definition_env
    assert isinstance(result, yugen.COND_CLOSURE)


def test_unresolved_conditional_does_not_speculatively_commit_emit():
    name_items = yugen.ATOM("items")
    items = yugen.LIST([yugen.INT(1), yugen.INT(2)])
    env = yugen.ENV(None, [(name_items, items)])
    residual = yugen.COND_CLOSURE(
        yugen.VAR(yugen.LATE_BOUND(), yugen.ATOM("condition")),
        yugen.EMIT(yugen.VAR([], name_items), None),
        yugen.INT(0),
    )

    result = yugen.yueval(residual, env)

    assert isinstance(result, yugen.COND_CLOSURE)
    assert isinstance(result.leg_1, yugen.EMIT)
    assert items == yugen.LIST([yugen.INT(1), yugen.INT(2)])
