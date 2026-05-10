import math

from pydantic import (
    AliasGenerator,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_serializer,
)
from pydantic.alias_generators import to_camel

from .conjugation_analysis import Regularity
from .grammar_base_model import PartOfSpeech, Subject, Tense, Variant
from .homonymy_analysis import Homonymy


class ExportData(BaseModel):
    lemmas: list[ExportLemma]
    elements: list[ExportElement]


class ExportLemma(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(serialization_alias=to_camel),
        serialize_by_alias=True,
        polymorphic_serialization=True,
    )

    lemma: str
    part_of_speech: PartOfSpeech
    dle_url: HttpUrl
    freq_adj: float = Field(gt=0)

    @field_serializer("freq_adj")
    def serialize_freq_adj(self, freq_adj: float) -> float:
        return round(freq_adj, 6 - math.ceil(math.log10(freq_adj)))


class ExportVerb(ExportLemma):
    models: list[str] = Field(default_factory=list)
    study_order: int | None = Field(default=None, gt=0)
    regularity: list[Regularity] = Field(default_factory=list)
    homonymy: list[Homonymy] = Field(default_factory=list)


class ExportElementId(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(serialization_alias=to_camel),
        serialize_by_alias=True,
        polymorphic_serialization=True,
    )

    lemma: str
    part_of_speech: PartOfSpeech
    form: str

    def __lt__(self, other: ExportElementId) -> bool:
        if not isinstance(other, ExportElementId):
            return NotImplemented
        a = (self.lemma, self.part_of_speech, self.form)
        b = (other.lemma, other.part_of_speech, other.form)
        return a < b


class ExportElement(ExportElementId):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(serialization_alias=to_camel),
        serialize_by_alias=True,
        polymorphic_serialization=True,
    )

    syllables: list[int]
    stress_pos: int

    homonymy: list[Homonymy] = Field(default_factory=list)
    heteronymous_forms: list[ExportElementId] = Field(default_factory=list)
    shared_forms: list[ExportElementId] = Field(default_factory=list)
    homographs: list[ExportElementId] = Field(default_factory=list)
    homophones: list[ExportElementId] = Field(default_factory=list)
    heteronyms: list[ExportElementId] = Field(default_factory=list)
    paronyms: list[ExportElementId] = Field(default_factory=list)


class ExportVerbFormId(ExportElementId):
    tense: Tense
    subject: Subject

    def __lt__(self, other: ExportElementId) -> bool:
        if not isinstance(other, ExportVerbFormId):
            return super().__lt__(other)
        a = (self.lemma, self.part_of_speech, self.tense, self.subject, self.form)
        b = (other.lemma, other.part_of_speech, other.tense, other.subject, other.form)
        return a < b


class ExportVerbForm(ExportVerbFormId, ExportElement):
    subject_group: list[Subject]
    variant: Variant | None = None
    preference: int

    affix_range: tuple[int, int]
    subject_range: tuple[int, int] | None = None
    variant_range: tuple[int, int] | None = None

    regularity: list[Regularity]
    regular_spelling: ExportVerbFormId | None = None
    regular_morphology: ExportVerbFormId | None = None
    regular_construction: ExportVerbFormId | None = None

    irregularities: list[ExportIrregularity] = Field(default_factory=list)


class ExportIrregularity(BaseModel):
    regularity: Regularity
    range: tuple[int, int]
    from_form: str
