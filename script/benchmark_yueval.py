#!/usr/bin/env python3
"""Reproduce the legacy definitions-by-calls evaluator baseline."""

from contextlib import ExitStack
import argparse
import json
from pathlib import Path
import sys
from time import perf_counter
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from yupp.pp import yugen  # noqa: E402


BASELINE_SIZES = (25, 50, 100, 200, 400)


def build_call_workload(definitions, calls):
    """Build a parameter-only closure behind unrelated bindings."""
    env = yugen.ENV(
        None,
        [
            (yugen.ATOM(f"unrelated_{index}"), yugen.INT(index))
            for index in range(definitions)
        ],
    )
    parameter = yugen.ATOM("parameter")
    function_name = yugen.ATOM("identity")
    closure = yugen.yueval(
        yugen.LAMBDA([([], parameter, None)], yugen.VAR([], parameter)),
        env,
    )
    env[function_name] = closure
    workload = yugen.LIST(
        [
            yugen.APPLY(
                yugen.VAR([], function_name),
                [yugen.INT(index)],
                [],
            )
            for index in range(calls)
        ]
    )
    return workload, env


def structural_baseline(definitions, calls):
    workload, env = build_call_workload(definitions, calls)
    counters = {
        "env_deepcopy_calls": 0,
        "env_bindings_copied": 0,
        "lookup_calls": 0,
        "lookup_frame_visits": 0,
    }
    original_deepcopy = yugen.ENV.__deepcopy__
    original_lookup = yugen.ENV.lookup

    def counted_deepcopy(current, memo=None):
        counters["env_deepcopy_calls"] += 1
        counters["env_bindings_copied"] += len(current)
        return original_deepcopy(current, memo)

    def counted_lookup(current, reg, var):
        counters["lookup_calls"] += 1
        frame = current
        while frame is not None:
            counters["lookup_frame_visits"] += 1
            if frame.__contains__(var):
                break
            frame = frame.parent
        return original_lookup(current, reg, var)

    with ExitStack() as stack:
        stack.enter_context(patch.object(yugen.ENV, "__deepcopy__", counted_deepcopy))
        stack.enter_context(patch.object(yugen.ENV, "lookup", counted_lookup))
        result = yugen.yueval(workload, env)

    assert result == yugen.LIST([yugen.INT(index) for index in range(calls)])
    return counters


def timed_baseline(definitions, calls):
    workload, env = build_call_workload(definitions, calls)
    started = perf_counter()
    result = yugen.yueval(workload, env)
    seconds = perf_counter() - started
    assert result == yugen.LIST([yugen.INT(index) for index in range(calls)])
    return seconds


def measure_case(definitions, calls, include_timing=True):
    measurement = {
        "definitions": definitions,
        "calls": calls,
        **structural_baseline(definitions, calls),
    }
    if include_timing:
        measurement["seconds"] = timed_baseline(definitions, calls)
    return measurement


def classify(measurements):
    per_call = [
        measurement["env_bindings_copied"] / measurement["calls"]
        for measurement in measurements
    ]
    return (
        "definitions-by-calls"
        if len(per_call) > 1 and per_call[-1] > per_call[0]
        else "not-detected"
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--sizes",
        nargs="+",
        type=int,
        default=BASELINE_SIZES,
        help="definition/call counts to measure",
    )
    parser.add_argument(
        "--no-timing",
        action="store_true",
        help="collect deterministic structural counters only",
    )
    arguments = parser.parse_args(argv)
    measurements = [
        measure_case(size, size, include_timing=not arguments.no_timing)
        for size in arguments.sizes
    ]
    print(
        json.dumps(
            {
                "classification": classify(measurements),
                "measurements": measurements,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
