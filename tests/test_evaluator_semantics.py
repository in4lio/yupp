import pytest

from tests.conftest import capture_evaluator_logs, parse_source
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


def test_unresolved_conditional_keeps_both_branches_untouched_until_selection():
    condition = yugen.ATOM("condition")
    items_name = yugen.ATOM("items")
    items = yugen.LIST([yugen.INT(1), yugen.INT(2)])
    env = yugen.ENV(None, [(items_name, items)])
    env.predeclare(condition)
    source = yugen.COND(
        yugen.VAR([], condition),
        yugen.EMIT(yugen.VAR([], items_name), None),
        _apply(_var("div"), yugen.INT(1), yugen.INT(0)),
    )

    residual = yugen.yueval(source, env)
    still_residual = yugen.yueval(residual, yugen.ENV())

    assert isinstance(still_residual, yugen.COND_CLOSURE)
    assert isinstance(still_residual.leg_1, yugen.EMIT)
    assert isinstance(still_residual.leg_0, yugen.APPLY)
    assert items == yugen.LIST([yugen.INT(1), yugen.INT(2)])

    env.publish(condition, yugen.INT(1))
    assert yugen.yueval(still_residual, yugen.ENV()) == 1
    assert items == yugen.LIST([yugen.INT(1), yugen.INT(2)])


def test_residual_keeps_regular_invocation_locals_after_lambda_returns():
    condition = yugen.ATOM("condition")
    definition = yugen.ENV()
    definition.predeclare(condition)
    closure = yugen.yueval(
        _lambda(
            ["value"],
            yugen.COND(yugen.VAR([], condition), _var("value"), yugen.INT(0)),
        ),
        definition,
    )

    residual = yugen.yueval(_apply(closure, yugen.INT(7)), yugen.ENV())
    definition.publish(condition, yugen.INT(1))

    assert isinstance(residual, yugen.COND_CLOSURE)
    assert yugen.yueval(residual, yugen.ENV()) == 7


def test_residual_chain_commits_effects_once_and_checkpoint_forks_are_independent():
    items_name = yugen.ATOM("items")
    gate_1 = yugen.ATOM("gate_1")
    gate_2 = yugen.ATOM("gate_2")
    items = yugen.LIST([yugen.INT(1), yugen.INT(2), yugen.INT(3)])
    env = yugen.ENV(None, [(items_name, items)])
    env.predeclare(gate_1)
    env.predeclare(gate_2)
    source = _apply(
        _var("list"),
        yugen.EMIT(yugen.VAR([], items_name), None),
        yugen.VAR([], gate_1),
        yugen.EMIT(yugen.VAR([], items_name), None),
        yugen.VAR([], gate_2),
        yugen.EMIT(yugen.VAR([], items_name), None),
    )
    before = repr(source)

    first = yugen.yueval(source, env)
    assert items == yugen.LIST([yugen.INT(2), yugen.INT(3)])
    env.publish(gate_1, yugen.INT(10))
    second = yugen.yueval(first, yugen.ENV())
    assert isinstance(second, yugen.APPLY)
    env.publish(gate_2, yugen.INT(20))

    assert yugen.yueval(second, yugen.ENV()) == yugen.LIST([1, 10, 2, 20, 3])
    assert yugen.yueval(first, yugen.ENV()) == yugen.LIST([1, 10, 2, 20, 3])
    assert yugen.yueval(first, yugen.ENV()) == yugen.LIST([1, 10, 2, 20, 3])
    assert items == yugen.LIST([yugen.INT(2), yugen.INT(3)])
    assert repr(source) == before


def test_late_reference_uses_application_caller_while_regular_name_stays_lexical():
    regular = yugen.ATOM("regular")
    dynamic = yugen.ATOM("dynamic")
    definition = yugen.ENV(None, [(regular, yugen.INT(1)), (dynamic, yugen.INT(10))])
    caller = yugen.ENV(None, [(regular, yugen.INT(2)), (dynamic, yugen.INT(3))])
    closure = yugen.yueval(
        _lambda(
            ["ignored"],
            yugen.LIST([yugen.VAR([], regular), yugen.VAR(yugen.LATE_BOUND(), dynamic)]),
        ),
        definition,
    )

    assert yugen.yueval(_apply(closure, yugen.INT(0)), caller) == yugen.LIST([1, 3])


