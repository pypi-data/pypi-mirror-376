# Copyright 2025 Çağlar Kutlu
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable
from typing import Any, Protocol, TypeVar

_T_co = TypeVar("_T_co", covariant=True)
_ExitT_co = TypeVar("_ExitT_co", covariant=True, bound=bool | None)
_F = TypeVar("_F", bound=Callable[..., Any])


class ContextManagerAndContextDecorator(Protocol[_T_co, _ExitT_co]):
    def __enter__(self) -> _T_co: ...
    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
        /,
    ) -> _ExitT_co: ...
    def __call__(self, func: _F) -> _F: ...
