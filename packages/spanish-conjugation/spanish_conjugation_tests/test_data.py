import csv
from importlib.resources import files
from typing import NamedTuple, cast

from annotated_string import AnnotatedString
from spanish_grammar import Subject, Tense, Variant
from spanish_phonology import annotate_phonemes

__test__ = False


class TestVerbForm(NamedTuple):
    form: str
    verb: str
    tense: Tense
    subject: Subject
    variant: Variant | None
    annotated_form: AnnotatedString


def _load_test_data(name: str) -> list[TestVerbForm]:
    data_path = files(cast("str", __package__)) / name
    with data_path.open("r") as f:
        reader = csv.DictReader(
            f,
            dialect=csv.unix_dialect,
            fieldnames=["verb", "tense", "subject", "variant", "form"],
        )

        result = []
        for row in reader:
            annotated_form = AnnotatedString(row["form"])
            annotate_phonemes(annotated_form)
            result.extend(
                TestVerbForm(
                    form=row["form"],
                    verb=row["verb"],
                    tense=Tense(row["tense"]),
                    subject=Subject(subject),
                    variant=Variant(row["variant"]) if row["variant"] else None,
                    annotated_form=annotated_form,
                )
                for subject in row["subject"].split(";")
            )

        return result


CORRECT_REGULAR_SPELLING_FORMS = _load_test_data("correct_regular_spelling_forms.csv")

INCORRECT_REGULAR_SPELLING_FORMS = _load_test_data(
    "incorrect_regular_spelling_forms.csv"
)

CORRECT_REGULAR_MORPHOLOGY_FORMS = _load_test_data(
    "correct_regular_morphology_forms.csv"
)
