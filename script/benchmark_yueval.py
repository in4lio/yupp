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


def build_call_workload(definitions, calls, demand_ancestor=False):
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
    body = (
        yugen.LET(
            yugen.ATOM("lookup_probe"),
            yugen.INT(0),
            yugen.VAR([], yugen.ATOM("unrelated_0")),
        )
        if demand_ancestor
        else yugen.VAR([], parameter)
    )
    closure = yugen.yueval(
        yugen.LAMBDA([([], parameter, None)], body),
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
    expected = (
        yugen.LIST([yugen.INT(0) for _ in range(calls)])
        if demand_ancestor
        else yugen.LIST([yugen.INT(index) for index in range(calls)])
    )
    return workload, env, function_name, expected


def structural_baseline(definitions, calls, demand_ancestor=False):
    workload, env, function_name, expected = build_call_workload(
        definitions, calls, demand_ancestor=demand_ancestor
    )
    counters = {
        "call_frames_created": 0,
        "captured_ancestor_copy_attempts": 0,
        "captured_ancestor_bindings_enumerated": 0,
        "env_deepcopy_calls": 0,
        "env_bindings_copied": 0,
        "lookup_calls": 0,
        "lookup_frame_visits": 0,
        "call_target_lookup_frame_visits": 0,
        "demanded_name_lookup_frame_visits": 0,
    }
    captured_frames = set()
    frame = env
    while frame is not None:
        captured_frames.add(id(frame))
        frame = frame.parent
    original_init = yugen.ENV.__init__
    original_deepcopy = yugen.ENV.__deepcopy__
    original_lookup = yugen.ENV.lookup
    original_xlocal = yugen.ENV.xlocal

    def counted_init(current, parent=None, local=None):
        if parent is not None:
            counters["call_frames_created"] += 1
        original_init(current, parent, local)

    def counted_deepcopy(current, memo=None):
        counters["env_deepcopy_calls"] += 1
        counters["env_bindings_copied"] += len(current)
        if id(current) in captured_frames:
            counters["captured_ancestor_copy_attempts"] += 1
        return original_deepcopy(current, memo)

    def counted_lookup(current, reg, var):
        counters["lookup_calls"] += 1
        frame = current
        while frame is not None:
            counters["lookup_frame_visits"] += 1
            counter = (
                "call_target_lookup_frame_visits"
                if var == function_name
                else "demanded_name_lookup_frame_visits"
            )
            counters[counter] += 1
            if frame.__contains__(var):
                break
            frame = frame.parent
        return original_lookup(current, reg, var)

    def counted_xlocal(current):
        if id(current) in captured_frames:
            counters["captured_ancestor_bindings_enumerated"] += len(current)
        return original_xlocal(current)

    with ExitStack() as stack:
        stack.enter_context(patch.object(yugen.ENV, "__init__", counted_init))
        stack.enter_context(patch.object(yugen.ENV, "__deepcopy__", counted_deepcopy))
        stack.enter_context(patch.object(yugen.ENV, "lookup", counted_lookup))
        stack.enter_context(patch.object(yugen.ENV, "xlocal", counted_xlocal))
        result = yugen.yueval(workload, env)

    assert result == expected
    return counters


def timed_baseline(definitions, calls, demand_ancestor=False):
    workload, env, _, expected = build_call_workload(
        definitions, calls, demand_ancestor=demand_ancestor
    )
    started = perf_counter()
    result = yugen.yueval(workload, env)
    seconds = perf_counter() - started
    assert result == expected
    return seconds


def measure_case(definitions, calls, include_timing=True, demand_ancestor=False):
    measurement = {
        "definitions": definitions,
        "calls": calls,
        **structural_baseline(definitions, calls, demand_ancestor=demand_ancestor),
    }
    if include_timing:
        measurement["seconds"] = timed_baseline(
            definitions, calls, demand_ancestor=demand_ancestor
        )
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
