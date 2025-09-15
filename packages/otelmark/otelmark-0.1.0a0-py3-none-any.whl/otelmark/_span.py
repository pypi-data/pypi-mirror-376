# Copyright 2025 Çağlar Kutlu
# SPDX-License-Identifier: Apache-2.0

from importlib.metadata import version

import attrs
from opentelemetry import trace

from ._constants import PACKAGE_NAME
from ._utils import ContextManagerAndContextDecorator


@attrs.frozen
class _InstrumentationConfig:
    _provider: trace.TracerProvider
    tracer: trace.Tracer

    @classmethod
    def default(cls):
        provider = trace.get_tracer_provider()
        tracer = provider.get_tracer(PACKAGE_NAME, version(PACKAGE_NAME))
        return cls(provider, tracer)


GLOBAL_CONFIG = _InstrumentationConfig.default()


def span(name: str) -> ContextManagerAndContextDecorator[trace.Span, bool | None]:
    return GLOBAL_CONFIG.tracer.start_as_current_span(
        name=name,
        kind=trace.SpanKind.INTERNAL,
        record_exception=False,
        set_status_on_exception=False,
    )
