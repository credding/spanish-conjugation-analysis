import logging

from joblib import Memory

from resources import obj_path
from conjugation import RegularConstructionConjugator, RegularFormConjugator
from corpes import CORPES
from dle_web import DLEWeb
from element_index import ElementIndex

logging.basicConfig(level=logging.INFO)

corpes = CORPES()
dle = DLEWeb()
element_index = ElementIndex()
regular_form_conjugator = RegularFormConjugator()
regular_construction_conjugator = RegularConstructionConjugator(element_index)

_cache_path = obj_path.joinpath("cache")
memory = Memory(location=_cache_path, verbose=0)
