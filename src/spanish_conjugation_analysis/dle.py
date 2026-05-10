import logging
import re
from collections.abc import Iterable
from pathlib import Path
from typing import cast
from urllib.parse import quote

import joblib
from bs4 import Tag
from spanish_grammar import (
    Inflection,
    Lemma,
    PartOfSpeech,
    Subject,
    Tense,
    Variant,
    Verb,
    VerbForm,
)
from spanish_phonology.phonetics import TRANSLATE_ADD_STRESS, TRANSLATE_REMOVE_STRESS

from .dle_model import DLELemma, DLEVerb, DLEVerbForm
from .dle_web import DLEPage, DLEWeb
from .grammar_base_model import SUBJECT_GROUPS

_logger = logging.getLogger(__name__)


class DLE:
    def __init__(self, dle_web: DLEWeb, cache_dir: Path | None = None) -> None:
        self._dle_web = dle_web

        memory = joblib.Memory(cache_dir, verbose=0)
        self._get_lemma = memory.cache(_get_lemma)
        self._get_verb = memory.cache(_get_verb)
        self._get_verb_forms = memory.cache(_get_verb_forms)

    def get_lemma(self, lemma: Lemma) -> DLELemma | None:
        page = self._dle_web.get_page(lemma.base_form)
        return self._get_lemma(page, lemma)

    def get_verb(self, verb: Verb) -> DLEVerb:
        page = self._dle_web.get_page(verb.base_form)
        return self._get_verb(page, verb)

    def get_verb_forms(self, verb: Verb) -> list[DLEVerbForm]:
        page = self._dle_web.get_page(verb.base_form)
        return self._get_verb_forms(page, verb)


_PART_OF_SPEECH_ABBRS = {
    PartOfSpeech.ADJECTIVE: ["adj."],
    PartOfSpeech.ADVERB: ["adv."],
    PartOfSpeech.AFFIX: ["suf.", "pref."],
    PartOfSpeech.ARTICLE: ["art."],
    PartOfSpeech.CONJUNCTION: ["conj."],
    PartOfSpeech.CONTRACTION: ["contracc."],
    PartOfSpeech.QUANTIFIER: ["adj."],
    PartOfSpeech.DEMONSTRATIVE: ["adj. dem.", "pron. dem."],
    PartOfSpeech.INTERJECTION: ["interj."],
    PartOfSpeech.INTERROGATIVE: ["adj. interrog.", "pron. interrog."],
    PartOfSpeech.NUMERAL: ["m.", "f."],
    PartOfSpeech.POSSESSIVE: ["adj. poses.", "pron. poses."],
    PartOfSpeech.PREPOSITION: ["prep."],
    PartOfSpeech.PERSONAL_PRONOUN: ["pron. person."],
    PartOfSpeech.RELATIVE: ["adj. relat.", "pron. relat."],
    PartOfSpeech.NOUN: ["m.", "f."],
    PartOfSpeech.VERB: ["aux.", "copulat.", "impers.", "intr.", "prnl.", "tr."],
}

_NUMERAL_PATTERN = re.compile(r"^\d+. ")


def _get_lemma(page: DLEPage, lemma: Lemma) -> DLELemma | None:
    _logger.info("parsing lemma data for %s", lemma)

    dle_url = _get_dle_url(page, lemma)
    if dle_url is None:
        return None

    lemma = Lemma(lemma.base_form, lemma.part_of_speech)
    return DLELemma(lemma, dle_url)


def _get_dle_url(page: DLEPage, lemma: Lemma) -> str | None:
    article_id = _find_article_id(page, lemma)
    if article_id is None:
        return None

    return f"{page.url}#{quote(article_id)}"


def _find_article_id(page: DLEPage, lemma: Lemma) -> str | None:
    abbrs = _PART_OF_SPEECH_ABBRS[lemma.part_of_speech]

    for tag in page.document.find_all(class_="c-definitions__item"):
        def_text = _NUMERAL_PATTERN.sub("", tag.get_text())

        for abbr in abbrs:
            if def_text.startswith(abbr):
                article = tag.find_parent("article")
                if article is None:
                    msg = f"missing article for {lemma}"
                    raise ValueError(msg)

                article_id = article["id"]
                if not isinstance(article_id, str):
                    msg = f"invalid article id for {lemma}"
                    raise ValueError(msg)

                return article_id

    return None


_CONJUG_MODELO_PATTERN = re.compile(r"\bConjug\. modelo\b")
_CONJUG_C_PATTERN = re.compile(r"\bConjug\.(?: actual)? c\. (\w+\b(?: o c\. \w+\b)*)")


def _get_verb(page: DLEPage, verb: Verb) -> DLEVerb:
    _logger.info("parsing verb data for %s", verb)

    dle_url = _get_dle_url(page, verb)
    if dle_url is None:
        msg = f"could not find DLE url for {verb}"
        raise ValueError(msg)

    is_model_verb = False
    model_verbs: list[Verb] = []

    for tag in page.document.find_all(class_="c-text-intro"):
        conjug_modelo = _CONJUG_MODELO_PATTERN.search(tag.get_text())
        if conjug_modelo is not None:
            is_model_verb = True

        conjug_c = _CONJUG_C_PATTERN.search(tag.get_text())
        if conjug_c is not None:
            model_verbs.extend(Verb(x) for x in conjug_c.group(1).split(" o c. "))

    verb = Verb(page.word)
    return DLEVerb(verb, dle_url, is_model_verb, model_verbs)


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

