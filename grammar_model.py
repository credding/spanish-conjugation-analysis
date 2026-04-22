from dataclasses import dataclass, field
from enum import Enum


class Class(Enum):
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


@dataclass(frozen=True)
class Lemma:
    base_form: str
    class_: Class


@dataclass(frozen=True)
class Element[T: Lemma]:
    form: str
    lemma: T

    @property
    def base_form(self) -> str:
        return self.lemma.base_form

    @property
    def class_(self) -> Class:
        return self.lemma.class_


@dataclass(frozen=True)
class Verb(Lemma):
    class_: Class = field(init=False, default=Class.VERB)
    models: list["Verb"] = field(compare=False, default_factory=list)

    @property
    def is_reflexive(self):
        return self.base_form.endswith("se")

    @property
    def infinitive(self) -> str:
        return self.base_form.removesuffix("se")

    @property
    def ending(self) -> str:
        return self.infinitive[-2:]


@dataclass(frozen=True)
class VerbForm(Element[Verb]):
    tense: Tense
    subject: Subject
    variant: Variant | None = field(compare=False)
    preference: int = field(compare=False)


class Tense(Enum):
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


class Subject(Enum):
    YO = "yo"
    TU = "tú"
    VOS = "vos"
    EL_ELLA = "él, ella"
    USTED = "usted"
    IMPERSONAL = "impersonal"
    NOSOTROS = "nosotros, nosotras"
    VOSOTROS = "vosotros, vosotras"
    ELLOS_ELLAS = "ellos, ellas"
    USTEDES = "ustedes"


class Variant(Enum):
    RA = "variante ‘ra’"
    SE = "variante ‘se’"


class Regularity(Enum):
    CORRECT_FORM = "forma correcta"
    INCORRECT_FORM = "forma incorrecta"
    SPELLING_CHANGE = "cambio ortográfico"
    REGULAR_FORM = "forma regular"
    IRREGULAR_FORM = "forma irregular"
    REGULAR_CONSTRUCTION = "construcción regular"
    IRREGULAR_CONSTRUCTION = "construcción irregular"
