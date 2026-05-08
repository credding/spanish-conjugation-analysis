from conjugation_analysis import Regularity
from grammar_index import GrammarIndex, TaggedElement
from ordered_enum import OrderedEnum


class Homonymy(OrderedEnum):
    HETERONYMOUS_FORM = "forma heterónima"
    SHARED_FORM = "forma compartida"
    HOMONYM = "homónimo"
    HOMOGRAPH = "homógrafo"
    HOMOPHONE = "homófono"
    HETERONYM = "heterónimo"
    PARONYM = "parónimo"


class HomonymyAnalyzer:
    def __init__(self, index: GrammarIndex) -> None:
        self._index = index

    def tag_heteronymous_forms(self, form: TaggedElement) -> None:
        heteronymous_forms = (
            self._index.lookup_elements(form.value.graphic_form_no_stress)
            .intersection_tags(Regularity.CORRECT_FORM, form.value.lemma_tag)
            .difference_tags(form.value.graphic_form)
        )

        if len(heteronymous_forms) > 0:
            form.tag(Homonymy.HETERONYMOUS_FORM)

        for x in heteronymous_forms:
            form.relate_to(x, Homonymy.HETERONYMOUS_FORM)

    def tag_shared_forms(self, form: TaggedElement) -> None:
        shared_forms = (
            self._index.lookup_elements(form.value.graphic_form)
            .intersection_tags(Regularity.CORRECT_FORM, form.value.part_of_speech)
            .difference_tags(form.value.lemma_tag)
        )

        if len(shared_forms) > 0:
            form.tag(Homonymy.SHARED_FORM)
            if Regularity.CORRECT_FORM in form.tags:
                self._index.lemmas[form.value.lemma_tag].tag(Homonymy.SHARED_FORM)

        for x in shared_forms:
            form.relate_to(x, Homonymy.SHARED_FORM)

    def tag_homonyms(self, element: TaggedElement) -> set[TaggedElement]:
        homonym_elements = (
            self._index.lookup_elements(element.value.phonetic_form_no_stress)
            .intersection_tags(Regularity.CORRECT_FORM)
            .difference_tags(element.value.part_of_speech)
        )

        if len(homonym_elements) > 0:
            element.tag(Homonymy.HOMONYM)
            if Regularity.CORRECT_FORM in element.tags:
                self._index.lemmas[element.value.lemma_tag].tag(Homonymy.HOMONYM)

        for homonym_element in homonym_elements:
            if element.value.graphic_form in homonym_element.tags:
                element.relate_to(homonym_element, Homonymy.HOMOGRAPH)
            elif element.value.phonetic_form in homonym_element.tags:
                element.relate_to(homonym_element, Homonymy.HOMOPHONE)
            elif element.value.graphic_form_no_stress in homonym_element.tags:
                element.relate_to(homonym_element, Homonymy.HETERONYM)
            else:
                element.relate_to(homonym_element, Homonymy.PARONYM)

        return homonym_elements
