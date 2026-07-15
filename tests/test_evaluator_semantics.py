import pytest

from tests.conftest import capture_evaluator_logs
from yupp.pp import yugen


def _var(name):
    return yugen.VAR([], yugen.ATOM(name))


def _apply(function, *arguments):
    return yugen.APPLY(function, list(arguments), [])


def _lambda(parameters, body):
    return yugen.LAMBDA(
        [([], yugen.ATOM(parameter), None) for parameter in parameters],
        body,
    )


def test_repeated_full_and_partial_closure_calls_are_independent():
    identity = yugen.yueval(_lambda(["value"], _var("value")), yugen.ENV())
    identity_before = repr(identity)

    assert yugen.yueval(_apply(identity, yugen.INT(1)), yugen.ENV()) == 1
    assert yugen.yueval(_apply(identity, yugen.INT(2)), yugen.ENV()) == 2
    assert repr(identity) == identity_before

    add = _var("add")
    add3 = yugen.yueval(
        _lambda(
            ["a", "b", "c"],
            _apply(add, _apply(add, _var("a"), _var("b")), _var("c")),
        ),
        yugen.ENV(),
    )
    partial = yugen.yueval(_apply(add3, yugen.INT(10)), yugen.ENV())
    partial_before = repr(partial)

    assert yugen.yueval(_apply(partial, yugen.INT(1), yugen.INT(2)), yugen.ENV()) == 13
    assert yugen.yueval(_apply(partial, yugen.INT(3), yugen.INT(4)), yugen.ENV()) == 17
    assert repr(partial) == partial_before


def test_regular_reference_uses_definition_environment_not_caller_shadow():
    name = yugen.ATOM("captured")
    definition = yugen.ENV(None, [(name, yugen.INT(1))])
    caller = yugen.ENV(None, [(name, yugen.INT(2))])
    closure = yugen.yueval(
        _lambda(["ignored"], _apply(_var("add"), _var("captured"), _var("ignored"))),
        definition,
    )

    assert yugen.yueval(_apply(closure, yugen.INT(0)), caller) == 1
    assert closure.env.parent is definition


def test_self_and_mutual_recursive_binding_groups_share_one_frame():
    factorial = _lambda(
        ["n"],
        yugen.COND(
            _var("n"),
            _apply(
                _var("mul"),
                _var("n"),
                _apply(_var("factorial"), _apply(_var("sub"), _var("n"), yugen.INT(1))),
            ),
            yugen.INT(1),
        ),
    )
    factorial_env = yugen.yueval(yugen.SET(yugen.ATOM("factorial"), factorial), yugen.ENV())

    assert yugen.yueval(_apply(_var("factorial"), yugen.INT(6)), factorial_env) == 720

    even = _lambda(
        ["n"],
        yugen.COND(
            _var("n"),
            _apply(_var("odd"), _apply(_var("sub"), _var("n"), yugen.INT(1))),
            yugen.INT(1),
        ),
    )
    odd = _lambda(
        ["n"],
        yugen.COND(
            _var("n"),
            _apply(_var("even"), _apply(_var("sub"), _var("n"), yugen.INT(1))),
            yugen.INT(0),
        ),
    )
    parity_env = yugen.yueval(
        yugen.SET([yugen.ATOM("even"), yugen.ATOM("odd")], yugen.LIST([even, odd])),
        yugen.ENV(),
    )

    assert yugen.yueval(_apply(_var("even"), yugen.INT(8)), parity_env) == 1
    assert yugen.yueval(_apply(_var("odd"), yugen.INT(7)), parity_env) == 1


def test_let_destructuring_publishes_dependencies_and_mutual_closures():
    name_a = yugen.ATOM("a")
    name_b = yugen.ATOM("b")
    dependent = yugen.LET(
        [name_a, name_b],
        yugen.LIST(
            [
                yugen.INT(5),
                _apply(_var("add"), _var("a"), yugen.INT(1)),
            ]
        ),
        _apply(_var("add"), _var("a"), _var("b")),
    )

    assert yugen.yueval(dependent, yugen.ENV()) == 11

    even = _lambda(
        ["n"],
        yugen.COND(
            _var("n"),
            _apply(_var("odd"), _apply(_var("sub"), _var("n"), yugen.INT(1))),
            yugen.INT(1),
        ),
    )
    odd = _lambda(
        ["n"],
        yugen.COND(
            _var("n"),
            _apply(_var("even"), _apply(_var("sub"), _var("n"), yugen.INT(1))),
            yugen.INT(0),
        ),
    )
    parity = yugen.LET(
        [yugen.ATOM("even"), yugen.ATOM("odd")],
        yugen.LIST([even, odd]),
        yugen.LIST(
            [
                _apply(_var("even"), yugen.INT(8)),
                _apply(_var("odd"), yugen.INT(7)),
            ]
        ),
    )

    assert yugen.yueval(parity, yugen.ENV()) == yugen.LIST([yugen.INT(1), yugen.INT(1)])


