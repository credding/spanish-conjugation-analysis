from collections.abc import Callable, Hashable, Sequence
from dataclasses import dataclass

from annotated_string import AnnotatedString, StringAnnotation
from grammar_model import Regularity
from phonetic_analysis import TRANSLATE_REMOVE_DIACRITICS, Phoneme


@dataclass(repr=False)
class Irregularity(StringAnnotation):
    regularity: Regularity
    diff_text: str

    @property
    def diff_string(self) -> str:
        return f"{self.string[: self.start]}{self.diff_text}{self.string[self.stop :]}"

    @property
    def diff_stop(self) -> int:
        return self.stop - (len(self.text) - len(self.diff_text))

    def unique_key(self) -> Hashable:
        return type(self), self.regularity

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}("
            f"{self.string[: self.start]}"
            f"[{self.diff_text or "''"} -> {self.text or "''"}]"
            f"{self.string[self.stop :]})"
            f"{super().__repr__()[:-1]}, "
            f"regularity={self.regularity!r})"
        )


def eq_phoneme(a: Phoneme, b: Phoneme) -> bool:
    return (a.phoneme_kind, a.phoneme) == (b.phoneme_kind, b.phoneme)


def eq_phoneme_text(a: Phoneme, b: Phoneme) -> bool:
    return a.text == b.text


def eq_phoneme_text_norm(a: Phoneme, b: Phoneme) -> bool:
    a_text_norm = a.text.translate(TRANSLATE_REMOVE_DIACRITICS)
    b_text_norm = b.text.translate(TRANSLATE_REMOVE_DIACRITICS)
    return a_text_norm == b_text_norm


def annotate_irregularity(
    word: AnnotatedString,
    diff_word: AnnotatedString,
    /,
    *,
    eq: Callable[[Phoneme, Phoneme], bool],
    tag: Regularity,
) -> Irregularity | None:
    phonemes = word.get_annotations(Phoneme)
    diff_phonemes = diff_word.get_annotations(Phoneme)

    diff_range = _get_diff_range(phonemes, diff_phonemes, eq=eq)
    if diff_range is None:
        return None

    start_phoneme, stop_phoneme = diff_range

    start = (
        phonemes[start_phoneme].start
        if start_phoneme < len(phonemes)
        else len(word.string)
    )
    diff_start = (
        diff_phonemes[start_phoneme].start
        if start_phoneme < len(diff_phonemes)
        else len(diff_word.string)
    )

    len_diff = len(phonemes) - len(diff_phonemes)
    diff_stop_phoneme = stop_phoneme - len_diff

    stop = (
        phonemes[stop_phoneme].start
        if stop_phoneme < len(phonemes)
        else len(word.string)
    )
    diff_stop = (
        diff_phonemes[diff_stop_phoneme].start
        if diff_stop_phoneme < len(diff_phonemes)
        else len(diff_word.string)
    )

    return word.annotate(
        Irregularity, start, stop, tag, diff_word.string[diff_start:diff_stop]
    )


def _get_diff_range[T](
    string: Sequence[T],
    diff_string: Sequence[T],
    /,
    *,
    eq: Callable[[T, T], bool] = lambda x, y: x == y,
) -> tuple[int, int] | None:
    start = 0
    while (
        start < len(string)
        and start < len(diff_string)
        and eq(string[start], diff_string[start])
    ):
        start += 1

    if len(string) == len(diff_string) == start:
        return None

    len_diff = len(string) - len(diff_string)

    stop = len(string)
    while (
        stop > start
        and stop > len_diff
        and eq(string[stop - 1], diff_string[stop - len_diff - 1])
    ):
        stop -= 1

    return start, stop
