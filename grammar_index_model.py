from dataclasses import dataclass

from annotated_string import AnnotatedString
from grammar_base_model import BaseElement, BaseLemma, BaseVerb, BaseVerbForm, VerbTag
from phonetic_analysis import PhoneticForm


@dataclass(kw_only=True)
class IndexLemma(BaseLemma):
    dle_url: str
    freq_adj: float


@dataclass(kw_only=True)
class IndexVerb(IndexLemma, BaseVerb):
    model_verbs: list[VerbTag]
    study_order: int | None


@dataclass(kw_only=True)
class IndexElement(BaseElement):
    pass


@dataclass(kw_only=True)
class IndexVerbForm(IndexElement, BaseVerbForm):
    preference: int
    alt_phonology: AnnotatedString | None


@dataclass(kw_only=True)
class MappedLemma(IndexLemma):
    pass


@dataclass(kw_only=True)
class MappedVerb(MappedLemma, IndexVerb):
    pass


@dataclass(kw_only=True)
class MappedElement(IndexElement):
    lemma: MappedLemma
    annotated_form: AnnotatedString
    graphic_form: PhoneticForm
    graphic_form_no_stress: PhoneticForm
    phonetic_form: PhoneticForm
    phonetic_form_no_stress: PhoneticForm


@dataclass(kw_only=True)
class MappedVerbForm(MappedElement, IndexVerbForm):
    pass
