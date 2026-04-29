import logging
from typing import cast

import conjugation_analysis
import phonetic_analysis
import spelling_analysis
import stress_analysis
import syllable_analysis
from dle_verb_forms import get_verb_forms
from dle_verbs import get_verb
from export_data import export_verb_forms_and_homonyms
from grammar_model import PartOfSpeech, Regularity, Verb, VerbForm, VerbTag
from resources import artifacts_path, resources_path
from run_context import (
    corpes,
    element_index,
    lemma_index,
    regular_construction_conjugator,
    regular_form_conjugator,
)

_logger = logging.getLogger(__name__)


def main() -> None:
    index_top_corpes_lemmas()
    index_top_corpes_elements()

    index_dpd_model_verbs()
    index_kofi_verbs()
    index_dle_model_verbs()

    index_dle_verb_forms()

    index_regular_forms()
    analyze_irregular_affixes()

    index_regular_constructions()
    annotate_irregular_forms()
    annotate_irregular_constructions()

    analyze_element_phonetics()
    tag_shared_forms()
    tag_verb_homonyms()

    export_verb_data()

    _logger.info("done")


def index_top_corpes_lemmas() -> None:
    _logger.info("indexing top CORPES lemmas")

    top_lemmas = corpes.get_top_lemmas_by_freq_adj(5000)
    for freq_lemma in top_lemmas:
        if freq_lemma.part_of_speech is PartOfSpeech.VERB:
            dle_verb = get_verb(freq_lemma.tag)
            tagged_lemma = lemma_index.setdefault(dle_verb.tag, dle_verb.as_verb())
            if dle_verb.is_model:
                tagged_lemma.tag(Regularity.MODEL_VERB)
        else:
            tagged_lemma = lemma_index.setdefault(freq_lemma.tag, freq_lemma.as_lemma())

        lemma = tagged_lemma.value
        lemma.freq_adj = freq_lemma.freq_adj
        tagged_lemma.tag(*lemma.tags)


def index_top_corpes_elements() -> None:
    _logger.info("indexing top CORPES elements")

    for tagged_lemma in lemma_index.lookup() - lemma_index.lookup(PartOfSpeech.VERB):
        for freq_element in corpes.get_top_elements(tagged_lemma.key):
            tagged_element = element_index.setdefault(
                freq_element.tag, freq_element.as_element(tagged_lemma.value)
            )

            element = tagged_element.value
            tagged_element.tag(*element.tags)


def index_dpd_model_verbs() -> None:
    _logger.info("indexing DPD model verbs")

    for verb in _index_verb_list("dpd_model_verbs.txt"):
        lemma_index[verb.tag].tag(Regularity.MODEL_VERB)


def index_kofi_verbs() -> None:
    _logger.info("indexing KOFI verbs")

    for i, verb in enumerate(_index_verb_list("kofi_verbs.txt")):
        verb.study_order = i + 1


def _index_verb_list(list_name: str) -> list[Verb]:
    verb_list = (resources_path / list_name).read_text().splitlines()

    result = []
    for verb_item in verb_list:
        freq_lemma = corpes.get_lemma(VerbTag(verb_item))
        dle_verb = get_verb(VerbTag(verb_item))
        tagged_verb = lemma_index.setdefault(dle_verb.tag, dle_verb.as_verb())

        verb = cast("Verb", tagged_verb.value)
        verb.freq_adj = freq_lemma.freq_adj
        tagged_verb.tag(*verb.tags)
        if dle_verb.is_model:
            tagged_verb.tag(Regularity.MODEL_VERB)

        result.append(verb)

    return result


def index_dle_model_verbs() -> None:
    _logger.info("indexing DLE model verbs")

    model_verbs = {
        m
        for v in lemma_index.lookup(PartOfSpeech.VERB)
        for m in cast("Verb", v.value).models
    }
    for verb_tag in model_verbs:
        freq_lemma = corpes.get_lemma(verb_tag)
        tagged_verb = lemma_index.setdefault(verb_tag, Verb(verb_tag.base_form))

        verb = tagged_verb.value
        verb.freq_adj = freq_lemma.freq_adj
        tagged_verb.tag(*verb.tags, Regularity.MODEL_VERB)


