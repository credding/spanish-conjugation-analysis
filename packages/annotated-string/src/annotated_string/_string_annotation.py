# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from abc import ABC
from collections.abc import Hashable
from dataclasses import dataclass
from functools import total_ordering
from typing import TypeAlias

from ._errors import ConstraintError

_KeyRange: TypeAlias = tuple[int, int]


@dataclass(repr=False)
@total_ordering
class StringAnnotation(ABC):
    string: str
    start: int
    stop: int

    def __post_init__(self) -> None:
        if self.start < 0:
            msg = f"start must be >= 0, got {self.start}"
            raise ConstraintError(msg)
        if self.stop > len(self.string):
            msg = f"stop must be <= string length, got {self.stop}"
            raise ConstraintError(msg)
        if self.start > self.stop:
            msg = f"start must be <= stop, got {self.start} <= {self.stop}"
            raise ConstraintError(msg)

    @property
    def text(self) -> str:
        return self.string[self.start : self.stop]

    @property
    def unique_key(self) -> Hashable:
        return type(self)

    @property
    def unique_key_range(self) -> _KeyRange:
        return self.start, self.stop

    def __lt__(self, other: StringAnnotation) -> bool:
        if not isinstance(other, StringAnnotation):
            return NotImplemented
        return (self.start, self.stop) < (other.start, other.stop)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"{self.string[: self.start]}"
            f"[{self.text}]"
            f"{self.string[self.stop :]})"
        )


@dataclass(repr=False)
class SingletonStringAnnotation(StringAnnotation, ABC):
    def unique_key_range(self) -> _KeyRange:
        return 0, len(self.string)


@dataclass(repr=False)
class DiffStringAnnotation(SingletonStringAnnotation):
    diff_text: str

    @property
    def diff_stop(self) -> int:
        return self.stop - (len(self.text) - len(self.diff_text))

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"{self.string[: self.start]}"
            f"[{self.diff_text or ''''''} -> {self.text or ''''''}]"
            f"{self.string[self.stop :]})"
        )
