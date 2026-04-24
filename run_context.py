import logging

from joblib import Memory

from conjugation import (
    RegularConstructionConjugator,
    RegularFormConjugator,
    VerbConjugator,
)
from corpes import CORPES
from dle_web import DLEWeb
from element_index import ElementIndex
from resources import obj_path

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

corpes = CORPES()
dle = DLEWeb()
element_index = ElementIndex()
regular_form_conjugator: VerbConjugator = RegularFormConjugator()
regular_construction_conjugator: VerbConjugator = RegularConstructionConjugator(
    element_index
)

_cache_path = obj_path / "cache"
memory = Memory(location=_cache_path, verbose=0)
