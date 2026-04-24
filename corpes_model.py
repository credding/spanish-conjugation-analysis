from dataclasses import InitVar, dataclass, field
from enum import StrEnum

from grammar_model import Class, Element, Lemma


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


@dataclass
class FreqElement:
    form: str
    lemma: str
    tag_str: InitVar[str]
    tag: Tag = field(init=False)
    freq: int
    freq_norm_with_punc: float
    freq_norm_without_punc: float

    def __post_init__(self, tag_str: str):
        self.tag = Tag(tag_str)

    @property
    def class_(self) -> Class:
        return self.tag.class_tag.class_

    def as_element(self) -> Element:
        return Element(Lemma(self.lemma, self.class_), self.form)


@dataclass
class FreqLemma:
    lemma: str
    class_str: InitVar[str]
    class_tag: ClassTag = field(init=False)
    freq: int
    freq_norm_with_punc: float
    freq_norm_without_punc: float

    def __post_init__(self, class_str: str):
        self.class_tag = ClassTag(class_str)

    @property
    def class_(self) -> Class:
        return self.class_tag.class_

    def as_lemma(self) -> Lemma:
        return Lemma(self.lemma, self.class_)


@dataclass
class FreqForm:
    form: str
    freq: int
    freq_norm: float


@dataclass
class DpLemma:
    lemma: str
    class_str: InitVar[str]
    class_tag: ClassTag = field(init=False)
    freq: int
    freq_norm: float
    dp: float
    num_countries: int
    freq_adj: float

    def __post_init__(self, class_str: str):
        self.class_tag = ClassTag(class_str)

    @property
    def class_(self) -> Class:
        return self.class_tag.class_

    def as_lemma(self) -> Lemma:
        return Lemma(self.lemma, self.class_)


class Tag(str):
    @property
    def class_tag(self) -> ClassTag:
        return ClassTag(self[0])
