from pydantic import AliasGenerator, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from grammar_model import Class, Regularity, Subject, Tense, Variant


class ExportData(BaseModel):
    lemmas: list[ExportLemma]
    elements: list[ExportElement]


class ExportLemma(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(serialization_alias=to_camel),
        serialize_by_alias=True,
        polymorphic_serialization=True,
    )

    class_: Class = Field(serialization_alias="class")
    lemma: str
    freq_adj: float


class ExportVerb(ExportLemma):
    models: list[str]


class ExportElementId(BaseModel):
    model_config = ConfigDict(
        alias_generator=AliasGenerator(serialization_alias=to_camel),
        serialize_by_alias=True,
        polymorphic_serialization=True,
    )

    class_: Class = Field(serialization_alias="class")
    lemma: str
    form: str


class ExportVerbFormId(ExportElementId):
    tense: Tense
    subject: Subject


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
    start_offset: int
    end_offset: int
    from_form: str
