from abc import ABC
from dataclasses import dataclass, field, replace
from functools import total_ordering
from typing import Callable, Concatenate


@dataclass(frozen=True, slots=True)
class StringAnnotationKey:
    annotation_type: type[StringAnnotation]
    start: int
    stop: int


@dataclass(repr=False)
@total_ordering
class StringAnnotation(ABC):
    string: AnnotatedString
    start: int
    stop: int

    def __post_init__(self) -> None:
        if self.start < 0:
            raise ValueError(f"start must be >= 0, got {self.start}")
        if self.stop > len(self.string.text):
            raise ValueError(f"stop must be <= string length, got {self.stop}")

    @property
    def text(self) -> str:
        return self.string.text[self.start : self.stop]

    @property
    def key(self) -> StringAnnotationKey:
        return StringAnnotationKey(type(self), self.start, self.stop)

    def __lt__(self, other) -> bool:
        if not isinstance(other, StringAnnotation):
            return NotImplemented
        return (self.start, self.stop) < (other.start, other.stop)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"{self.string.text[: self.start]}"
            f"[{self.text}]"
            f"{self.string.text[self.stop :]})"
        )


@dataclass(eq=False)
class AnnotatedString:
    text: str
    _annotations: dict[StringAnnotationKey, StringAnnotation] = field(
        default_factory=dict
    )

    @property
    def annotations(self) -> list[StringAnnotation]:
        return [*self._annotations.values()]

    def annotate[T: StringAnnotation, **P](
        self,
        annotation_type: Callable[Concatenate[AnnotatedString, int, int, P], T],
        start: int | None = None,
        stop: int | None = None,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T:
        start, stop, _ = slice(start, stop).indices(len(self.text))
        annotation = annotation_type(self, start, stop, *args, **kwargs)
        self._annotations[annotation.key] = annotation
        return annotation

    def add_annotation[T: StringAnnotation](self, annotation: T):
        if annotation.string is not self:
            raise ValueError(f"annotation {annotation} is not for this string")
        self._annotations[annotation.key] = annotation

    def get_annotations[T: StringAnnotation](
        self,
        annotation_type: type[T],
        start: int | None = None,
        stop: int | None = None,
    ) -> list[T]:
        start, stop, _ = slice(start, stop).indices(len(self.text))
        return sorted(
            x
            for x in self._annotations.values()
            if isinstance(x, annotation_type)
            and (
                (start <= x.start < stop or start < x.stop <= stop)
                or start <= x.start == x.stop <= stop
            )
        )

    def get_annotation_or_none[T: StringAnnotation](
        self,
        annotation_type: type[T],
        start: int | None = None,
        stop: int | None = None,
    ) -> T | None:
        annotations = self.get_annotations(annotation_type, start, stop)
        if len(annotations) > 1:
            raise ValueError(
                f"multiple annotations of type {annotation_type} found for string {self.text}"
            )
        return annotations[0] if len(annotations) > 0 else None

    def get_annotation[T: StringAnnotation](
        self,
        annotation_type: type[T],
        start: int | None = None,
        stop: int | None = None,
    ):
        annotation = self.get_annotation_or_none(annotation_type, start, stop)
        if annotation is None:
            raise KeyError(
                f"no annotation of type {annotation_type} found for string {self.text}"
            )
        return annotation

    def remove_annotations[T: StringAnnotation](
        self,
        annotation_type: type[T],
        start: int | None = None,
        stop: int | None = None,
    ) -> list[T]:
        annotations = self.get_annotations(annotation_type, start, stop)
        for annotation in annotations:
            del self._annotations[annotation.key]
        return annotations

    def remove_annotation_or_none[T: StringAnnotation](
        self,
        annotation_type: type[T],
        start: int | None = None,
        stop: int | None = None,
    ) -> T | None:
        annotation = self.get_annotation_or_none(annotation_type, start, stop)
        if annotation is not None:
            del self._annotations[annotation.key]
        return annotation

    def remove_annotation[T: StringAnnotation](
        self,
        annotation_type: type[T],
        start: int | None = None,
        stop: int | None = None,
    ) -> T:
        annotation = self.get_annotation(annotation_type, start, stop)
        del self._annotations[annotation.key]
        return annotation

    def __getitem__(self, segment: slice) -> AnnotatedString:
        start, stop, _ = segment.indices(len(self.text))

        result = AnnotatedString(self.text[start:stop])
        for x in self._annotations.values():
            if (
                start <= x.start < stop
                or start < x.stop <= stop
                or start <= x.start == x.stop <= stop
            ):
                result.add_annotation(
                    replace(
                        x,
                        string=result,
                        start=max(x.start - start, 0),
                        stop=min(x.stop - start, stop - start),
                    )
                )

        return result

    def __add__(self, other: AnnotatedString | str) -> AnnotatedString:
        result = AnnotatedString(self.text)
        for x in self._annotations.values():
            result.add_annotation(replace(x, string=result))

        match other:
            case str():
                result.text += other
            case AnnotatedString():
                result.text += other.text
                for x in other._annotations.values():
                    result.add_annotation(
                        replace(
                            x,
                            string=result,
                            start=x.start + len(self.text),
                            stop=x.stop + len(self.text),
                        )
                    )
            case _:
                return NotImplemented

        return result

    def __radd__(self, other: str) -> AnnotatedString:
        if not isinstance(other, str):
            return NotImplemented

        result = AnnotatedString(other + self.text)
        for x in self._annotations.values():
            result.add_annotation(
                replace(
                    x,
                    string=result,
                    start=x.start + len(other),
                    stop=x.stop + len(other),
                )
            )

        return result
