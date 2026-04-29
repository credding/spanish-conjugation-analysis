import logging
import re

from dle_lemma import _get_dle_url
from dle_model import DLEVerb
from grammar_model import LemmaTag, VerbTag
from run_context import dle, memory

_logger = logging.getLogger(__name__)

_CONJUG_MODELO_PATTERN = re.compile(r"\bConjug\. modelo\b")
_CONJUG_C_PATTERN = re.compile(r"\bConjug\. c\. (\w+\b(?: o c\. \w+\b)*)")


@memory.cache
def get_verb(lemma_tag: LemmaTag) -> DLEVerb:
    _logger.info("fetching verb data for %s", lemma_tag)

    page = dle.get_page(lemma_tag.base_form)

    dle_url = _get_dle_url(page, lemma_tag)
    if dle_url is None:
        msg = f"could not find DLE url for {lemma_tag}"
        raise ValueError(msg)

    is_model = False
    models: list[VerbTag] = []

    for tag in page.document.find_all(class_="c-text-intro"):
        conjug_modelo = _CONJUG_MODELO_PATTERN.search(tag.get_text())
        if conjug_modelo is not None:
            is_model = True

        conjug_c = _CONJUG_C_PATTERN.search(tag.get_text())
        if conjug_c is not None:
            models.extend(VerbTag(x) for x in conjug_c.group(1).split(" o c. "))

    return DLEVerb(page.word, dle_url, is_model, models)
