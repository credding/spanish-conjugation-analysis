# SPDX-License-Identifier: GPL-3.0-or-later

from ._affix_analysis import (
    VerbAffix,
    VerbSubject,
    VerbVariant,
    annotate_verb_form_affix,
)
from ._conjugation import (
    RegularMorphologyConjugator,
    RegularSpellingConjugator,
    VerbConjugator,
)

__all__ = [
    "RegularMorphologyConjugator",
    "RegularSpellingConjugator",
    "VerbAffix",
    "VerbConjugator",
    "VerbSubject",
    "VerbVariant",
    "annotate_verb_form_affix",
]
