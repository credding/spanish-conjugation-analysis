from dataclasses import dataclass

from .grammar_base_model import BaseLemma, BaseVerb, BaseVerbForm, VerbTag


@dataclass
class DLELemma(BaseLemma):
    dle_url: str


@dataclass
class DLEVerb(BaseVerb, DLELemma):
    is_model_verb: bool
    model_verbs: list[VerbTag]


@dataclass
class DLEVerbForm(BaseVerbForm):
    preference: int
