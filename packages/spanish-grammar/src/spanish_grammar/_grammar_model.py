# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from dataclasses import dataclass, field
from functools import total_ordering

from ordered_enum import OrderedEnum


class PartOfSpeech(OrderedEnum):
    ADJECTIVE = "adjetivo"
    ADVERB = "adverbio"
    AFFIX = "afjio"
    ARTICLE = "artículo"
    CONJUNCTION = "conjunión"
    CONTRACTION = "contracción"
    QUANTIFIER = "cuantificador"
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
class Lemma:
    base_form: str
    part_of_speech: PartOfSpeech


@dataclass(frozen=True, slots=True)
class Element:
    lemma: Lemma
    form: str

    @property
    def base_form(self) -> str:
        return self.lemma.base_form

    @property
    def part_of_speech(self) -> PartOfSpeech:
        return self.lemma.part_of_speech


@dataclass(frozen=True, slots=True)
class Verb(Lemma):
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


@dataclass(frozen=True, slots=True)
class VerbForm(Element):
    lemma: Verb
    inflection: Inflection

    @property
    def tense(self) -> Tense:
        return self.inflection.tense

    @property
    def subject(self) -> Subject:
        return self.inflection.subject

    @property
    def variant(self) -> Variant | None:
        return self.inflection.variant


@dataclass(frozen=True, slots=True)
@total_ordering
class Inflection:
    tense: Tense
    subject: Subject
    variant: Variant | None

    def __lt__(self, other: Inflection) -> bool:
        a = (self.tense, self.subject, self.variant is not None, self.variant)
        b = (other.tense, other.subject, other.variant is not None, other.variant)
        return a < b  # ty:ignore[unsupported-operator]


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
