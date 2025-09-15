# Copyright 2025 Çağlar Kutlu
# SPDX-License-Identifier: Apache-2.0

"""Utilities for testing `otelmark` itself.

!!! warning

    Nothing here is stable.
"""

import random
import time
import uuid
from contextlib import contextmanager
from typing import Any, Protocol

import attrs
import freezegun
from opentelemetry.trace import Span, Tracer, get_tracer_provider


@contextmanager
def tsl(
    *,
    freeze_time: bool = True,
    spans_out: list[Span] | None = None,
    random_state: random.Random | None = None,
):
    """Tiny language for creating named opentelemetry spans of certain durations
    using context managers."""

    if random_state is None:
        random_state = random.Random()

    tracer = get_tracer_provider().get_tracer("test")

    if freeze_time:
        with freezegun.freeze_time() as frozen:
            yield TSLContext(tracer, frozen.tick, random_state, spans_out)
    else:
        yield TSLContext(tracer, time.sleep, random_state, spans_out)


class _Sleep(Protocol):
    def __call__(self, seconds: float, /) -> Any: ...


@attrs.define
class TSLContext:
    tracer: Tracer
    sleep: _Sleep

    rng: random.Random

    _span_collection: list[Span] | None

    @contextmanager
    def span(self, name: str | None = None):
        if name is None:
            name = uuid.UUID(int=self.rng.getrandbits(128), version=4).urn

        with self.tracer.start_as_current_span(name=name) as span:
            yield
            if self._span_collection is not None:
                self._span_collection.append(span)

    def spend(self, time: float | None = None):
        if time is None:
            time = self.rng.random()

        self.sleep(time)
