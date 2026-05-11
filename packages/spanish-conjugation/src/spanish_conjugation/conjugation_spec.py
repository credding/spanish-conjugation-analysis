import csv
import re
from dataclasses import dataclass
from importlib.resources import files
from typing import Any, NamedTuple, cast

from spanish_grammar import Inflection, Subject, Tense, Variant, Verb
from spanish_phonology.phonetics import TRANSLATE_ADD_STRESS


class _ConjugationSpecKey(NamedTuple):
    ending: str
    inflection: Inflection


@dataclass(frozen=True)
class ConjugationSpec:
    base_form: Inflection
    truncate_str: str
    pre_affix_stress: bool
    affix: str
    subject_len: int | None
    full_affix_pattern: re.Pattern


def get_conjugation_spec(
    verb_tag: Verb, inflection: Inflection
) -> ConjugationSpec | None:
    spec_key = _ConjugationSpecKey(verb_tag.ending, inflection)
    return _CONJUGATION_SPEC_LOOKUP.get(spec_key)


def _load_conjugation_spec_lookup() -> dict[_ConjugationSpecKey, ConjugationSpec]:
    rows = _read_conjugation_spec_rows()
    return {k: _build_conjugation_spec(rows, k, v) for k, v in rows.items()}


def _read_conjugation_spec_rows() -> dict[_ConjugationSpecKey, dict[str, Any]]:
    conjugation_data_path = files(cast("str", __package__)) / "regular_conjugation.csv"
    result: dict[_ConjugationSpecKey, dict[str, Any]] = {}
    with conjugation_data_path.open("r") as f:
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
                        ending, Inflection(tense, subject, variant)
                    )
                    result[key] = row
    return result


def _build_conjugation_spec(
    rows: dict[_ConjugationSpecKey, dict[str, Any]],
    key: _ConjugationSpecKey,
    row: dict[str, Any],
) -> ConjugationSpec:
    base_form = Inflection(Tense(row["base_tense"]), Subject(row["base_subject"]), None)
    truncate_str: str = row["truncate_str"].replace("_", key.ending[0])
    pre_affix_stress: bool = row["pre_affix_stress"] == "1"
    affix: str = row["affix"]
    if row["subject_len"]:
        subject_len = int(row["subject_len"])
        assert subject_len > 0  # noqa: S101
    else:
        subject_len = None

    if base_form is not None:
        base_spec = _ConjugationSpecKey(key.ending, base_form)
        base_affix: str = rows[base_spec]["affix"]
        assert base_affix.endswith(truncate_str)  # noqa: S101
        base_affix = base_affix[: -len(truncate_str) or None]
    else:
        base_affix = ""

    if pre_affix_stress:
        base_affix = base_affix[:-1] + base_affix[-1].translate(TRANSLATE_ADD_STRESS)

    full_affix = base_affix + affix

    full_affix_pattern = _build_affix_pattern(full_affix)

    return ConjugationSpec(
        base_form=base_form,
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
