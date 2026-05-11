from __future__ import annotations

from abc import ABC
from collections.abc import Callable, Hashable
from dataclasses import dataclass, field, replace
from typing import Concatenate, ParamSpec, TypeVar


@dataclass(repr=False)
class StringAnnotation(ABC):
    string: str
    start: int
    stop: int

    def __post_init__(self) -> None:
        if self.start < 0:
            msg = f"start must be >= 0, got {self.start}"
            raise ValueError(msg)
        if self.stop > len(self.string):
            msg = f"stop must be <= string length, got {self.stop}"
            raise ValueError(msg)

    @property
    def text(self) -> str:
        return self.string[self.start : self.stop]

    @property
    def unique_key(self) -> Hashable:
        return type(self), self.start, self.stop

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


_T = TypeVar("_T", bound=StringAnnotation)
_P = ParamSpec("_P")


@dataclass(eq=False)
class AnnotatedString:
    string: str
    _annotations: dict[Hashable, StringAnnotation] = field(default_factory=dict)

    @property
    def annotations(self) -> list[StringAnnotation]:
        return [*self._annotations.values()]

    def annotate(
        self,
        annotation_type: Callable[Concatenate[str, int, int, _P], _T],
        /,
        start: int | None = None,
        stop: int | None = None,
        *args: _P.args,
        **kwargs: _P.kwargs,
    ) -> _T:
        start, stop, _ = slice(start, stop).indices(len(self.string))
        annotation = annotation_type(self.string, start, stop, *args, **kwargs)
        self.add_annotation(annotation)
        return annotation

    def add_annotation(self, annotation: _T, /) -> None:
        if annotation.string != self.string:
            msg = f"annotation {annotation} is not for this string"
            raise ValueError(msg)
        if annotation.unique_key in self._annotations:
            msg = f"annotation {annotation.unique_key} already exists"
            raise ValueError(msg)
        self._annotations[annotation.unique_key] = annotation

    def get_annotations(self, annotation_type: type[_T]) -> list[_T]:
        return sorted(
            x for x in self._annotations.values() if isinstance(x, annotation_type)
        )

    def get_annotation_or_none(self, annotation_type: type[_T]) -> _T | None:
        annotations = self.get_annotations(annotation_type)
        if len(annotations) > 1:
            msg = (
                f"multiple annotations of type {annotation_type} "
                f"found for string {self.string}"
            )
            raise ValueError(msg)
        return annotations[0] if len(annotations) > 0 else None

    def get_annotation(self, annotation_type: type[_T]) -> _T:
        annotation = self.get_annotation_or_none(annotation_type)
        if annotation is None:
            msg = (
                f"no annotation of type {annotation_type} "
                f"found for string {self.string}"
            )
            raise KeyError(msg)
        return annotation

    def __getitem__(self, segment: slice) -> AnnotatedString:
        start, stop, _ = segment.indices(len(self.string))

        result = AnnotatedString(self.string[start:stop])
        for x in self._annotations.values():
            if (
                start <= x.start < stop
                or start < x.stop <= stop
                or start <= x.start == x.stop <= stop
            ):
                result.add_annotation(
                    replace(
                        x,
                        string=result.string,
                        start=max(x.start - start, 0),
                        stop=min(x.stop - start, stop - start),
                    )
                )

        return result

    def __add__(self, other: str | AnnotatedString) -> AnnotatedString:
        if not isinstance(other, (str, AnnotatedString)):
            return NotImplemented

        match other:
            case str():
                result = AnnotatedString(self.string + other)
                for x in self._annotations.values():
                    result.add_annotation(replace(x, string=result.string))

                return result

            case AnnotatedString():
                result = AnnotatedString(self.string + other.string)
                for x in self._annotations.values():
                    result.add_annotation(replace(x, string=result.string))
                for x in other._annotations.values():
                    result.add_annotation(
                        replace(
                            x,
                            string=result.string,
                            start=len(self.string) + x.start,
                            stop=len(self.string) + x.stop,
                        )
                    )

                return result
