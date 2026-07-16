# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass

from annotated_string import AnnotatedString
from spanish_grammar import Verb
from spanish_phonology import PhoneticForm

from .grammar_base_model import BaseElement, BaseLemma, BaseVerb, BaseVerbForm


@dataclass(kw_only=True)
class IndexLemma(BaseLemma):
    dle_url: str
    freq_adj: float


@dataclass(kw_only=True)
class IndexVerb(IndexLemma, BaseVerb):
    model_verbs: list[Verb]
    study_order: int | None


@dataclass(kw_only=True)
class IndexElement(BaseElement):
    pass


@dataclass(kw_only=True)
class IndexVerbForm(IndexElement, BaseVerbForm):
    preference: int
    alt_phonology: AnnotatedString | None


@dataclass(kw_only=True)
class MappedLemma(BaseLemma):
    dle_url: str
    freq_adj: float


@dataclass(kw_only=True)
class MappedVerb(MappedLemma, BaseVerb):
    model_verbs: list[Verb]
    study_order: int | None


@dataclass(kw_only=True)
class MappedElement(BaseElement):
    lemma: MappedLemma
    annotated_form: AnnotatedString
    graphic_form: PhoneticForm
    graphic_form_no_stress: PhoneticForm
    phonetic_form: PhoneticForm
    phonetic_form_no_stress: PhoneticForm


@dataclass(kw_only=True)
class MappedVerbForm(MappedElement, BaseVerbForm):
    lemma: MappedVerb
    preference: int
    alt_phonology: AnnotatedString | None
