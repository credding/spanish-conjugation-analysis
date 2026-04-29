from functools import total_ordering

from pydantic import AliasGenerator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from grammar_model import PartOfSpeech, Regularity, Subject, Tense, Variant


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
    freq_adj: float


class ExportVerb(ExportLemma):
    regularity: list[Regularity] = Field(default_factory=list)
    models: list[str] = Field(default_factory=list)
    study_order: int | None = None


@total_ordering
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


class ExportVerbFormId(ExportElementId):
    tense: Tense
    subject: Subject

    def __lt__(self, other: ExportElementId) -> bool:
        if not isinstance(other, ExportVerbFormId):
            return super().__lt__(other)
        a = (self.lemma, self.part_of_speech, self.tense, self.subject, self.form)
        b = (other.lemma, other.part_of_speech, other.tense, other.subject, other.form)
        return a < b


class ExportElement(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(serialization_alias=to_camel),
        serialize_by_alias=True,
        polymorphic_serialization=True,
    )

    id: ExportElementId

    syllables: list[int]
    stress_pos: int

    shared_forms: list[ExportElementId] = Field(default_factory=list)
    homographs: list[ExportElementId] = Field(default_factory=list)
    homophones: list[ExportElementId] = Field(default_factory=list)
    heteronyms: list[ExportElementId] = Field(default_factory=list)
    paronyms: list[ExportElementId] = Field(default_factory=list)


class ExportVerbForm(ExportElement):
    id: ExportVerbFormId

    subject_group: list[Subject]
    variant: Variant | None = None
    preference: int | None = None

    affix_range: tuple[int, int]
    subject_range: tuple[int, int] | None = None
    variant_range: tuple[int, int] | None = None

    regularity: list[Regularity]
    regular_form: ExportVerbFormId | None = None
    regular_construction: ExportVerbFormId | None = None

    spelling_change: FormChange | None = None
    form_change: FormChange | None = None
    construction_change: FormChange | None = None


class FormChange(BaseModel):
    range: tuple[int, int]
    from_form: str
