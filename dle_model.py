from dataclasses import dataclass

from grammar_model import (
    BaseLemma,
    BaseVerb,
    BaseVerbForm,
    Subject,
    Variant,
    Verb,
    VerbForm,
    VerbTag,
)


@dataclass
class DLELemma(BaseLemma):
    dle_url: str


@dataclass
class DLEVerb(BaseVerb, DLELemma):
    is_model: bool
    models: list[VerbTag]

    def as_verb(self) -> Verb:
        return Verb(self.base_form, dle_url=self.dle_url, models=self.models)


@dataclass
class DLEVerbForm(BaseVerbForm):
    subject_group: list[Subject]
    variant: Variant | None
    preference: int

    def as_verb_form(self, verb: Verb) -> VerbForm:
        return VerbForm(
            self.lemma_tag,
            self.form,
            verb,
            self.tense,
            self.subject,
            self.subject_group,
            self.variant,
            self.preference,
        )
