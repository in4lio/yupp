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
    assert few["call_frames_created"] == many["call_frames_created"] == 6
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
    assert [item["call_frames_created"] for item in measurements] == [8, 16, 32]
    assert [item["captured_ancestor_bindings_enumerated"] for item in measurements] == [0, 0, 0]
