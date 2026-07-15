import importlib.util
from pathlib import Path


BENCHMARK_PATH = Path(__file__).resolve().parents[1] / "script" / "benchmark_yueval.py"
SPEC = importlib.util.spec_from_file_location("benchmark_yueval", BENCHMARK_PATH)
benchmark_yueval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark_yueval)


def test_call_setup_does_not_copy_unrelated_bindings():
    few = benchmark_yueval.measure_case(4, 3, include_timing=False)
    many = benchmark_yueval.measure_case(12, 3, include_timing=False)

    assert few["env_deepcopy_calls"] == many["env_deepcopy_calls"] == 0
    assert few["env_bindings_copied"] == many["env_bindings_copied"] == 0
    assert few["call_frames_created"] == many["call_frames_created"] == 3
    assert few["closure_deepcopy_calls"] == many["closure_deepcopy_calls"] == 3
    assert few["captured_ancestor_copy_attempts"] == 0
    assert many["captured_ancestor_copy_attempts"] == 0
    assert few["captured_ancestor_bindings_enumerated"] == 0
    assert many["captured_ancestor_bindings_enumerated"] == 0
    assert few["lookup_frame_visits"] == many["lookup_frame_visits"]
    assert few["call_target_lookup_frame_visits"] == 3
    assert few["demanded_name_lookup_frame_visits"] == 3

    demanded = benchmark_yueval.measure_case(
        12, 3, include_timing=False, demand_ancestor=True
    )
    assert demanded["captured_ancestor_copy_attempts"] == 0
    assert demanded["captured_ancestor_bindings_enumerated"] == 0
    assert demanded["demanded_name_lookup_frame_visits"] == 9


def test_scaling_classifier_does_not_detect_definitions_by_calls_growth():
    measurements = [
        benchmark_yueval.measure_case(size, size, include_timing=False)
        for size in (4, 8, 16)
    ]

    assert benchmark_yueval.classify(measurements) == "not-detected"
    assert [item["env_bindings_copied"] for item in measurements] == [0, 0, 0]
    assert [item["call_frames_created"] for item in measurements] == [4, 8, 16]
    assert [item["closure_deepcopy_calls"] for item in measurements] == [4, 8, 16]
    assert [item["captured_ancestor_bindings_enumerated"] for item in measurements] == [0, 0, 0]


def test_scaling_classifier_detects_definitions_by_calls_growth():
    measurements = [
        {"calls": 4, "env_bindings_copied": 16},
        {"calls": 8, "env_bindings_copied": 128},
    ]

    assert benchmark_yueval.classify(measurements) == "definitions-by-calls"


def test_residual_checkpoint_does_not_enumerate_ancestor_bindings(monkeypatch):
    yugen = benchmark_yueval.yugen
    gate = yugen.ATOM("gate")
    env = yugen.ENV(
        None,
        [(yugen.ATOM(f"unrelated_{index}"), yugen.INT(index)) for index in range(100)],
    )
    env.predeclare(gate)
    enumerated = 0
    original_xlocal = yugen.ENV.xlocal

    def counted_xlocal(current):
        nonlocal enumerated
        enumerated += len(current)
        return original_xlocal(current)

    monkeypatch.setattr(yugen.ENV, "xlocal", counted_xlocal)
    checkpoint = yugen.yueval(
        yugen.COND(yugen.VAR([], gate), yugen.INT(1), yugen.INT(0)), env
    )

    assert isinstance(checkpoint, yugen.COND_CLOSURE)
    assert enumerated == 0


def test_closure_copy_count_is_constant_in_parameter_count(monkeypatch):
    yugen = benchmark_yueval.yugen
    cases = []
    for count in (1, 20):
        parameters = [yugen.ATOM(f"parameter_{index}") for index in range(count)]
        closure = yugen.yueval(
            yugen.LAMBDA(
                [([], parameter, None) for parameter in parameters],
                yugen.VAR([], parameters[-1]),
            ),
            yugen.ENV(),
        )
        function_name = yugen.ATOM(f"function_{count}")
        cases.append((yugen.ENV(None, [(function_name, closure)]), function_name, count))
    deepcopy_calls = 0
    existing_binding_reorders = 0
    bindings_enumerated = 0
    original_deepcopy = yugen.L_CLOSURE.__deepcopy__
    original_setitem = yugen.ENV.__setitem__
    original_xlocal = yugen.ENV.xlocal

    def counted_deepcopy(current, memo=None):
        nonlocal deepcopy_calls
        deepcopy_calls += 1
        return original_deepcopy(current, memo)

    def counted_setitem(current, key, value):
        nonlocal existing_binding_reorders
        if dict.__contains__(current, key):
            existing_binding_reorders += 1
        return original_setitem(current, key, value)

    def counted_xlocal(current):
        nonlocal bindings_enumerated
        bindings_enumerated += len(current)
        return original_xlocal(current)

    monkeypatch.setattr(yugen.L_CLOSURE, "__deepcopy__", counted_deepcopy)
    monkeypatch.setattr(yugen.ENV, "__setitem__", counted_setitem)
    monkeypatch.setattr(yugen.ENV, "xlocal", counted_xlocal)
    copies_per_call = []
    enumerated_per_call = []
    for env, function_name, count in cases:
        copies_before = deepcopy_calls
        bindings_before = bindings_enumerated
        result = yugen.yueval(
            yugen.APPLY(
                yugen.VAR([], function_name),
                [yugen.INT(index) for index in range(count)],
                [],
            ),
            env,
        )
        copies_per_call.append(deepcopy_calls - copies_before)
        enumerated_per_call.append(bindings_enumerated - bindings_before)
        assert result == count - 1

    assert copies_per_call == [1, 1]
    assert enumerated_per_call == [2, 40]
    assert existing_binding_reorders == 0