def index_dle_verb_forms() -> None:
    _logger.info("indexing DLE verb forms")

    for tagged_verb in lemma_index.lookup(PartOfSpeech.VERB):
        verb = cast("Verb", tagged_verb.value)
        for dle_form in get_verb_forms(verb.tag):
            tagged_element = element_index.setdefault(
                dle_form.tag, dle_form.as_verb_form(verb)
            )

            form = cast("VerbForm", tagged_element.value)
            tagged_element.tag(*form.tags, Regularity.CORRECT_FORM)


def index_regular_forms() -> None:
    _logger.info("indexing regular verb forms")

    for tagged_form in element_index.lookup(Regularity.CORRECT_FORM):
        conjugation_analysis.index_regular_forms(
            cast("VerbForm", tagged_form.value),
            regular_form_conjugator,
            Regularity.REGULAR_FORM,
        )


def analyze_irregular_affixes() -> None:
    _logger.info("analyzing irregular affixes")

    for tagged_form in element_index.lookup(
        Regularity.CORRECT_FORM
    ) - element_index.lookup(Regularity.REGULAR_FORM):
        conjugation_analysis.annotate_irregular_affix(
            cast("VerbForm", tagged_form.value)
        )


def index_regular_constructions() -> None:
    _logger.info("indexing regular verb form constructions")

    for tagged_form in element_index.lookup(Regularity.CORRECT_FORM):
        conjugation_analysis.index_regular_forms(
            cast("VerbForm", tagged_form.value),
            regular_construction_conjugator,
            Regularity.REGULAR_CONSTRUCTION,
        )


def annotate_irregular_forms() -> None:
    _logger.info("annotating irregular verb forms")

    for tagged_form in element_index.lookup(Regularity.CORRECT_FORM):
        conjugation_analysis.annotate_irregular_form(
            cast("VerbForm", tagged_form.value)
        )

    for tagged_verb in lemma_index.lookup(PartOfSpeech.VERB) - lemma_index.lookup(
        Regularity.IRREGULAR_VERB
    ):
        tagged_verb.tag(Regularity.REGULAR_VERB)


def annotate_irregular_constructions() -> None:
    _logger.info("annotating irregular verb form constructions")

    for tagged_form in element_index.lookup(Regularity.CORRECT_FORM):
        conjugation_analysis.annotate_irregular_construction(
            cast("VerbForm", tagged_form.value)
        )


def analyze_element_phonetics() -> None:
    _logger.info("analyzing element phonetics")

    for tagged_element in element_index.lookup():
        key, element = tagged_element.key, tagged_element.value
        phonetic_analysis.annotate_phonemes(element.annotated_form)
        syllable_analysis.annotate_syllables(element.annotated_form)
        stress_analysis.annotate_stress(element.annotated_form)

        spelling_analysis.tag_phonetic_spelling(key)


def tag_shared_forms() -> None:
    _logger.info("tagging shared forms")

    for tagged_element in element_index.lookup():
        spelling_analysis.tag_shared_forms(tagged_element.key)


def tag_verb_homonyms() -> None:
    _logger.info("tagging verb homonyms")

    for tagged_form in element_index.lookup(PartOfSpeech.VERB):
        for tag in spelling_analysis.tag_homonyms(tagged_form.key):
            if tag.part_of_speech is PartOfSpeech.VERB:
                continue
            spelling_analysis.tag_homonyms(tag)


def export_verb_data() -> None:
    _logger.info("exporting verb data")

    export_data = export_verb_forms_and_homonyms()
    export_json = export_data.model_dump_json(ensure_ascii=False, exclude_defaults=True)
    (artifacts_path / "verb_data.json").write_text(export_json)


if __name__ == "__main__":
    main()
