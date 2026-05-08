from dataclasses import dataclass, field

from ordered_enum import OrderedEnum


class PartOfSpeech(OrderedEnum):
    ADJECTIVE = "adjetivo"
    ADVERB = "adverbio"
    AFFIX = "afjio"
    ARTICLE = "artículo"
    CONJUNCTION = "conjunión"
    CONTRACTION = "contracción"
    QUANTIFIER = "quantificador"
    DEMONSTRATIVE = "demonstrativo"
    UNKNOWN = "desconocido"
    FOREIGN = "extranjerismo"
    INTERJECTION = "interjección"
    INTERROGATIVE = "interrogativo"
    NUMERAL = "numeral"
    POSSESSIVE = "posesivo"
    PREPOSITION = "preposición"
    PERSONAL_PRONOUN = "pronombre personal"
    PUNCTUATION = "puntuación"
    RELATIVE = "relativo"
    NOUN = "sustantivo"
    VERB = "verbo"


@dataclass(frozen=True, slots=True)
class LemmaTag:
    base_form: str
    part_of_speech: PartOfSpeech


@dataclass
class BaseLemma:
    lemma_tag: LemmaTag

    @property
    def base_form(self) -> str:
        return self.lemma_tag.base_form

    @property
    def part_of_speech(self) -> PartOfSpeech:
        return self.lemma_tag.part_of_speech


@dataclass(frozen=True, slots=True)
class ElementTag:
    lemma_tag: LemmaTag
    form: str

    @property
    def base_form(self) -> str:
        return self.lemma_tag.base_form

    @property
    def part_of_speech(self) -> PartOfSpeech:
        return self.lemma_tag.part_of_speech


@dataclass
class BaseElement:
    element_tag: ElementTag

    @property
    def lemma_tag(self) -> LemmaTag:
        return self.element_tag.lemma_tag

    @property
    def form(self) -> str:
        return self.element_tag.form

    @property
    def base_form(self) -> str:
        return self.lemma_tag.base_form

    @property
    def part_of_speech(self) -> PartOfSpeech:
        return self.lemma_tag.part_of_speech


@dataclass(frozen=True, slots=True)
class VerbTag(LemmaTag):
    part_of_speech: PartOfSpeech = field(
        default=PartOfSpeech.VERB, init=False, repr=False
    )

    @property
    def is_reflexive(self) -> bool:
        return self.base_form.endswith("se")

    @property
    def infinitive(self) -> str:
        return self.base_form.removesuffix("se")

    @property
    def ending(self) -> str:
        return self.infinitive[-2:]


@dataclass
class BaseVerb(BaseLemma):
    lemma_tag: VerbTag

    @property
    def is_reflexive(self) -> bool:
        return self.lemma_tag.is_reflexive

    @property
    def infinitive(self) -> str:
        return self.lemma_tag.infinitive

    @property
    def ending(self) -> str:
        return self.lemma_tag.ending


@dataclass(frozen=True, slots=True)
class ConjugationTag:
    tense: Tense
    subject: Subject
    variant: Variant | None


@dataclass(frozen=True, slots=True)
class VerbFormTag(ElementTag):
    lemma_tag: VerbTag
    conjug_tag: ConjugationTag

    @property
    def tense(self) -> Tense:
        return self.conjug_tag.tense

    @property
    def subject(self) -> Subject:
        return self.conjug_tag.subject

    @property
    def variant(self) -> Variant | None:
        return self.conjug_tag.variant


@dataclass
class BaseVerbForm(BaseElement):
    element_tag: VerbFormTag

    @property
    def lemma_tag(self) -> VerbTag:
        return self.element_tag.lemma_tag

    @property
    def conjug_tag(self) -> ConjugationTag:
        return self.element_tag.conjug_tag

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


class Tense(OrderedEnum):
    INFINITIVE = "infinitivo"
    GERUND = "gerundio"
    PARTICIPLE = "participio"
    PRESENT = "presente"
    IMPERFECT = "imperfecto"
    PAST = "pretérito"
    FUTURE = "futuro"
    CONDITIONAL = "condicional"
    SUBJUNCTIVE_PRESENT = "subjuntivo presente"
    SUBJUNCTIVE_PAST = "subjuntivo pretérito"
    SUBJUNCTIVE_FUTURE = "subjuntivo futuro"
    IMPERATIVE = "imperativo"


class Subject(OrderedEnum):
    YO = "yo"
    TU = "tú"
    VOS = "vos"
    USTED = "usted"
    EL_ELLA = "él, ella"
    IMPERSONAL = "impersonal"
    NOSOTROS = "nosotros, nosotras"
    VOSOTROS = "vosotros, vosotras"
    USTEDES = "ustedes"
    ELLOS_ELLAS = "ellos, ellas"


class Variant(OrderedEnum):
    RA = "variante ‘ra’"  # noqa: RUF001
    SE = "variante ‘se’"  # noqa: RUF001


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
