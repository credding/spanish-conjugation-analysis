from abc import ABC
from dataclasses import dataclass, field
from enum import Enum
from functools import total_ordering
from typing import Any, Self

from annotated_string import AnnotatedString


@total_ordering
class _OrderedEnum(Enum):
    def __lt__(self, other: Self) -> bool:
        if not isinstance(other, type(self)):
            return NotImplemented
        members = [*type(self)]
        return members.index(self) < members.index(other)


class PartOfSpeech(_OrderedEnum):
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
class BaseLemma(ABC):
    base_form: str
    part_of_speech: PartOfSpeech

    @property
    def tag(self) -> LemmaTag:
        return LemmaTag(self.base_form, self.part_of_speech)


@dataclass
class Lemma(BaseLemma):
    freq_adj: float = 0

    @property
    def tags(self) -> tuple[Any, ...]:
        return self.tag, self.part_of_speech


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
class BaseElement(ABC):
    lemma_tag: LemmaTag
    form: str

    @property
    def part_of_speech(self) -> PartOfSpeech:
        return self.lemma_tag.part_of_speech

    @property
    def tag(self) -> ElementTag:
        return ElementTag(self.lemma_tag, self.form)


@dataclass
class Element(BaseElement):
    lemma: Lemma
    form: str
    annotated_form: AnnotatedString = field(init=False)

    def __post_init__(self) -> None:
        self.annotated_form = AnnotatedString(self.form)

    @property
    def tags(self) -> tuple[Any, ...]:
        return self.lemma_tag, self.part_of_speech, self.tag, self.tag.form_tag


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
class BaseVerb(BaseLemma, ABC):
    part_of_speech: PartOfSpeech = field(
        default=PartOfSpeech.VERB, init=False, repr=False
    )

    @property
    def tag(self) -> VerbTag:
        return VerbTag(self.base_form)


@dataclass
class Verb(BaseVerb, Lemma):
    models: list[VerbTag] = field(default_factory=list)
    study_order: int | None = field(default=None)


class Tense(_OrderedEnum):
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


class Subject(_OrderedEnum):
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


class Variant(_OrderedEnum):
    RA = "variante ‘ra’"  # noqa: RUF001
    SE = "variante ‘se’"  # noqa: RUF001


@dataclass(frozen=True, slots=True)
class VerbFormTag(ElementTag):
    lemma_tag: VerbTag
    tense: Tense
    subject: Subject


@dataclass
class BaseVerbForm(BaseElement, ABC):
    lemma_tag: VerbTag
    tense: Tense
    subject: Subject

    @property
    def tag(self) -> VerbFormTag:
        return VerbFormTag(self.lemma_tag, self.form, self.tense, self.subject)


@dataclass
class VerbForm(BaseVerbForm, Element):
    lemma: Verb
    subject_group: list[Subject]
    variant: Variant | None
    preference: int | None

    @property
    def tags(self) -> tuple[Any, ...]:
        return (
            *super().tags,
            self.tense,
            *self.subject_group,
            *((self.variant,) if self.variant else ()),
        )


class Regularity(_OrderedEnum):
    MODEL_VERB = "verbo modelo"
    REGULAR_VERB = "verbo regular"
    IRREGULAR_VERB = "verbo irregular"
    CORRECT_FORM = "forma correcta"
    INCORRECT_FORM = "forma incorrecta"
    SPELLING_CHANGE = "cambio ortográfico"
    REGULAR_FORM = "forma regular"
    IRREGULAR_FORM = "forma irregular"
    REGULAR_CONSTRUCTION = "construcción regular"
    IRREGULAR_CONSTRUCTION = "construcción irregular"
