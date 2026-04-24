import logging
import re

from grammar_model import Lemma, Verb
from run_context import dle, memory

_logger = logging.getLogger(__name__)

_CONJUG_C_PATTERN = re.compile(r"Conjug\. c\. (\w+\b(?: o c\. \w+\b)*)")


@memory.cache
def get_verb(verb: Lemma) -> Verb:
    _logger.info("fetching verb data for %s", verb)

    page = dle.get_page(verb.base_form)

    models: list[Verb] = []

    for tag in page.document.find_all(class_="c-text-intro"):
        conjug_c = _CONJUG_C_PATTERN.search(tag.get_text())
        if conjug_c is None:
            continue
        for model_verb in conjug_c.group(1).split(" o c. "):
            models.append(Verb(model_verb))

    return Verb(page.word, models)
