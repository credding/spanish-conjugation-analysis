import csv
import re
from dataclasses import dataclass
from typing import Any

from grammar_model import Subject, Tense, Variant, VerbTag
from phonetic_analysis import TRANSLATE_ADD_STRESS
from resources import resources_path


@dataclass(frozen=True, slots=True)
class _ConjugationKey:
    ending: str
    tense: Tense
    subject: Subject
    variant: Variant | None


@dataclass(frozen=True)
class ConjugationSpec:
    from_tense: Tense | None
    from_subject: Subject | None
    truncate_str: str
    pre_affix_stress: bool
    affix: str
    subject_len: int | None
    full_affix_pattern: re.Pattern


def get_conjugation_spec(
    verb_tag: VerbTag, tense: Tense, subject: Subject, variant: Variant | None
) -> ConjugationSpec | None:
    spec_key = _ConjugationKey(verb_tag.ending, tense, subject, variant)
    return _CONJUGATION_SPEC_LOOKUP.get(spec_key)


def _load_conjugation_spec_lookup() -> dict[_ConjugationKey, ConjugationSpec]:
    rows = _read_conjugation_spec_rows()
    return {k: _build_conjugation_spec(rows, k, v) for k, v in rows.items()}


def _read_conjugation_spec_rows() -> dict[_ConjugationKey, dict[str, Any]]:
    conjugation_data_path = resources_path / "regular_conjugation.csv"
    result: dict[_ConjugationKey, dict[str, Any]] = {}
    with conjugation_data_path.open("r", newline="") as f:
        for row in csv.DictReader(f, dialect=csv.unix_dialect):
            tense = Tense(row["tense"])
            subjects = (
                tuple(Subject(x) for x in row["subjects"].split(";"))
                if row["subjects"]
                else None
            )
            variant = Variant(row["variant"]) if row["variant"] else None
            for ending in row["endings"].split(";"):
                for subject in subjects or [Subject.IMPERSONAL]:
                    key = _ConjugationKey(
                        ending=ending, tense=tense, subject=subject, variant=variant
                    )
                    result[key] = row
    return result


def _build_conjugation_spec(
    rows: dict[_ConjugationKey, dict[str, Any]],
    key: _ConjugationKey,
    row: dict[str, Any],
) -> ConjugationSpec:
    from_tense = Tense(row["from_tense"]) if row["from_tense"] else None
    from_subject = Subject(row["from_subject"]) if row["from_subject"] else None
    truncate_str: str = row["truncate_str"].replace("_", key.ending[0])
    pre_affix_stress: bool = row["pre_affix_stress"] == "1"
    affix: str = row["affix"]
    if row["subject_len"]:
        subject_len = int(row["subject_len"])
        assert subject_len > 0  # noqa: S101
    else:
        subject_len = None

    if from_tense is not None:
        assert from_subject is not None  # noqa: S101
        from_key = _ConjugationKey(key.ending, from_tense, from_subject, None)
        from_affix: str = rows[from_key]["affix"]
        assert from_affix.endswith(truncate_str)  # noqa: S101
        from_affix = from_affix[: -len(truncate_str) or None]
    else:
        assert from_subject is None  # noqa: S101
        from_affix = ""

    if pre_affix_stress:
        from_affix = from_affix[:-1] + from_affix[-1].translate(TRANSLATE_ADD_STRESS)

    full_affix = from_affix + affix

    full_affix_pattern = _build_affix_pattern(full_affix)

    return ConjugationSpec(
        from_tense=from_tense,
        from_subject=from_subject,
        truncate_str=truncate_str,
        pre_affix_stress=pre_affix_stress,
        affix=affix,
        subject_len=subject_len,
        full_affix_pattern=full_affix_pattern,
    )


_I_PATTERN = r"[iíy]?"
_VERB_CONSONANT_PATTERN = r"[aáeéíioó]+[^aáeéiíoó]*"
_AFFIX_START_PATTERN = re.compile(rf"^({_I_PATTERN}){_VERB_CONSONANT_PATTERN}")


def _build_affix_pattern(affix: str) -> re.Pattern:
    affix_start_match = _AFFIX_START_PATTERN.search(affix)
    assert affix_start_match is not None  # noqa: S101

    affix_pattern = _VERB_CONSONANT_PATTERN + affix[affix_start_match.end() :] + "$"
    if affix_start_match.group(1):
        affix_pattern = _I_PATTERN + affix_pattern

    return re.compile(affix_pattern)


_CONJUGATION_SPEC_LOOKUP = _load_conjugation_spec_lookup()
