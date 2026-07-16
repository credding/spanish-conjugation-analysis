# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass
from enum import Enum, auto

from annotated_string import AnnotatedString

from spanish_phonology import Phoneme
from spanish_phonology.phonetics import (
    TX_ADD_STRESS,
    TX_REMOVE_DIACRITICS,
    TX_REMOVE_STRESS,
)


class SpellingType(Enum):
    GRAPHIC = auto()
    GRAPHIC_NO_STRESS = auto()
    GRAPHIC_NO_DIACRITICS = auto()
    PHONETIC = auto()
    PHONETIC_NO_STRESS = auto()


@dataclass(frozen=True, slots=True)
class PhoneticForm:
    spelling_type: SpellingType
    form: str


def get_phonetic_form(
    word: AnnotatedString, spelling_type: SpellingType
) -> PhoneticForm:
    form = {
        SpellingType.GRAPHIC: _get_graphic_form,
        SpellingType.GRAPHIC_NO_STRESS: _get_graphic_form_no_stress,
        SpellingType.GRAPHIC_NO_DIACRITICS: _get_graphic_form_no_diacritics,
        SpellingType.PHONETIC: _get_phonetic_form,
        SpellingType.PHONETIC_NO_STRESS: _get_phonetic_form_no_stress,
    }[spelling_type](word)

    return PhoneticForm(spelling_type, form)


def _get_graphic_form(word: AnnotatedString) -> str:
    return word.string


def _get_graphic_form_no_stress(word: AnnotatedString) -> str:
    return word.string.translate(TX_REMOVE_STRESS)


def _get_graphic_form_no_diacritics(word: AnnotatedString) -> str:
    return word.string.translate(TX_REMOVE_DIACRITICS)


def _get_phonetic_form(word: AnnotatedString) -> str:
    return "".join(
        x.phoneme.translate(TX_ADD_STRESS) if x.has_stress else x.phoneme
        for x in word.get_annotations(Phoneme)
    )


def _get_phonetic_form_no_stress(word: AnnotatedString) -> str:
    return "".join(x.phoneme for x in word.get_annotations(Phoneme))
