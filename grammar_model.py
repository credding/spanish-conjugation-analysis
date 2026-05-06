from collections.abc import Hashable
from dataclasses import dataclass, field
from enum import Enum
from typing import Self

from annotated_string import AnnotatedString


class OrderedEnum(Enum):
    def __lt__(self, other: Self) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        members = [*type(self)]
        return members.index(self) < members.index(other)


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
    base_form: str
    part_of_speech: PartOfSpeech

    @property
    def lemma_tag(self) -> LemmaTag:
        return LemmaTag(self.base_form, self.part_of_speech)


@dataclass
class Lemma(BaseLemma):
    dle_url: str = ""
    freq_adj: float = 0

    @property
    def tags(self) -> tuple[Hashable, ...]:
        return self.lemma_tag, self.part_of_speech


@dataclass(frozen=True, slots=True)
class ElementTag:
    lemma_tag: LemmaTag
    form: str

    @property
    def form_tag(self) -> FormTag:
        return FormTag(self.form)

    @property
    def part_of_speech(self) -> PartOfSpeech:
        return self.lemma_tag.part_of_speech


@dataclass(frozen=True, slots=True)
class FormTag:
    form: str


@dataclass
class BaseElement:
    lemma_tag: LemmaTag
    form: str

    @property
    def element_tag(self) -> ElementTag:
        return ElementTag(self.lemma_tag, self.form)

    @property
    def form_tag(self) -> FormTag:
        return FormTag(self.form)

    @property
    def part_of_speech(self) -> PartOfSpeech:
        return self.lemma_tag.part_of_speech


@dataclass
class Element(BaseElement):
    lemma: Lemma
    form: str
    annotated_form: AnnotatedString = field(init=False)

    def __post_init__(self) -> None:
        self.annotated_form = AnnotatedString(self.form)

    @property
    def tags(self) -> tuple[Hashable, ...]:
        return self.lemma_tag, self.part_of_speech, self.element_tag, self.form_tag


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
    part_of_speech: PartOfSpeech = field(
        default=PartOfSpeech.VERB, init=False, repr=False
    )

    @property
    def lemma_tag(self) -> VerbTag:
        return VerbTag(self.base_form)


@dataclass
class Verb(BaseVerb, Lemma):
    models: list[VerbTag] = field(default_factory=list)
    study_order: int | None = field(default=None)


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


@dataclass(frozen=True, slots=True)
class VerbFormTag(ElementTag):
    lemma_tag: VerbTag
    tense: Tense
    subject: Subject


@dataclass
class BaseVerbForm(BaseElement):
    lemma_tag: VerbTag
    tense: Tense
    subject: Subject

    @property
    def element_tag(self) -> VerbFormTag:
        return VerbFormTag(self.lemma_tag, self.form, self.tense, self.subject)


@dataclass
class VerbForm(BaseVerbForm, Element):
    lemma: Verb
    subject_group: list[Subject]
    variant: Variant | None
    preference: int
    alt_phonology: AnnotatedString | None = None

    @property
    def tags(self) -> tuple[Hashable, ...]:
        return *super().tags, self.tense, *self.subject_group, self.variant


class Regularity(OrderedEnum):
    MODEL_VERB = "verbo modelo"
    CORRECT_FORM = "forma correcta"
    INCORRECT_FORM = "forma incorrecta"
    REGULAR_MORPHOLOGY = "morfología regular"
    IRREGULAR_MORPHOLOGY = "morfología irregular"
    REGULAR_SPELLING = "ortografía regular"
    IRREGULAR_SPELLING = "ortografía irregular"
    REGULAR_SPELLING_CHANGE = "cambio ortográfico regular"
    CONSTRUCTED_FORM = "forma construida"
    REGULAR_CONSTRUCTION = "construcción regular"
    IRREGULAR_CONSTRUCTION = "construcción irregular"
