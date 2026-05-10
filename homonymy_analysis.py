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
        heteronymous_forms = self._index.lookup_elements(
            Regularity.CORRECT_FORM,
            form.value.lemma_tag,
            form.value.graphic_form_no_stress,
        )
        heteronymous_forms -= {
            x for x in heteronymous_forms if form.value.graphic_form in x.tags
        }

        if len(heteronymous_forms) > 0:
            form.tag(Homonymy.HETERONYMOUS_FORM)

        for x in heteronymous_forms:
            form.relate_to(x, Homonymy.HETERONYMOUS_FORM)

    def tag_shared_forms(self, form: TaggedElement) -> None:
        shared_forms = self._index.lookup_elements(
            Regularity.CORRECT_FORM, form.value.part_of_speech, form.value.graphic_form
        )
        shared_forms -= {x for x in shared_forms if form.value.lemma_tag in x.tags}

        if len(shared_forms) == 0:
            return

        form.tag(Homonymy.SHARED_FORM)
        if Regularity.CORRECT_FORM in form.tags:
            self._index.lemmas[form.value.lemma_tag].tag(Homonymy.SHARED_FORM)

        for x in shared_forms:
            form.relate_to(x, Homonymy.SHARED_FORM)

    def tag_homonyms(self, element: TaggedElement) -> set[TaggedElement]:
        homonyms = self._index.lookup_elements(
            Regularity.CORRECT_FORM, element.value.phonetic_form_no_stress
        )
        homonyms -= {x for x in homonyms if element.value.part_of_speech in x.tags}

        if len(homonyms) == 0:
            return set()

        element.tag(Homonymy.HOMONYM)
        if Regularity.CORRECT_FORM in element.tags:
            self._index.lemmas[element.value.lemma_tag].tag(Homonymy.HOMONYM)

        for homonym in homonyms:
            if element.value.graphic_form in homonym.tags:
                element.tag(Homonymy.HOMOGRAPH)
                element.relate_to(homonym, Homonymy.HOMOGRAPH)
            elif element.value.phonetic_form in homonym.tags:
                element.tag(Homonymy.HOMOPHONE)
                element.relate_to(homonym, Homonymy.HOMOPHONE)
            elif element.value.graphic_form_no_stress in homonym.tags:
                element.tag(Homonymy.HETERONYM)
                element.relate_to(homonym, Homonymy.HETERONYM)
            elif element.value.phonetic_form_no_stress in homonym.tags:
                element.tag(Homonymy.PARONYM)
                element.relate_to(homonym, Homonymy.PARONYM)

        return homonyms