def test_partial_application_uses_only_completing_caller_for_new_late_demand():
    dynamic = yugen.ATOM("dynamic")
    closure = yugen.yueval(
        _lambda(["first", "second"], yugen.VAR(yugen.LATE_BOUND(), dynamic)),
        yugen.ENV(None, [(dynamic, yugen.INT(0))]),
    )
    first_caller = yugen.ENV(None, [(dynamic, yugen.INT(1))])
    completing_caller = yugen.ENV(None, [(dynamic, yugen.INT(2))])

    partial = yugen.yueval(_apply(closure, yugen.INT(10)), first_caller)

    assert yugen.yueval(_apply(partial, yugen.INT(20)), completing_caller) == 2


def test_resumed_branch_keeps_regular_lexical_value_and_uses_resumption_caller_for_late_name():
    condition = yugen.ATOM("condition")
    regular = yugen.ATOM("regular")
    dynamic = yugen.ATOM("dynamic")
    definition = yugen.ENV(None, [(regular, yugen.INT(1)), (dynamic, yugen.INT(10))])
    definition.predeclare(condition)
    closure = yugen.yueval(
        _lambda(
            [],
            yugen.COND(
                yugen.VAR([], condition),
                yugen.LIST([yugen.VAR([], regular), yugen.VAR(yugen.LATE_BOUND(), dynamic)]),
                yugen.INT(0),
            ),
        ),
        definition,
    )
    residual = yugen.yueval(_apply(closure), yugen.ENV())
    definition.publish(condition, yugen.INT(1))
    resume_caller = yugen.ENV(None, [(regular, yugen.INT(99)), (dynamic, yugen.INT(7))])

    assert yugen.yueval(residual, resume_caller) == yugen.LIST([1, 7])


def test_eval_started_before_suspension_retains_caller_but_new_eval_uses_resume_caller():
    gate = yugen.ATOM("gate")
    value = yugen.ATOM("value")
    original = yugen.ENV(None, [(value, yugen.INT(1))])
    original.predeclare(gate)
    started = parse_source("($$ gate)").ast[0]
    in_progress = yugen.yueval(started, original)
    original.publish(gate, yugen.STR("($list value)"))
    resume = yugen.ENV(None, [(value, yugen.INT(2))])

    assert yugen.yueval(in_progress, resume) == yugen.LIST([1])

    gate_2 = yugen.ATOM("gate_2")
    lexical = yugen.ENV(None, [(value, yugen.INT(1))])
    lexical.predeclare(gate_2)
    deferred = yugen.COND(
        yugen.VAR([], gate_2),
        parse_source('($$ "($list value)")').ast[0],
        yugen.INT(0),
    )
    checkpoint = yugen.yueval(deferred, lexical)
    lexical.publish(gate_2, yugen.INT(1))

    assert yugen.yueval(checkpoint, resume) == yugen.LIST([2])


def test_macro_started_before_suspension_retains_caller_but_new_macro_uses_resume_caller():
    parse_source("macro context")
    macro_name = yugen.ATOM("context_macro")
    parameter = yugen.ATOM("parameter")
    macro_env = yugen.yueval(
        yugen.MACRO(macro_name, [parameter], "($list ($parameter) value)"),
        yugen.ENV(),
    )
    gate = yugen.ATOM("gate")
    value = yugen.ATOM("value")
    original = yugen.ENV(macro_env, [(value, yugen.INT(1))])
    original.predeclare(gate)
    in_progress = yugen.yueval(
        _apply(yugen.VAR([], macro_name), yugen.VAR([], gate)), original
    )
    original.publish(gate, yugen.INT(7))
    resume = yugen.ENV(None, [(value, yugen.INT(2))])

    assert yugen.yueval(in_progress, resume) == yugen.LIST([7, 1])

    gate_2 = yugen.ATOM("gate_2")
    lexical = yugen.ENV(macro_env, [(value, yugen.INT(1))])
    lexical.predeclare(gate_2)
    checkpoint = yugen.yueval(
        yugen.COND(
            yugen.VAR([], gate_2),
            _apply(yugen.VAR([], macro_name), yugen.INT(8)),
            yugen.INT(0),
        ),
        lexical,
    )
    lexical.publish(gate_2, yugen.INT(1))

    assert yugen.yueval(checkpoint, resume) == yugen.LIST([8, 2])


def test_macro_and_eval_use_the_enclosing_lambda_invocation_frame():
    parse_source("dynamic operation context")
    value = yugen.ATOM("value")
    macro_name = yugen.ATOM("read_value")
    macro_env = yugen.yueval(
        yugen.MACRO(macro_name, [], "($list value)"),
        yugen.ENV(),
    )
    definition = yugen.ENV(macro_env, [(value, yugen.INT(1))])
    macro_closure = yugen.yueval(
        _lambda(["value"], _apply(yugen.VAR([], macro_name))),
        definition,
    )
    eval_closure = yugen.yueval(
        _lambda(["value"], parse_source('($$ "($list value)")').ast[0]),
        definition,
    )

    assert yugen.yueval(_apply(macro_closure, yugen.INT(2)), yugen.ENV()) == yugen.LIST([2])
    assert yugen.yueval(_apply(eval_closure, yugen.INT(3)), yugen.ENV()) == yugen.LIST([3])


