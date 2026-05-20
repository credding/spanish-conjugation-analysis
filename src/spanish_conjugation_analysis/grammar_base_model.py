from dataclasses import dataclass

from spanish_grammar import (
    Element,
    Inflection,
    Lemma,
    PartOfSpeech,
    Subject,
    Tense,
    Variant,
    Verb,
    VerbForm,
)


@dataclass
class BaseLemma:
    lemma_tag: Lemma

    @property
    def base_form(self) -> str:
        return self.lemma_tag.base_form

    @property
    def part_of_speech(self) -> PartOfSpeech:
        return self.lemma_tag.part_of_speech


@dataclass
class BaseElement:
    element_tag: Element

    @property
    def lemma_tag(self) -> Lemma:
        return self.element_tag.lemma

    @property
    def form(self) -> str:
        return self.element_tag.form

    @property
    def base_form(self) -> str:
        return self.lemma_tag.base_form

    @property
    def part_of_speech(self) -> PartOfSpeech:
        return self.lemma_tag.part_of_speech


@dataclass
class BaseVerb(BaseLemma):
    lemma_tag: Verb

    @property
    def is_reflexive(self) -> bool:
        return self.lemma_tag.is_reflexive

    @property
    def infinitive(self) -> str:
        return self.lemma_tag.infinitive

    @property
    def ending(self) -> str:
        return self.lemma_tag.ending


@dataclass
class BaseVerbForm(BaseElement):
    element_tag: VerbForm

    @property
    def lemma_tag(self) -> Verb:
        return self.element_tag.lemma

    @property
    def inflection(self) -> Inflection:
        return self.element_tag.inflection

    @property
    def tense(self) -> Tense:
        return self.element_tag.tense

    @property
    def subject(self) -> Subject:
        return self.element_tag.subject

    @property
    def subject_group(self) -> list[Subject]:
        return SUBJECT_GROUPS.get((self.tense, self.subject), [self.subject])

    @property
    def variant(self) -> Variant | None:
        return self.element_tag.variant


# fmt: off
# ruff: disable[E501]
SUBJECT_GROUPS = {
    (Tense.PRESENT, Subject.EL_ELLA): [Subject.EL_ELLA, Subject.USTED],
    (Tense.PRESENT, Subject.ELLOS_ELLAS): [Subject.ELLOS_ELLAS, Subject.USTEDES],
    (Tense.IMPERFECT, Subject.TU): [Subject.TU, Subject.VOS],
    (Tense.IMPERFECT, Subject.EL_ELLA): [Subject.YO, Subject.EL_ELLA, Subject.USTED],
    (Tense.IMPERFECT, Subject.ELLOS_ELLAS): [Subject.ELLOS_ELLAS, Subject.USTEDES],
    (Tense.PAST, Subject.TU): [Subject.TU, Subject.VOS],
    (Tense.PAST, Subject.EL_ELLA): [Subject.EL_ELLA, Subject.USTED],
    (Tense.PAST, Subject.ELLOS_ELLAS): [Subject.ELLOS_ELLAS, Subject.USTEDES],
    (Tense.FUTURE, Subject.TU): [Subject.TU, Subject.VOS],
    (Tense.FUTURE, Subject.EL_ELLA): [Subject.EL_ELLA, Subject.USTED],
    (Tense.FUTURE, Subject.ELLOS_ELLAS): [Subject.ELLOS_ELLAS, Subject.USTEDES],
    (Tense.CONDITIONAL, Subject.TU): [Subject.TU, Subject.VOS],
    (Tense.CONDITIONAL, Subject.EL_ELLA): [Subject.YO, Subject.EL_ELLA, Subject.USTED],
    (Tense.CONDITIONAL, Subject.ELLOS_ELLAS): [Subject.ELLOS_ELLAS, Subject.USTEDES],
    (Tense.SUBJUNCTIVE_PRESENT, Subject.TU): [Subject.TU, Subject.VOS],
    (Tense.SUBJUNCTIVE_PRESENT, Subject.EL_ELLA): [Subject.YO, Subject.EL_ELLA, Subject.USTED],
    (Tense.SUBJUNCTIVE_PRESENT, Subject.ELLOS_ELLAS): [Subject.ELLOS_ELLAS, Subject.USTEDES],
    (Tense.SUBJUNCTIVE_PAST, Subject.TU): [Subject.TU, Subject.VOS],
    (Tense.SUBJUNCTIVE_PAST, Subject.EL_ELLA): [Subject.YO, Subject.EL_ELLA, Subject.USTED],
    (Tense.SUBJUNCTIVE_PAST, Subject.ELLOS_ELLAS): [Subject.ELLOS_ELLAS, Subject.USTEDES],
    (Tense.SUBJUNCTIVE_FUTURE, Subject.TU): [Subject.TU, Subject.VOS],
    (Tense.SUBJUNCTIVE_FUTURE, Subject.EL_ELLA): [Subject.YO, Subject.EL_ELLA, Subject.USTED],
    (Tense.SUBJUNCTIVE_FUTURE, Subject.ELLOS_ELLAS): [Subject.ELLOS_ELLAS, Subject.USTEDES],
}
# ruff: enable[E501]
# fmt: on
