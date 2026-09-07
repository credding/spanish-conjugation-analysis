# SPDX-License-Identifier: GPL-3.0-or-later

import csv
from pathlib import Path

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

from .dle_model import DLELemma, DLEVerb, DLEVerbForm
from .resources import resources_path

TOP_LEMMAS_SEARCH_LIMIT = 5_000
TOP_ELEMENTS_FREQ_THRESHOLD = 10

dle_lemmas_name = "dle_lemmas.csv"
dle_lemmas_cols = [
    "lemma",
    "part_of_speech",
    "dle_lemma",
    "dle_url",
    "is_model_verb",
    "model_verbs",
]

dle_verb_forms_name = "dle_verb_forms.csv"
dle_verb_forms_cols = ["lemma", "tense", "subject", "variant", "form", "preference"]


def load_dle_lemmas() -> dict[Lemma, DLELemma]:
    dle_lemmas_path = resources_path / dle_lemmas_name
    with dle_lemmas_path.open(mode="r") as f:
        r = csv.DictReader(f, dialect=csv.unix_dialect)
        result: dict[Lemma, DLELemma] = {}
        for row in r:
            part_of_speech = PartOfSpeech(row["part_of_speech"])
            if part_of_speech is PartOfSpeech.VERB:
                lemma = Verb(row["lemma"])
                lemma_tag = Verb(row["dle_lemma"])
                dle_lemma = DLEVerb(
                    lemma_tag=lemma_tag,
                    dle_url=row["dle_url"],
                    is_model_verb=bool(int(row["is_model_verb"])),
                    model_verbs=(
                        [Verb(x) for x in row["model_verbs"].split(",")]
                        if row["model_verbs"]
                        else []
                    ),
                )
            else:
                lemma = Lemma(row["lemma"], part_of_speech)
                lemma_tag = Lemma(row["dle_lemma"], part_of_speech)
                dle_lemma = DLELemma(lemma_tag=lemma_tag, dle_url=row["dle_url"])

            result[lemma] = dle_lemma

        return result


def write_dle_lemmas(path: Path, dle_lemmas: dict[Lemma, DLELemma]) -> None:
    with (path / dle_lemmas_name).open(mode="w") as f:
        w = csv.DictWriter(f, fieldnames=dle_lemmas_cols, dialect=csv.unix_dialect)
        w.writeheader()
        for lemma, dle_lemma in dle_lemmas.items():
            if isinstance(dle_lemma, DLEVerb):
                w.writerow(
                    {
                        "lemma": lemma.base_form,
                        "part_of_speech": lemma.part_of_speech.value,
                        "dle_lemma": dle_lemma.base_form,
                        "dle_url": dle_lemma.dle_url,
                        "is_model_verb": int(dle_lemma.is_model_verb),
                        "model_verbs": ",".join(
                            x.base_form for x in dle_lemma.model_verbs
                        ),
                    }
                )
            else:
                w.writerow(
                    {
                        "lemma": lemma.base_form,
                        "part_of_speech": lemma.part_of_speech.value,
                        "dle_lemma": dle_lemma.base_form,
                        "dle_url": dle_lemma.dle_url,
                    }
                )


def load_dle_verb_forms() -> dict[Verb, list[DLEVerbForm]]:
    dle_verb_forms_path = resources_path / dle_verb_forms_name
    with dle_verb_forms_path.open(mode="r") as f:
        r = csv.DictReader(f, dialect=csv.unix_dialect)
        result: dict[Verb, list[DLEVerbForm]] = {}
        for row in r:
            verb = Verb(row["lemma"])
            if verb not in result:
                result[verb] = []
            result[verb].append(
                DLEVerbForm(
                    element_tag=VerbForm(
                        lemma=verb,
                        inflection=Inflection(
                            tense=Tense(row["tense"]),
                            subject=Subject(row["subject"]),
                            variant=Variant(row["variant"]) if row["variant"] else None,
                        ),
                        form=row["form"],
                    ),
                    preference=int(row["preference"]),
                )
            )

        return result


def write_dle_verb_forms(
    path: Path, dle_verb_forms: dict[Verb, list[DLEVerbForm]]
) -> None:
    with (path / dle_verb_forms_name).open(mode="w") as f:
        w = csv.DictWriter(f, fieldnames=dle_verb_forms_cols, dialect=csv.unix_dialect)
        w.writeheader()
        for verb_forms in dle_verb_forms.values():
            for form in verb_forms:
                w.writerow(
                    {
                        "lemma": form.base_form,
                        "tense": form.tense.value,
                        "subject": form.subject.value,
                        "variant": form.variant.value if form.variant else None,
                        "form": form.form,
                        "preference": form.preference,
                    }
                )
