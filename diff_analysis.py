from abc import ABC
from dataclasses import dataclass
from typing import Callable, Concatenate

from string_analysis import AnnotatedString, StringAnnotation


@dataclass(frozen=True, eq=False, repr=False)
class DiffAnnotation(StringAnnotation, ABC):
    from_string: str

    @property
    def stop_offset(self):
        return len(self.string.text) - self.stop

    @property
    def from_text(self) -> str:
        return self.from_string[self.start : -self.stop_offset or None]

    def __repr__(self):
        return (
            f"{type(self).__name__}("
            f"{self.string.text[: self.start]}"
            f"[{self.from_text or "''"}->{self.text or "''"}]"
            f"{self.string.text[self.stop :]})"
        )


def annotate_diff[T: DiffAnnotation, **P](
    cls: Callable[Concatenate[AnnotatedString, int, int, str, P], T],
    word: AnnotatedString,
    from_string: str,
    *args: P.args,
    **kwargs: P.kwargs,
) -> T | None:
    if word.text == from_string:
        return None

    start_offset = 0
    while (
        start_offset < len(word.text)
        and start_offset < len(from_string)
        and word.text[start_offset] == from_string[start_offset]
    ):
        start_offset += 1

    stop_offset = 0
    while (
        stop_offset < len(word.text)
        and stop_offset < len(from_string)
        and len(word.text) - stop_offset > start_offset
        and word.text[-(stop_offset + 1)] == from_string[-(stop_offset + 1)]
    ):
        stop_offset += 1

    return word.annotate(
        cls,
        start_offset,
        len(word.text) - stop_offset,
        from_string,
        *args,
        **kwargs,
    )