def test_eval_reached_inside_resumed_eval_uses_resumption_caller():
    gate = yugen.ATOM("gate")
    value = yugen.ATOM("value")
    original = yugen.ENV(None, [(value, yugen.INT(1))])
    original.predeclare(gate)
    in_progress = yugen.yueval(parse_source("($$ gate)").ast[0], original)
    original.publish(gate, yugen.STR('($$ "($list value)")'))
    resume = yugen.ENV(None, [(value, yugen.INT(2))])

    assert yugen.yueval(in_progress, resume) == yugen.LIST([2])


def test_macro_reached_inside_resumed_eval_uses_resumption_caller():
    gate = yugen.ATOM("gate")
    value = yugen.ATOM("value")
    macro_name = yugen.ATOM("nested_context")
    parameter = yugen.ATOM("parameter")
    macro_env = yugen.yueval(
        yugen.MACRO(macro_name, [parameter], "($list ($parameter) value)"),
        yugen.ENV(),
    )
    original = yugen.ENV(macro_env, [(value, yugen.INT(1))])
    original.predeclare(gate)
    in_progress = yugen.yueval(parse_source("($$ gate)").ast[0], original)
    original.publish(gate, yugen.STR("($nested_context 9)"))
    resume = yugen.ENV(macro_env, [(value, yugen.INT(2))])

    assert yugen.yueval(in_progress, resume) == yugen.LIST([9, 2])


def _caller_only_lambda(filename="migration.yu", application_body=False):
    parsed = parse_source("($ \\ignored.($caller_only) 0)", filename).ast[0].fn
    body = parsed.l_form if application_body else parsed.l_form.fn
    return yugen.LAMBDA(parsed.bound, body)


def _migration_warnings(records):
    return [
        message
        for name, level, message in records
        if name == "log" and level == "WARNING" and "dynamic scope" in message
    ]


def test_dynamic_scope_migration_warning_is_opt_in_and_never_substitutes_caller_value():
    caller_only = yugen.ATOM("caller_only")
    caller = yugen.ENV(None, [(caller_only, yugen.INT(7))])

    yugen.config.warn_dynamic_scope = False
    disabled = yugen.yueval(_caller_only_lambda(), yugen.ENV())
    with capture_evaluator_logs() as disabled_records:
        disabled_result = yugen.yueval(_apply(disabled, yugen.INT(0)), caller)

    yugen.config.warn_dynamic_scope = True
    enabled = yugen.yueval(_caller_only_lambda(), yugen.ENV())
    with capture_evaluator_logs() as enabled_records:
        enabled_result = yugen.yueval(_apply(enabled, yugen.INT(0)), caller)

    assert disabled_result == enabled_result == caller_only
    assert _migration_warnings(disabled_records) == []
    assert len(_migration_warnings(enabled_records)) == 1
    warning = _migration_warnings(enabled_records)[0]
    assert "executed path" in warning
    assert "explicit argument" in warning
    assert "late binding" in warning
    assert 'File "migration.yu", line 1' in warning


def test_dynamic_scope_migration_warning_is_once_per_site_per_evaluation():
    yugen.config.warn_dynamic_scope = True
    caller_only = yugen.ATOM("caller_only")
    caller = yugen.ENV(None, [(caller_only, yugen.INT(7))])
    closure = yugen.yueval(_caller_only_lambda(), yugen.ENV())

    with capture_evaluator_logs() as one_evaluation:
        result = yugen.yueval(
            yugen.LIST([
                _apply(closure, yugen.INT(0)),
                _apply(closure, yugen.INT(1)),
            ]),
            caller,
        )
    with capture_evaluator_logs() as separate_evaluations:
        yugen.yueval(_apply(closure, yugen.INT(2)), caller)
        yugen.yueval(_apply(closure, yugen.INT(3)), caller)

    assert result == yugen.LIST([caller_only, caller_only])
    assert len(_migration_warnings(one_evaluation)) == 1
    assert len(_migration_warnings(separate_evaluations)) == 2


