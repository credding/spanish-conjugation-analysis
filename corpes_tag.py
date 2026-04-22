from enum import StrEnum

from grammar_model import Class


class ClassTag(StrEnum):
    ADJECTIVE = "A", Class.ADJECTIVE
    ADVERB = "R", Class.ADVERB
    AFFIX = "J", Class.AFFIX
    ARTICLE = "T", Class.ARTICLE
    CONJUNCTION = "C", Class.CONJUNCTION
    CONTRACTION = "E", Class.CONTRACTION
    QUANTIFIER = "Q", Class.QUANTIFIER
    DEMONSTRATIVE = "D", Class.DEMONSTRATIVE
    UNKNOWN = "U", Class.UNKNOWN
    FOREIGN = "F", Class.FOREIGN
    INTERJECTION = "I", Class.INTERJECTION
    INTERROGATIVE = "W", Class.INTERROGATIVE
    NUMERAL = "M", Class.NUMERAL
    POSSESSIVE = "X", Class.POSSESSIVE
    PREPOSITION = "P", Class.PREPOSITION
    PERSONAL_PRONOUN = "L", Class.PERSONAL_PRONOUN
    PUNCTUATION = "Y", Class.PUNCTUATION
    RELATIVE = "H", Class.RELATIVE
    NOUN = "N", Class.NOUN
    VERB = "V", Class.VERB

    def __new__(cls, value: str, _: Class):
        obj = str.__new__(cls, value)
        obj._value_ = value
        return obj

    def __init__(self, _: str, class_: Class):
        self.class_ = class_


class Gender(StrEnum):
    COMMON = "c"
    FEMININE = "f"
    MASCULINE = "m"
    FEMININE_OR_MASCULINE_OR_NEUTER = "e"
    NEUTER = "n"


class Mood(StrEnum):
    IMPERATIVE = "p"
    INDICATIVE = "i"
    SUBJUNCTIVE = "s"


class Number(StrEnum):
    PLURAL = "p"
    SINGULAR = "s"
    SINGULAR_OR_PLURAL = "i"


class AdverbType(StrEnum):
    AFFIRMATIVE = "a"
    DEICTIC = "d"
    INTENSIFIER = "i"
    INTERROGATIVE = "u"
    NEGATIVE = "n"
    RELATIVE = "r"


class ConjunctionType(StrEnum):
    COORDINATE = "o"
    SUBORDINATE = "b"


class NumeralType(StrEnum):
    CARDINAL = "k"
    ORDINAL = "l"
    PARTITIVE = "s"


class NounType(StrEnum):
    COMMON = "c"
    PROPER = "p"


class TenseVariant(StrEnum):
    RA = "h"
    SE = "s"


class Tense(StrEnum):
    CONDITIONAL_COMPOUND = "w"
    CONDITIONAL_SIMPLE = "c"
    FUTURE_COMPOUND = "q"
    FUTURE_SIMPLE = "f"
    GERUND_COMPOUND = "x"
    GERUND_SIMPLE = "g"
    INFINITIVE_COMPOUND = "y"
    INFINITIVE_SIMPLE = "v"
    PAST_PARTICIPLE = "d"
    PRESENT = "p"
    PAST_ANTERIOR = "m"
    PAST_IMPERFECT_SIMPLE = "i"
    PAST_PERFECT_COMPOUND = "j"
    PAST_PERFECT_SIMPLE = "t"
    PAST_IMPERFECT_COMPOUND = "k"


class Person(StrEnum):
    FIRST = "1"
    SECOND = "2"
    THIRD = "3"


class Case(StrEnum):
    ACCUSATIVE = "a"
    DATIVE = "o"
    ACCUSATIVE_OR_DATIVE = "n"
    PREPOSITIONAL = "e"
    REFLEXIVE = "r"


class Possessor(StrEnum):
    PLURAL = "l"
    SINGULAR = "s"
    PLURAL_OR_SINGULAR = "b"


class Degree(StrEnum):
    COMPARATIVE = "c"
    POSITIVE = "p"
    SUPERLATIVE = "s"


class Definiteness(StrEnum):
    DEFINITE = "a"
    INDEFINITE = "i"


class Function(StrEnum):
    DETERMINER = "d"
    HEAD = "r"


class Tag(str):
    @property
    def class_tag(self) -> ClassTag:
        return ClassTag(self[0])

    @property
    def gender(self) -> Gender:
        return Gender(self[1])

    @property
    def mood(self) -> Mood:
        return Mood(self[1])

    @property
    def number(self) -> Number:
        return Number(self[2])

    @property
    def adverb_type(self) -> AdverbType:
        return AdverbType(self[3])

    @property
    def conjunction_type(self) -> ConjunctionType:
        return ConjunctionType(self[3])

    @property
    def numeral_type(self) -> NumeralType:
        return NumeralType(self[3])

    @property
    def noun_type(self) -> NounType:
        return NounType(self[3])

    @property
    def tense_variant(self) -> TenseVariant:
        return TenseVariant(self[3])

    @property
    def person(self) -> Person:
        return Person(self[4])

    @property
    def possessor(self) -> Possessor:
        return Possessor(self[5])

    @property
    def case(self) -> Case:
        return Case(self[5])

    @property
    def tense(self) -> Tense:
        return Tense(self[5])

    @property
    def degree(self) -> Degree:
        return Degree(self[6])

    @property
    def definiteness(self) -> Definiteness:
        return Definiteness(self[6])

    @property
    def function(self) -> Function:
        return Function(self[6])
