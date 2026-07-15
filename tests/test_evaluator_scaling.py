import importlib.util
from pathlib import Path


BENCHMARK_PATH = Path(__file__).resolve().parents[1] / "script" / "benchmark_yueval.py"
SPEC = importlib.util.spec_from_file_location("benchmark_yueval", BENCHMARK_PATH)
benchmark_yueval = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(benchmark_yueval)


def test_legacy_call_setup_deepcopies_unrelated_bindings_baseline():
    few = benchmark_yueval.measure_case(4, 3, include_timing=False)
    many = benchmark_yueval.measure_case(12, 3, include_timing=False)

    assert few["env_deepcopy_calls"] == many["env_deepcopy_calls"] == 6
    assert few["env_bindings_copied"] == 18
    assert many["env_bindings_copied"] == 42
    assert many["env_bindings_copied"] - few["env_bindings_copied"] == 3 * (12 - 4)


def test_legacy_scaling_classifier_detects_definitions_by_calls_growth():
    measurements = [
        benchmark_yueval.measure_case(size, size, include_timing=False)
        for size in (4, 8, 16)
    ]

    assert benchmark_yueval.classify(measurements) == "definitions-by-calls"
    assert [item["env_bindings_copied"] for item in measurements] == [24, 80, 288]
    assert [item["lookup_frame_visits"] for item in measurements] == [8, 16, 32]
