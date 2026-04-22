from conjugation_analysis import (
    tag_correct_form,
    tag_form_construction,
    tag_form_regularity,
)
from dle_verb_forms import get_verb_forms
from dle_verbs import get_verb
from grammar_model import Class, Lemma, Regularity, VerbForm
from phonetic_analysis import annotate_phonemes
from resources import resources_path
from run_context import corpes, element_index
from spelling_analysis import tag_homonyms, tag_phonetic_spelling
from stress_analysis import annotate_stress
from syllable_analysis import annotate_syllables


def main():
    top_dp_lemmas = corpes.get_top_lemmas_by_freq_adj(5000)
    top_freq_elements = corpes.get_top_elements_by_lemma_freq_adj(5000)
    kofi_verbs = resources_path.joinpath("kofi_verbs.txt").read_text().splitlines()

    verb_lemmas = {x.as_lemma() for x in top_dp_lemmas if x.class_ is Class.VERB}
    verb_lemmas.update(Lemma(x, Class.VERB) for x in kofi_verbs)

    verbs = [get_verb(x) for x in verb_lemmas]
    model_verbs = {m for v in verbs for m in v.models}
    verbs.extend(get_verb(x) for x in model_verbs.difference(verbs))

    verb_forms = [f for v in verbs for f in get_verb_forms(v)]

    for form in verb_forms:
        tag_correct_form(form)

    for freq_element in top_freq_elements:
        if freq_element.class_ is Class.VERB or not freq_element.form.islower():
            continue
        element_index.index_element(freq_element.as_element())

    for correct_form in element_index.lookup(VerbForm, Regularity.CORRECT_FORM):
        tag_form_regularity(correct_form)

    for correct_form in element_index.lookup(VerbForm, Regularity.CORRECT_FORM):
        tag_form_construction(correct_form)

    for form in (
        element_index.lookup(Regularity.REGULAR_FORM)
        | element_index.lookup(Regularity.REGULAR_CONSTRUCTION)
    ) - element_index.lookup(Regularity.CORRECT_FORM):
        form.tag(Regularity.INCORRECT_FORM)

    for element in element_index.lookup():
        annotate_phonemes(element.annotated_form)
        annotate_syllables(element.annotated_form)
        annotate_stress(element.annotated_form)

        tag_phonetic_spelling(element)

    for element in element_index.lookup():
        tag_homonyms(element)

    pass


if __name__ == "__main__":
    main()