_REDUNDANT_SUBJECTS = {
    (tense, extra_subject)
    for (tense, subject), subjects in SUBJECT_GROUPS.items()
    for extra_subject in subjects
    if extra_subject != subject
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


def _get_verb_forms(page: DLEPage, verb: Verb) -> list[DLEVerbForm]:
    _logger.info("parsing verb forms for %s", verb)

    verb_forms: list[DLEVerbForm] = []

    conjugation_anchor = page.document.find(attrs={"name": "conjugacion"})
    if conjugation_anchor is None:
        msg = "missing conjugation section"
        raise ValueError(msg)

    conjugation_section = conjugation_anchor.find_parent("section")
    if conjugation_section is None:
        msg = "missing conjugation section"
        raise ValueError(msg)

    for mood_group in conjugation_section.find_all(class_="c-collapse"):
        mood_id: str = cast("str", mood_group["id"])
        for table_tag in mood_group.find_all("table"):
            verb_forms.extend(_parse_conjugation_table(verb, mood_id, table_tag))

    return verb_forms


def _parse_conjugation_table(
    verb: Verb, mood_id: str, table: Tag
) -> Iterable[DLEVerbForm]:
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
                    if header_text != "":
                        col_headers[col_idx] = header_text
                        row_header = header_text

                case "td":
                    col_header = col_headers.get(col_idx)
                    if col_header is not None:
                        yield from _parse_conjugation_cell(
                            verb, mood_id, col_header, row_header, cell_tag.get_text()
                        )


def _parse_conjugation_cell(
    verb: Verb, mood_id: str, col_header: str, row_header: str | None, cell_text: str
) -> Iterable[DLEVerbForm]:
    tense = _TENSES.get((mood_id, col_header))
    if tense is None:
        return

    if row_header is None:
        subjects = [Subject.IMPERSONAL]
    else:
        subjects = [Subject(x) for x in row_header.split(" / ")]

    subject_forms = cell_text.split(" / ")
    subject_forms += subject_forms[:1] * (len(subjects) - len(subject_forms))

    for subject, subject_form in zip(subjects, subject_forms, strict=True):
        if (tense, subject) not in _REDUNDANT_SUBJECTS:
            yield from _parse_form(verb, tense, subject, subject_form)


def _normalize_table(table: Tag) -> list[list[Tag]]:
    row_tags = table.find_all("tr")

    result = [[] for _ in row_tags]

    for row_pos, row_tag in enumerate(row_tags):
        col_pos = 0

        for cell_tag in row_tag.find_all(["th", "td"]):
            rowspan = int(cast("str", cell_tag.get("rowspan", "1")))
            colspan = int(cast("str", cell_tag.get("colspan", "1")))

            for cell in result[row_pos][col_pos:]:
                if cell is None:
                    break
                col_pos += 1

            for row in result[row_pos : row_pos + rowspan]:
                row.extend([None] * (col_pos - len(row)))
                row[col_pos : col_pos + colspan] = [cell_tag] * colspan

            col_pos += colspan

    return result


def _parse_form(
    verb: Verb, tense: Tense, subject: Subject, forms_text: str
) -> Iterable[DLEVerbForm]:
    for i, form_text in enumerate(_FORM_DELIM_PATTERN.split(forms_text)):
        form_parts = _FORM_PATTERN.fullmatch(form_text)
        if form_parts is None:
            msg = f"could not parse verb form {form_text}"
            raise ValueError(msg)

        if tense == Tense.SUBJUNCTIVE_PAST:
            variant = Variant.RA if i % 2 == 0 else Variant.SE
            preference = i // 2
        else:
            variant = None
            preference = i

        form = _remove_reflexive_pronoun(verb, form_parts[1], tense, subject)
        form_tag = VerbForm(verb, form, Inflection(tense, subject, variant))
        yield DLEVerbForm(form_tag, preference)

        if form_parts[2]:
            subject = Subject(form_parts[2])

            form = _remove_reflexive_pronoun(verb, form_parts[3], tense, subject)
            form_tag = VerbForm(verb, form, Inflection(tense, subject, None))
            yield DLEVerbForm(form_tag, 0)


def _remove_reflexive_pronoun(
    verb: Verb, form: str, tense: Tense, subject: Subject
) -> str:
    if not verb.is_reflexive:
        return form

    pronoun = _REFLEXIVE_PRONOUNS[subject]
    match tense, subject:
        case Tense.INFINITIVE, _:
            form = form.removesuffix(pronoun)
        case Tense.PARTICIPLE, _:
            pass
        case Tense.IMPERATIVE, Subject.VOS:
            form = form.removesuffix(pronoun)
            form = form[:-1] + form[-1].translate(TRANSLATE_ADD_STRESS)
        case Tense.IMPERATIVE, Subject.VOSOTROS:
            form = form.removesuffix(pronoun).translate(TRANSLATE_REMOVE_STRESS) + "d"
        case Tense.GERUND | Tense.IMPERATIVE, _:
            form = form.removesuffix(pronoun).translate(TRANSLATE_REMOVE_STRESS)
        case _:
            form = form.removeprefix(f"{pronoun} ")

    return form
