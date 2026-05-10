import csv
import re
from dataclasses import dataclass
from typing import Any, NamedTuple

from .grammar_base_model import ConjugationTag, Subject, Tense, Variant, VerbTag
from .phonetic_analysis import TRANSLATE_ADD_STRESS
from .resources import resources_path


class _ConjugationSpecKey(NamedTuple):
    ending: str
    conjug_tag: ConjugationTag


@dataclass(frozen=True)
class ConjugationSpec:
    from_conjug: ConjugationTag | None
    truncate_str: str
    pre_affix_stress: bool
    affix: str
    subject_len: int | None
    full_affix_pattern: re.Pattern


def get_conjugation_spec(
    verb_tag: VerbTag, conjug_tag: ConjugationTag
) -> ConjugationSpec | None:
    spec_key = _ConjugationSpecKey(verb_tag.ending, conjug_tag)
    return _CONJUGATION_SPEC_LOOKUP.get(spec_key)


def _load_conjugation_spec_lookup() -> dict[_ConjugationSpecKey, ConjugationSpec]:
    rows = _read_conjugation_spec_rows()
    return {k: _build_conjugation_spec(rows, k, v) for k, v in rows.items()}


def _read_conjugation_spec_rows() -> dict[_ConjugationSpecKey, dict[str, Any]]:
    conjugation_data_path = resources_path / "regular_conjugation.csv"
    result: dict[_ConjugationSpecKey, dict[str, Any]] = {}
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
                    key = _ConjugationSpecKey(
                        ending, ConjugationTag(tense, subject, variant)
                    )
                    result[key] = row
    return result


def _build_conjugation_spec(
    rows: dict[_ConjugationSpecKey, dict[str, Any]],
    key: _ConjugationSpecKey,
    row: dict[str, Any],
) -> ConjugationSpec:
    from_conjug = (
        ConjugationTag(Tense(row["from_tense"]), Subject(row["from_subject"]), None)
        if row["from_tense"] or row["from_subject"]
        else None
    )
    truncate_str: str = row["truncate_str"].replace("_", key.ending[0])
    pre_affix_stress: bool = row["pre_affix_stress"] == "1"
    affix: str = row["affix"]
    if row["subject_len"]:
        subject_len = int(row["subject_len"])
        assert subject_len > 0  # noqa: S101
    else:
        subject_len = None

    if from_conjug is not None:
        from_ = _ConjugationSpecKey(key.ending, from_conjug)
        from_affix: str = rows[from_]["affix"]
        assert from_affix.endswith(truncate_str)  # noqa: S101
        from_affix = from_affix[: -len(truncate_str) or None]
    else:
        from_affix = ""

    if pre_affix_stress:
        from_affix = from_affix[:-1] + from_affix[-1].translate(TRANSLATE_ADD_STRESS)

    full_affix = from_affix + affix

    full_affix_pattern = _build_affix_pattern(full_affix)

    return ConjugationSpec(
        from_conjug=from_conjug,
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
