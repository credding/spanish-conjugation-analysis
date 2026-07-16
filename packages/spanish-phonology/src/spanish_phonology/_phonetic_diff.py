# SPDX-License-Identifier: GPL-3.0-or-later

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from annotated_string import AnnotatedString

from ._phonetic_analysis import Phoneme
from ._phonetic_spelling import SpellingType
from .phonetics import TX_REMOVE_DIACRITICS, TX_REMOVE_STRESS


@dataclass
class PhoneticDiffResult:
    start: int
    stop: int
    diff_start: int
    diff_stop: int


def get_phonetic_diff(
    word: AnnotatedString, diff_word: AnnotatedString, spelling_type: SpellingType
) -> PhoneticDiffResult | None:
    eq_phoneme = {
        SpellingType.GRAPHIC: _eq_graphic,
        SpellingType.GRAPHIC_NO_STRESS: _eq_graphic_no_stress,
        SpellingType.GRAPHIC_NO_DIACRITICS: _eq_graphic_no_diacritics,
        SpellingType.PHONETIC: _eq_phonetic,
        SpellingType.PHONETIC_NO_STRESS: _eq_phonetic_no_stress,
    }[spelling_type]

    return _get_phonetic_diff(word, diff_word, eq_phoneme)


def _get_phonetic_diff(
    word: AnnotatedString,
    diff_word: AnnotatedString,
    eq: Callable[[Phoneme, Phoneme], bool],
) -> PhoneticDiffResult | None:
    phonemes = word.get_annotations(Phoneme)
    diff_phonemes = diff_word.get_annotations(Phoneme)

    diff_range = _get_phoneme_diff_range(phonemes, diff_phonemes, eq)
    if diff_range is None:
        return None

    start_phoneme, stop_phoneme, diff_stop_phoneme = diff_range

    start = _get_phoneme_text_index(phonemes, start_phoneme)
    stop = _get_phoneme_text_index(phonemes, stop_phoneme)
    diff_start = _get_phoneme_text_index(diff_phonemes, start_phoneme)
    diff_stop = _get_phoneme_text_index(diff_phonemes, diff_stop_phoneme)

    return PhoneticDiffResult(start, stop, diff_start, diff_stop)


def _get_phoneme_text_index(phonemes: Sequence[Phoneme], index: int) -> int:
    return phonemes[index].start if index < len(phonemes) else len(phonemes[-1].string)


def _get_phoneme_diff_range(
    string: Sequence[Phoneme],
    diff_string: Sequence[Phoneme],
    eq: Callable[[Phoneme, Phoneme], bool],
) -> tuple[int, int, int] | None:
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

    return start, stop, stop - len_diff


def _eq_graphic(a: Phoneme, b: Phoneme) -> bool:
    return a.text == b.text


def _eq_graphic_no_stress(a: Phoneme, b: Phoneme) -> bool:
    a_text_norm = a.text.translate(TX_REMOVE_STRESS)
    b_text_norm = b.text.translate(TX_REMOVE_STRESS)
    return a_text_norm == b_text_norm


def _eq_graphic_no_diacritics(a: Phoneme, b: Phoneme) -> bool:
    a_text_norm = a.text.translate(TX_REMOVE_DIACRITICS)
    b_text_norm = b.text.translate(TX_REMOVE_DIACRITICS)
    return a_text_norm == b_text_norm


def _eq_phonetic(a: Phoneme, b: Phoneme) -> bool:
    return (a.phoneme_kind, a.phoneme) == (b.phoneme_kind, b.phoneme)


def _eq_phonetic_no_stress(a: Phoneme, b: Phoneme) -> bool:
    return a.phoneme == b.phoneme
