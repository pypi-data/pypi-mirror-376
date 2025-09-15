# Copyright 2025 Çağlar Kutlu
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Iterable

import attrs
from opentelemetry.sdk.trace import ReadableSpan


@attrs.define
class TraceCollection:
    _spans: list[ReadableSpan] = attrs.field(factory=list)

    def append_spans(self, spans: Iterable[ReadableSpan]):
        self._spans.extend(spans)

    def get_spans(self):
        return self._spans


@attrs.define
class SignalCollection:
    traces: TraceCollection = attrs.field(factory=TraceCollection)
