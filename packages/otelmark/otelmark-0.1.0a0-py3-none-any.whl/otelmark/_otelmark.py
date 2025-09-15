# Copyright 2025 Çağlar Kutlu
# SPDX-License-Identifier: Apache-2.0

import gc
import sys
import time
from collections import defaultdict
from collections.abc import Callable
from typing import cast

import attrs
import numpy as np
from opentelemetry.trace import SpanKind

from otelmark._collections import SignalCollection
from otelmark._collector import collect

from ._span import GLOBAL_CONFIG

_BENCHMARK_ROOT_SPAN_NAME = "otelmark.benchmark"


@attrs.frozen(kw_only=True)
class Stats:
    min: float
    max: float
    mean: float
    median: float
    stddev: float

    @classmethod
    def from_array(cls, arr: np.ndarray[tuple[int], np.dtype[np.float64]]):
        return Stats(
            min=arr.min(),
            max=arr.max(),
            mean=arr.mean(),
            median=np.median(arr, axis=0),
            stddev=arr.std(),
        )


@attrs.frozen
class BenchmarkResult:
    span_stats: dict[str, Stats]
    function_stats: Stats


@attrs.define
class _BenchmarkSignalProcessor:
    """Helper class to produce the signals produced during benchmarks.

    !!! note

        In the long-term, this should become a span processor to reduce memory usage.

    """

    signal_collection: SignalCollection
    rounds: int
    iterations: int
    round_durations_ns: np.ndarray[tuple[int], np.dtype[np.uint64]]

    def _process_round_durations(self) -> Stats:
        round_durations_s = cast(
            np.ndarray[tuple[int], np.dtype[np.float64]],
            self.round_durations_ns.astype(dtype=np.float64) / self.iterations * 1e-9,
        )
        return Stats.from_array(round_durations_s)

    def _process_span_durations(
        self,
    ) -> dict[str, np.ndarray[tuple[int], np.dtype[np.float64]]]:
        spans = self.signal_collection.traces.get_spans()

        by_name = defaultdict(list)
        for span in spans:
            if span.name == _BENCHMARK_ROOT_SPAN_NAME:
                continue
            by_name[span.name].append(span)

        duration_data = defaultdict(
            lambda: np.zeros(shape=self.rounds, dtype=np.float64)
        )
        # NOTE: Assumes spans are ordered by start time
        for name, span_l in by_name.items():
            round = 0
            iter = 0
            for span in span_l:
                assert span.attributes is not None
                assert iter < self.iterations, "Encountered too many iterations."
                assert round < self.rounds, "Encountered too many rounds."

                duration_data[name][round] += (
                    (span.end_time - span.start_time) / self.iterations / 1e9
                )
                iter += 1
                if iter == self.iterations:
                    round += 1
                    iter = 0
        return duration_data

    def process(self) -> BenchmarkResult:
        durations = self._process_span_durations()
        stats = {name: Stats.from_array(arr) for name, arr in durations.items()}
        return BenchmarkResult(stats, function_stats=self._process_round_durations())


def benchmark(
    fun: Callable,
    args: tuple = (),
    kwargs: dict | None = None,
    *,
    rounds: int = 1,
    iterations: int = 1,
    # TODO:
    include_spans: tuple[str, ...] = (),  # noqa: ARG001
    disable_gc: bool = False,
    warmup_rounds: int = 0,
    disable_sys_tracing: bool = True,
) -> BenchmarkResult:
    if kwargs is None:
        kwargs = {}

    systracer = None
    if disable_sys_tracing:
        systracer = sys.gettrace()
        sys.settrace(None)

    has_disabled_gc = False
    if gc.isenabled() and disable_gc:
        gc.disable()
        has_disabled_gc = True

    for _ in range(warmup_rounds):
        for _ in range(iterations):
            fun(*args, **kwargs)

    sigcol = SignalCollection()

    round_durations = np.empty(rounds, dtype=np.uint64)
    with (
        collect(into=sigcol),
        GLOBAL_CONFIG.tracer.start_as_current_span(
            _BENCHMARK_ROOT_SPAN_NAME,
            kind=SpanKind.INTERNAL,  # TEST:
            attributes={"rounds": rounds, "iterations": iterations},
        ),
    ):
        for i in range(rounds):
            start = time.perf_counter_ns()
            for _ in range(iterations):
                fun(*args, **kwargs)
            round_durations[i] = time.perf_counter_ns() - start

    if has_disabled_gc:
        gc.enable()

    if disable_sys_tracing:
        sys.settrace(systracer)

    proc = _BenchmarkSignalProcessor(
        sigcol, rounds=rounds, iterations=iterations, round_durations_ns=round_durations
    )
    return proc.process()


# TODO:
