from abc import ABC
from dataclasses import dataclass
from typing import Callable, Concatenate

from annotated_string import AnnotatedString, StringAnnotation


@dataclass(repr=False)
class DiffAnnotation(StringAnnotation, ABC):
    diff_text: str

    @property
    def diff_string(self) -> str:
        return f"{self.string.text[: self.start]}{self.diff_text}{self.string.text[self.stop :]}"

    @property
    def diff_stop(self):
        return self.stop - (len(self.text) - len(self.diff_text))

    def __repr__(self):
        return (
            f"{type(self).__name__}("
            f"{self.string.text[: self.start]}"
            f"[{self.diff_text or "''"}->{self.text or "''"}]"
            f"{self.string.text[self.stop :]})"
        )


def annotate_diff[T: DiffAnnotation, **P](
    annotation_type: Callable[Concatenate[AnnotatedString, int, int, str, P], T],
    word: AnnotatedString,
    diff_string: str,
    *args: P.args,
    **kwargs: P.kwargs,
) -> T | None:
    if word.text == diff_string:
        return None

    start_offset = 0
    while (
        start_offset < len(word.text)
        and start_offset < len(diff_string)
        and word.text[start_offset] == diff_string[start_offset]
    ):
        start_offset += 1

    stop_offset = 0
    while (
        stop_offset < len(word.text)
        and stop_offset < len(diff_string)
        and len(word.text) - stop_offset > start_offset
        and word.text[-(stop_offset + 1)] == diff_string[-(stop_offset + 1)]
    ):
        stop_offset += 1

    return word.annotate(
        annotation_type,
        start_offset,
        len(word.text) - stop_offset,
        diff_string[start_offset : -stop_offset or None],
        *args,
        **kwargs,
    )