def test_dynamic_scope_migration_warning_reports_distinct_source_sites():
    yugen.config.warn_dynamic_scope = True
    parsed = parse_source(
        "($ \\ignored.($caller_only) 0)($ \\ignored.($caller_only) 0)",
        "migration-sites.yu",
    )
    closures = []
    for application in parsed.ast:
        source_lambda = application.fn
        closures.append(
            yugen.yueval(
                yugen.LAMBDA(source_lambda.bound, source_lambda.l_form.fn),
                yugen.ENV(),
            )
        )
    caller_only = yugen.ATOM("caller_only")
    caller = yugen.ENV(None, [(caller_only, yugen.INT(7))])

    with capture_evaluator_logs() as records:
        result = yugen.yueval(
            yugen.LIST([_apply(closure, yugen.INT(0)) for closure in closures]),
            caller,
        )

    assert result == yugen.LIST([caller_only, caller_only])
    assert len(_migration_warnings(records)) == 2


def test_dynamic_scope_migration_warning_survives_residual_and_is_shared_by_forks():
    yugen.config.warn_dynamic_scope = True
    caller_only = yugen.ATOM("caller_only")
    gate = yugen.ATOM("gate")
    definition = yugen.ENV()
    definition.predeclare(gate)
    parsed = _caller_only_lambda("migration-residual.yu")
    closure = yugen.yueval(
        yugen.LAMBDA(
            parsed.bound,
            yugen.COND(yugen.VAR([], gate), parsed.l_form, yugen.INT(0)),
        ),
        definition,
    )
    caller = yugen.ENV(None, [(caller_only, yugen.INT(7))])
    residual = yugen.yueval(_apply(closure, yugen.INT(0)), caller)
    definition.publish(gate, yugen.INT(1))

    with capture_evaluator_logs() as records:
        first = yugen.yueval(residual, caller)
        second = yugen.yueval(residual, caller)

    assert first == second == caller_only
    assert len(_migration_warnings(records)) == 1


def test_explicit_late_binding_does_not_emit_a_migration_warning():
    yugen.config.warn_dynamic_scope = True
    caller_only = yugen.ATOM("caller_only")
    closure = yugen.yueval(
        _lambda(["ignored"], yugen.VAR(yugen.LATE_BOUND(), caller_only)),
        yugen.ENV(),
    )

    with capture_evaluator_logs() as records:
        result = yugen.yueval(
            _apply(closure, yugen.INT(0)),
            yugen.ENV(None, [(caller_only, yugen.INT(7))]),
        )

    assert result == 7
    assert _migration_warnings(records) == []


def test_dynamic_scope_and_unbound_application_warnings_remain_independent():
    yugen.config.warn_dynamic_scope = True
    yugen.config.warn_unbound_application = True
    caller_only = yugen.ATOM("caller_only")
    closure = yugen.yueval(
        _caller_only_lambda("migration-unbound.yu", application_body=True),
        yugen.ENV(),
    )

    with capture_evaluator_logs() as records:
        result = yugen.yueval(
            _apply(closure, yugen.INT(0)),
            yugen.ENV(None, [(caller_only, yugen.INT(7))]),
        )

    warnings = [message for name, level, message in records if name == "log" and level == "WARNING"]
    assert result == caller_only
    assert len(_migration_warnings(records)) == 1
    assert any('application of unbound atom "caller_only"' in message for message in warnings)


@pytest.mark.parametrize(
    "kind,source,filename,provenance",
    [
        (
            "macro",
            "($macro maker () ($set generated \\ignored.($caller_only))0)($maker)",
            "migration-macro.yu",
            'Macro "maker", line 1',
        ),
        (
            "eval",
            '($$ "($set generated \\\\ignored.($caller_only))0")',
            "migration-eval.yu",
            'Macro "<string>", line 1',
        ),
    ],
)
def test_dynamic_scope_migration_warning_keeps_macro_and_eval_provenance(
    kind, source, filename, provenance
):
    yugen.config.warn_dynamic_scope = True
    ast = parse_source(source, filename)
    env = yugen.ENV()
    if kind == "macro":
        env = yugen.yueval(ast.ast[0], env)
        embedded = yugen.yueval(ast.ast[1], env)
    else:
        embedded = yugen.yueval(ast.ast[0], env)
    assignment = next(node for node in embedded.ast if isinstance(node, yugen.SET))
    parsed_lambda = assignment.ast
    closure = yugen.yueval(
        yugen.LAMBDA(parsed_lambda.bound, parsed_lambda.l_form.fn),
        yugen.ENV(),
    )
    caller_only = yugen.ATOM("caller_only")

    with capture_evaluator_logs() as records:
        result = yugen.yueval(
            _apply(closure, yugen.INT(0)),
            yugen.ENV(None, [(caller_only, yugen.INT(7))]),
        )

    assert result == caller_only
    warning = _migration_warnings(records)
    assert len(warning) == 1
    assert f'File "{filename}", line 1' in warning[0]
    assert provenance in warning[0]
