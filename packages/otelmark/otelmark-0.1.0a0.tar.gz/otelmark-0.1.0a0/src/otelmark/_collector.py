# Copyright 2025 Çağlar Kutlu
# SPDX-License-Identifier: Apache-2.0

from contextlib import AbstractContextManager
from typing import cast

import attrs
from opentelemetry.baggage import get_baggage
from opentelemetry.context import Context
from opentelemetry.sdk.trace import Span, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import set_tracer_provider
from opentelemetry.util.types import AttributeValue

from otelmark._collections import SignalCollection
from otelmark._constants import RESOURCE

from ._collections import TraceCollection

_COLLECTOR = None


def collect(*, into: SignalCollection) -> AbstractContextManager[None, None]:
    return _Collector.singleton().collect(into=into)


class BaggagePassingSpanProcessor(SimpleSpanProcessor):
    def on_start(self, span: Span, parent_context: Context | None = None) -> None:
        # TODO: Pass the baggage name here explicitly and get rid of branching
        baggage = cast(
            dict[str, AttributeValue], get_baggage("otelmark.benchmark", parent_context)
        )

        if baggage is not None:
            span.set_attributes(baggage)

        # TODO: Get rid of baggage passing. It costs ~2us!
        # span._start_time = time.time_ns()


@attrs.define
class InMemoryTracingContextManager:
    collection: TraceCollection

    provider: TracerProvider
    _exporter: InMemorySpanExporter = attrs.field(
        init=False, factory=InMemorySpanExporter
    )

    def __enter__(self):
        self.provider.add_span_processor(BaggagePassingSpanProcessor(self._exporter))

    def __exit__(self, exc_type, exc_value, traceback):
        provider = cast(TracerProvider, self.provider)
        provider.shutdown()
        self.collection.append_spans(self._exporter.get_finished_spans())


@attrs.define
class _Collector:
    _tracer_provider: TracerProvider = attrs.field()

    def collect(self, *, into: SignalCollection) -> AbstractContextManager[None, None]:
        return InMemoryTracingContextManager(into.traces, self._tracer_provider)

    @classmethod
    def singleton(cls):
        global _COLLECTOR
        if _COLLECTOR is not None:
            return _COLLECTOR

        provider = TracerProvider(resource=RESOURCE)
        set_tracer_provider(provider)

        _COLLECTOR = cls(provider)
        return _COLLECTOR
