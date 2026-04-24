import logging

from conjugation_analysis import (
    tag_correct_form,
    tag_form_construction,
    tag_form_regularity,
)
from dle_verb_forms import get_verb_forms
from dle_verbs import get_verb
from export_data import export_verbs_and_homonyms
from grammar_model import Class, Lemma
from phonetic_analysis import annotate_phonemes
from resources import artifacts_path, resources_path
from run_context import corpes, element_index
from spelling_analysis import tag_homonyms, tag_phonetic_spelling
from stress_analysis import annotate_stress
from syllable_analysis import annotate_syllables

_logger = logging.getLogger(__name__)


def main():
    _logger.info("querying top lemmas")
    top_dp_lemmas = corpes.get_top_lemmas_by_freq_adj(5000)

    _logger.info("querying top lemma elements")
    top_freq_elements = corpes.get_top_elements_by_lemma_freq_adj(5000)

    verb_lemmas = {x.as_lemma() for x in top_dp_lemmas if x.class_ is Class.VERB}
    kofi_verbs = (resources_path / "kofi_verbs.txt").read_text().splitlines()
    verb_lemmas.update(Lemma(x, Class.VERB) for x in kofi_verbs)

    _logger.info("fetching verb data")
    verbs = {get_verb(x) for x in verb_lemmas}
    model_verbs = {m for v in verbs for m in v.models}
    verbs.update(get_verb(x) for x in model_verbs - verbs)

    _logger.info("fetching verb forms")
    verb_forms = {f for v in verbs for f in get_verb_forms(v)}

    _logger.info("indexing correct verb forms")
    correct_forms = {tag_correct_form(x) for x in verb_forms}

    _logger.info("tagging form regularity")
    for correct_form in correct_forms:
        tag_form_regularity(correct_form)

    _logger.info("tagging form construction")
    for correct_form in correct_forms:
        tag_form_construction(correct_form)

    _logger.info("indexing top elements")
    for freq_element in top_freq_elements:
        if (
            freq_element.class_ is Class.VERB
            or not freq_element.form.isalpha()
            or not freq_element.form.islower()
        ):
            continue
        element_index.index_element(freq_element.as_element())

    _logger.info("annotating elements")
    for element in element_index.all_elements:
        annotate_phonemes(element.annotated_form)
        annotate_syllables(element.annotated_form)
        annotate_stress(element.annotated_form)

        tag_phonetic_spelling(element)

    _logger.info("tagging homonyms")
    for form in element_index.lookup(Class.VERB):
        for element in tag_homonyms(form):
            tag_homonyms(element)

    _logger.info("exporting verb and homonym data")
    export_data = export_verbs_and_homonyms()
    export_json = export_data.model_dump_json(ensure_ascii=False, exclude_defaults=True)
    (artifacts_path / "verb_data.json").write_text(export_json)

    _logger.info("done")


if __name__ == "__main__":
    main()
