from abc import ABC
from dataclasses import dataclass, field, replace
from functools import total_ordering
from typing import Callable, Concatenate


@dataclass(eq=False, repr=False)
@total_ordering
class StringAnnotation(ABC):
    string: AnnotatedString
    start: int
    stop: int

    def __post_init__(self) -> None:
        assert 0 <= self.start <= self.stop <= len(self.string.text)

    @property
    def text(self) -> str:
        return self.string.text[self.start : self.stop]

    def __lt__(self, other) -> bool:
        if not isinstance(other, StringAnnotation):
            return NotImplemented
        return (self.start, self.stop) < (other.start, other.stop)

    def __eq__(self, other) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        a = (self.string, self.start, self.stop)
        b = (other.string, other.start, other.stop)
        return a == b

    def __hash__(self) -> int:
        return hash((type(self), id(self.string), self.start, self.stop))

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"{self.string.text[: self.start]}"
            f"[{self.text}]"
            f"{self.string.text[self.stop :]})"
        )


@dataclass
class AnnotatedString:
    text: str
    annotations: set[StringAnnotation] = field(default_factory=set)

    def annotate[T: StringAnnotation, **P](
        self,
        cls: Callable[Concatenate[AnnotatedString, int, int, P], T],
        start: int | None = None,
        stop: int | None = None,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        start, stop, _ = slice(start, stop).indices(len(self.text))
        annotation = cls(self, start, stop, *args, **kwargs)
        self.annotations.add(annotation)
        return annotation

    def add_annotation[T: StringAnnotation](self, annotation: T) -> T:
        assert annotation.string.text == self.text
        annotation = replace(annotation, string=self)
        self.annotations.add(annotation)
        return annotation

    def get_annotations[T: StringAnnotation](
        self,
        cls: type[T],
        start: int | None = None,
        stop: int | None = None,
    ) -> list[T]:
        start, stop, _ = slice(start, stop).indices(len(self.text))
        return sorted(
            x
            for x in self.annotations
            if isinstance(x, cls)
            and (
                (start <= x.start < stop or start < x.stop <= stop)
                or start <= x.start == x.stop <= stop
            )
        )

    def get_annotation[T: StringAnnotation](
        self,
        cls: type[T],
        start: int | None = None,
        stop: int | None = None,
    ) -> T | None:
        annotations = self.get_annotations(cls, start, stop)
        assert len(annotations) <= 1
        return annotations[0] if annotations else None

    def remove_annotations[T: StringAnnotation](
        self,
        cls: type[T],
        start: int | None = None,
        stop: int | None = None,
    ) -> list[T]:
        annotations = self.get_annotations(cls, start, stop)
        self.annotations -= set(annotations)
        return annotations

    def remove_annotation[T: StringAnnotation](
        self,
        cls: type[T],
        start: int | None = None,
        stop: int | None = None,
    ) -> T | None:
        annotation = self.get_annotation(cls, start, stop)
        if not annotation:
            return None
        self.annotations.remove(annotation)
        return annotation

    def __getitem__(self, segment: slice) -> AnnotatedString:
        start, stop, _ = segment.indices(len(self.text))

        result = AnnotatedString(self.text[start:stop])
        result.annotations = {
            replace(
                x,
                string=result,
                start=max(x.start - start, 0),
                stop=min(x.stop - start, stop - start),
            )
            for x in self.annotations
            if (
                (start <= x.start < stop or start < x.stop <= stop)
                or start <= x.start == x.stop <= stop
            )
        }

        assert all(x.string is result for x in result.annotations)
        return result

    def __add__(self, other: AnnotatedString | str) -> AnnotatedString:
        result = AnnotatedString(self.text)
        result.annotations = {replace(x, string=result) for x in self.annotations}

        match other:
            case str():
                result.text += other
            case AnnotatedString():
                result.text += other.text
                result.annotations.update(
                    replace(
                        x,
                        string=result,
                        start=x.start + len(self.text),
                        stop=x.stop + len(self.text),
                    )
                    for x in other.annotations
                )
            case _:
                return NotImplemented

        assert all(x.string is result for x in result.annotations)
        return result