def test_uninitialized_recursive_member_stops_lookup_and_runtime_cycle_is_safe():
    name = yugen.ATOM("member")
    outer = yugen.ENV(None, [(name, yugen.INT(99))])
    group = yugen.ENV(outer)
    group.predeclare(name)

    assert isinstance(group.lookup([], name), yugen.BOUND)

    recursive = yugen.yueval(_lambda(["value"], _var("member")), group)
    group.publish(name, recursive)

    assert "L_CLOSURE" in repr(recursive)
    assert recursive == recursive
    failing = yugen.yueval(
        _lambda(
            ["value"],
            _apply(
                _var("div"),
                yugen.INT(1),
                _apply(_var("sub"), _var("value"), _var("value")),
            ),
        ),
        group,
    )
    with pytest.raises(ZeroDivisionError) as error:
        yugen.yueval(_apply(failing, yugen.INT(1)), yugen.ENV())
    assert str(error.value).startswith("yueval:")


def test_recursive_trace_and_top_level_environments_remain_isolated():
    name = yugen.ATOM("recursive")
    body = _lambda(
        ["n"],
        yugen.COND(
            _var("n"),
            _apply(_var("recursive"), _apply(_var("sub"), _var("n"), yugen.INT(1))),
            yugen.INT(0),
        ),
    )
    recursive_env = yugen.yueval(yugen.SET(name, body), yugen.ENV())
    yugen.trace.stage = yugen.TRACE_STAGE_EVAL
    yugen.trace.set_current(yugen.TRACE_STAGE_EVAL)

    with capture_evaluator_logs() as records:
        assert yugen.yueval(_apply(_var("recursive"), yugen.INT(3)), recursive_env) == 0

    messages = [message for logger, _, message in records if logger == "trace"]
    assert messages
    assert any("BINDING_CELL(<L_CLOSURE>)" in message for message in messages)

    local_name = yugen.ATOM("top_level_only")
    omitted_result = yugen.yueval(yugen.SET(local_name, yugen.INT(1)))
    explicit = yugen.ENV(None, [(local_name, yugen.INT(2))])

    assert omitted_result.lookup([], local_name) == 1
    assert yugen.yueval(_var("top_level_only")) == local_name
    assert yugen.yueval(_var("top_level_only"), explicit) == 2
    assert yugen.yueval(_var("top_level_only")) == local_name


def test_application_evaluates_callee_and_mixed_operands_in_written_order(monkeypatch):
    events = []
    target = yugen.yueval(_lambda(["a", "b", "c", "d"], yugen.LIST([
        _var("a"), _var("b"), _var("c"), _var("d"),
    ])), yugen.ENV())

    def callee():
        events.append("callee")
        return target

    def mark(value):
        events.append(str(value))
        return value

    monkeypatch.setitem(yugen.builtin, "ordered_callee", callee)
    monkeypatch.setitem(yugen.builtin, "ordered_mark", mark)
    from tests.conftest import parse_source
    ast = parse_source(
        '($($ordered_callee) ($ordered_mark "p1") '
        '\\b ($ordered_mark "n1") ($ordered_mark "p2") '
        '\\d ($ordered_mark "n2"))'
    )

    assert yugen.yueval(ast, yugen.ENV()) == '"p1""n1""p2""n2"'
    assert events == ["callee", '"p1"', '"n1"', '"p2"', '"n2"']


def test_application_stops_at_first_residual_without_touching_later_operand(monkeypatch):
    events = []

    def mark(value):
        events.append(str(value))
        return value

    def explode():
        raise AssertionError("later operand was evaluated")

    monkeypatch.setitem(yugen.builtin, "ordered_mark", mark)
    monkeypatch.setitem(yugen.builtin, "ordered_explode", explode)
    residual = yugen.APPLY(
        _var("list"),
        [
            _apply(_var("ordered_mark"), yugen.STR("first")),
            yugen.VAR(yugen.LATE_BOUND(), yugen.ATOM("missing")),
            _apply(_var("ordered_explode")),
        ],
        [],
    )

    result = yugen.yueval(residual, yugen.ENV())

    assert isinstance(result, yugen.APPLY)
    assert result.args[0] == "first"
    assert isinstance(result.args[1], yugen.VAR)
    assert isinstance(result.args[2], yugen.APPLY)
    assert events == ["first"]


def test_residual_default_is_demanded_in_definition_environment():
    captured = yugen.ATOM("captured_default")
    parameter = yugen.ATOM("value")
    definition = yugen.ENV()
    definition.predeclare(captured)
    closure = yugen.yueval(
        yugen.LAMBDA(
            [([], parameter, yugen.VAR([], captured))],
            yugen.VAR([], parameter),
        ),
        definition,
    )
    definition.publish(captured, yugen.INT(7))
    caller = yugen.ENV(None, [(captured, yugen.INT(99))])

    assert yugen.yueval(yugen.APPLY(closure, [], []), caller) == 7
