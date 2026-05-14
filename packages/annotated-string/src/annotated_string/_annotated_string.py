from __future__ import annotations

from abc import ABC
from collections import defaultdict
from collections.abc import Collection, Hashable, Iterator, MutableSet
from dataclasses import dataclass, replace
from functools import total_ordering
from typing import TypeAlias, TypeVar, overload


class ConflictError(ValueError):
    pass


class ConstraintError(ValueError):
    pass


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


class _AnnotationSet(MutableSet[StringAnnotation]):
    def __init__(self, string: str) -> None:
        self._string = string
        self._unique_key_ranges: dict[Hashable, dict[_KeyRange, StringAnnotation]] = (
            defaultdict(dict)
        )

    def add(self, annotation: StringAnnotation, /) -> None:
        self._validate(annotation)
        self._add(annotation)

    def _validate(self, value: StringAnnotation, /) -> None:
        if value.string != self._string:
            msg = f"annotation does not match this string: {value}"
            raise ConstraintError(msg)

        key_ranges = self._unique_key_ranges.get(value.unique_key)
        if key_ranges is None:
            return

        existing = key_ranges.get(value.unique_key_range)
        if existing is not None:
            if existing == value:
                return
            msg = f"annotations have overlapping unique keys: {existing}, {value}"
            raise ConflictError(msg)

        a_start, a_stop = value.unique_key_range
        for (b_start, b_stop), b in key_ranges.items():
            if a_start < b_stop and b_start < a_stop:
                msg = f"annotations have overlapping unique keys: {b}, {value}"
                raise ConflictError(msg)

    def _add(self, value: StringAnnotation, /) -> None:
        self._unique_key_ranges[value.unique_key][value.unique_key_range] = value

    def discard(self, value: StringAnnotation, /) -> None:
        if value not in self:
            return
        self._remove(value)

    def remove(self, value: StringAnnotation, /) -> None:
        if value not in self:
            raise KeyError(value)
        self._remove(value)

    def _remove(self, value: StringAnnotation, /) -> None:
        key_ranges = self._unique_key_ranges[value.unique_key]
        del key_ranges[value.unique_key_range]
        if len(key_ranges) == 0:
            del self._unique_key_ranges[value.unique_key]

    def clear(self) -> None:
        self._unique_key_ranges.clear()

    def __len__(self) -> int:
        return sum(len(ranges) for ranges in self._unique_key_ranges.values())

    def __iter__(self) -> Iterator[StringAnnotation]:
        yield from (
            annotation
            for key_ranges in self._unique_key_ranges.values()
            for annotation in key_ranges.values()
        )

    def __contains__(self, x: object, /) -> bool:
        if not isinstance(x, StringAnnotation):
            return False
        key_ranges = self._unique_key_ranges.get(x.unique_key)
        return key_ranges is not None and x == key_ranges.get(x.unique_key_range)


class _AnnotationsView(Collection[StringAnnotation]):
    def __init__(self, string: AnnotatedString) -> None:
        self._string = string

    def __len__(self) -> int:
        return len(self._string._annotations)  # noqa: SLF001

    def __contains__(self, other: object) -> bool:
        return other in self._string._annotations  # noqa: SLF001

    def __iter__(self) -> Iterator[StringAnnotation]:
        return iter(self._string._annotations)  # noqa: SLF001


_TA = TypeVar("_TA", bound=StringAnnotation)


class AnnotatedString:
    def __init__(self, string: str) -> None:
        self.string = string
        self._annotations = _AnnotationSet(string)

    @property
    def annotations(self) -> Collection[StringAnnotation]:
        return _AnnotationsView(self)

    def add_annotation(self, annotation: StringAnnotation) -> None:
        self._annotations.add(annotation)

    def remove_annotation(self, annotation: StringAnnotation) -> None:
        self._annotations.remove(annotation)

    def clear_annotations(self) -> None:
        self._annotations.clear()

    @overload
    def get_annotations(self) -> list[StringAnnotation]: ...
    @overload
    def get_annotations(self, annotation_type: type[_TA]) -> list[_TA]: ...
    def get_annotations(
        self, annotation_type: type[_TA] | None = None
    ) -> list[StringAnnotation]:
        if annotation_type is None:
            return sorted(self._annotations)
        return sorted(x for x in self._annotations if isinstance(x, annotation_type))

    def __getitem__(self, segment: slice) -> AnnotatedString:
        start, stop, _ = segment.indices(len(self.string))

        result = AnnotatedString(self.string[start:stop])
        for x in self._annotations:
            if x.start < stop and start < x.stop:
                result.add_annotation(
                    replace(
                        x,
                        string=result.string,
                        start=max(x.start - start, 0),
                        stop=min(x.stop - start, len(result.string)),
                    )
                )

        return result

    def __add__(self, other: str | AnnotatedString) -> AnnotatedString:
        match other:
            case str():
                result = AnnotatedString(self.string + other)
                for x in self._annotations:
                    result.add_annotation(replace(x, string=result.string))

                return result

            case AnnotatedString():
                result = AnnotatedString(self.string + other.string)
                for x in self._annotations:
                    result.add_annotation(replace(x, string=result.string))
                for x in other._annotations:
                    result.add_annotation(
                        replace(
                            x,
                            string=result.string,
                            start=len(self.string) + x.start,
                            stop=len(self.string) + x.stop,
                        )
                    )

                return result
            case _:
                return NotImplemented
