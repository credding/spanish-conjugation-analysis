from grammar_index import ElementIndex, LemmaIndex, TaggedElement
from ordered_enum import OrderedEnum
from regularity_analysis import Regularity


class Homonymy(OrderedEnum):
    HETERONYMOUS_FORM = "forma heterónima"
    SHARED_FORM = "forma compartida"
    HOMONYM = "homónimo"
    HOMOGRAPH = "homógrafo"
    HOMOPHONE = "homófono"
    HETERONYM = "heterónimo"
    PARONYM = "parónimo"


class HomonymAnalyzer:
    def __init__(self, lemma_index: LemmaIndex, element_index: ElementIndex) -> None:
        self._element_index = element_index
        self._lemma_index = lemma_index

    def tag_heteronymous_forms(self, form: TaggedElement) -> None:
        heteronymous_forms = (
            self._element_index.lookup(form.value.graphic_form_no_stress)
            .intersection_tags(Regularity.CORRECT_FORM, form.value.lemma_tag)
            .difference_tags(form.value.graphic_form)
        )

        if len(heteronymous_forms) > 0:
            form.tag(Homonymy.HETERONYMOUS_FORM)

        for x in heteronymous_forms:
            form.relate_to(x, Homonymy.HETERONYMOUS_FORM)

    def tag_shared_forms(self, form: TaggedElement) -> None:
        shared_forms = (
            self._element_index.lookup(form.value.graphic_form)
            .intersection_tags(Regularity.CORRECT_FORM, form.value.part_of_speech)
            .difference_tags(form.value.lemma_tag)
        )

        if len(shared_forms) > 0:
            form.tag(Homonymy.SHARED_FORM)
            if Regularity.CORRECT_FORM in form.tags:
                self._lemma_index[form.value.lemma_tag].tag(Homonymy.SHARED_FORM)

        for x in shared_forms:
            form.relate_to(x, Homonymy.SHARED_FORM)

    def tag_homonyms(self, element: TaggedElement) -> set[TaggedElement]:
        homonym_elements = (
            self._element_index.lookup(element.value.phonetic_form_no_stress)
            .intersection_tags(Regularity.CORRECT_FORM)
            .difference_tags(element.value.part_of_speech)
        )

        if len(homonym_elements) > 0:
            element.tag(Homonymy.HOMONYM)
            if Regularity.CORRECT_FORM in element.tags:
                self._lemma_index[element.value.lemma_tag].tag(Homonymy.HOMONYM)

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
