import logging
import re
from dataclasses import dataclass

from grammar_model import BaseVerb, LemmaTag, Verb, VerbTag
from run_context import dle, memory

_logger = logging.getLogger(__name__)

_CONJUG_MODELO_PATTERN = re.compile(r"\bConjug\. modelo\b")
_CONJUG_C_PATTERN = re.compile(r"\bConjug\. c\. (\w+\b(?: o c\. \w+\b)*)")


@dataclass
class DLEVerb(BaseVerb):
    is_model: bool
    models: list[VerbTag]

    def as_verb(self) -> Verb:
        return Verb(self.base_form, models=self.models)


@memory.cache
def get_verb(lemma_tag: LemmaTag) -> DLEVerb:
    _logger.info("fetching verb data for %s", lemma_tag)

    page = dle.get_page(lemma_tag.base_form)

    is_model = False
    models: list[VerbTag] = []

    for tag in page.document.find_all(class_="c-text-intro"):
        conjug_modelo = _CONJUG_MODELO_PATTERN.search(tag.get_text())
        if conjug_modelo is not None:
            is_model = True

        conjug_c = _CONJUG_C_PATTERN.search(tag.get_text())
        if conjug_c is not None:
            for model_verb in conjug_c.group(1).split(" o c. "):
                models.append(VerbTag(model_verb))

    return DLEVerb(page.word, is_model, models)
