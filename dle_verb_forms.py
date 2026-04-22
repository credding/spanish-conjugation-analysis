import logging
import re
from typing import Iterable, cast

from bs4 import Tag

from grammar_model import Subject, Tense, Variant, Verb, VerbForm
from run_context import dle, memory
from phonetic_analysis import TRANSLATE_ADD_STRESS, TRANSLATE_REMOVE_STRESS

_logger = logging.getLogger(__name__)

_TENSES = {
    ("Formas-no-personales", "Infinitivo"): Tense.INFINITIVE,
    ("Formas-no-personales", "Gerundio"): Tense.GERUND,
    ("Formas-no-personales", "Participio"): Tense.PARTICIPLE,
    ("Indicativo", "Presente"): Tense.PRESENT,
    ("Indicativo", "Pretérito imperfecto / Copretérito"): Tense.IMPERFECT,
    ("Indicativo", "Pretérito perfecto simple / Pretérito"): Tense.PAST,
    ("Indicativo", "Futuro simple / Futuro"): Tense.FUTURE,
    ("Indicativo", "Condicional simple / Pospretérito"): Tense.CONDITIONAL,
    ("Subjuntivo", "Presente"): Tense.SUBJUNCTIVE_PRESENT,
    ("Subjuntivo", "Pretérito imperfecto / Pretérito"): Tense.SUBJUNCTIVE_PAST,
    ("Subjuntivo", "Futuro simple / Futuro"): Tense.SUBJUNCTIVE_FUTURE,
    ("Imperativo", "Imperativo"): Tense.IMPERATIVE,
}
_FORM_DELIM_PATTERN = re.compile(r" o | u |, |/")
_FORM_PATTERN = re.compile(r"([\w ]+?)(?: \((\w+): ([\w ]+)\))?")

_REFLEXIVE_PRONOUNS = {
    Subject.YO: "me",
    Subject.TU: "te",
    Subject.VOS: "te",
    Subject.USTED: "se",
    Subject.IMPERSONAL: "se",
    Subject.EL_ELLA: "se",
    Subject.NOSOTROS: "nos",
    Subject.VOSOTROS: "os",
    Subject.ELLOS_ELLAS: "se",
    Subject.USTEDES: "se",
}


@memory.cache
def get_verb_forms(verb: Verb) -> list[VerbForm]:
    _logger.info("Fetching verb forms for %s", verb)

    page = dle.get_page(verb.base_form)

    verb_forms: list[VerbForm] = []

    conjugation_anchor = page.document.find(attrs={"name": "conjugacion"})
    if not conjugation_anchor:
        raise Exception("Missing conjugation section")

    conjugation_section = conjugation_anchor.find_parent("section")
    if not conjugation_section:
        raise Exception("Missing conjugation section")

    for mood_group in conjugation_section.find_all(class_="c-collapse"):
        mood_id: str = cast(str, mood_group["id"])
        for table_tag in mood_group.find_all("table"):
            verb_forms.extend(_parse_conjugation_table(verb, mood_id, table_tag))

    return verb_forms


def _parse_conjugation_table(
    verb: Verb, mood_id: str, table: Tag
) -> Iterable[VerbForm]:
    table_norm = _normalize_table(table)

    col_headers: dict[int, str] = {}

    for row in table_norm:
        row_header: str | None = None

        seen: set[Tag] = set()
        for col_idx, cell_tag in enumerate(row):
            if cell_tag in seen:
                continue
            seen.add(cell_tag)
            match cell_tag.name:
                case "th":
                    header_text = cell_tag.get_text()
                    col_headers[col_idx] = header_text
                    row_header = header_text

                case "td":
                    tense_name = col_headers.get(col_idx)
                    if not tense_name:
                        continue

                    tense = _TENSES.get((mood_id, tense_name))
                    if not tense:
                        continue

                    form_text = cell_tag.get_text()
                    if not row_header:
                        for form in _parse_form(
                            verb, tense, Subject.IMPERSONAL, form_text
                        ):
                            yield form
                        continue

                    subjects = [Subject(x) for x in row_header.split(" / ")]
                    subject_forms = form_text.split(" / ")

                    for _ in range(len(subject_forms), len(subjects)):
                        subject_forms.append(subject_forms[0])

                    for subject, subject_form in zip(subjects, subject_forms):
                        for form in _parse_form(verb, tense, subject, subject_form):
                            yield form


def _normalize_table(table: Tag) -> list[list[Tag]]:
    row_tags = table.find_all("tr")

    result = [[] for _ in row_tags]

    for row_pos, row_tag in enumerate(row_tags):
        col_pos = 0

        for cell_tag in row_tag.find_all(["th", "td"]):
            rowspan = int(cast(str, cell_tag.get("rowspan", "1")))
            colspan = int(cast(str, cell_tag.get("colspan", "1")))

            for cell in result[row_pos][col_pos:]:
                if cell is None:
                    break
                col_pos += 1

            for row in result[row_pos : min(row_pos + rowspan, len(result))]:
                for _ in range(len(row), col_pos):
                    row.append(None)
                for i in range(col_pos, min(col_pos + colspan, len(row))):
                    row[i] = cell_tag
                for _ in range(len(row), col_pos + colspan):
                    row.append(cell_tag)

            col_pos += colspan

    return result


def _parse_form(
    verb: Verb, tense: Tense, subject: Subject, form: str
) -> Iterable[VerbForm]:
    for i, form in enumerate(_FORM_DELIM_PATTERN.split(form)):
        form_parts = _FORM_PATTERN.fullmatch(form)

        if not form_parts:
            raise Exception(f"Could not parse verb form {form}")

        if tense == Tense.SUBJUNCTIVE_PAST:
            if i % 2 == 0:
                variant = Variant.RA
            else:
                variant = Variant.SE
            preference = i // 2
        else:
            variant = None
            preference = i

        form = remove_reflexive_pronoun(verb, form_parts[1], tense, subject)
        yield VerbForm(
            lemma=verb,
            form=form,
            tense=tense,
            subject=subject,
            variant=variant,
            preference=preference,
        )

        if form_parts[2]:
            subject = Subject(form_parts[2])
            form = remove_reflexive_pronoun(verb, form_parts[3], tense, subject)
            yield VerbForm(
                lemma=verb,
                form=form,
                tense=tense,
                subject=subject,
                variant=None,
                preference=0,
            )


def remove_reflexive_pronoun(
    verb: Verb, form: str, tense: Tense, subject: Subject
) -> str:
    if not verb.is_reflexive:
        return form

    pronoun = _REFLEXIVE_PRONOUNS[subject]
    match tense, subject:
        case Tense.INFINITIVE, _:
            return form.removesuffix(pronoun)
        case Tense.PARTICIPLE, _:
            return form
        case Tense.IMPERATIVE, Subject.VOS:
            form = form.removesuffix(pronoun)
            return form [:-1] + form[-1].translate(TRANSLATE_ADD_STRESS)
        case Tense.IMPERATIVE, Subject.VOSOTROS:
            return form.removesuffix(pronoun).translate(TRANSLATE_REMOVE_STRESS) + "d"
        case Tense.GERUND | Tense.IMPERATIVE, _:
            return form.removesuffix(pronoun).translate(TRANSLATE_REMOVE_STRESS)
        case _:
            return form.removeprefix(f"{pronoun} ")
