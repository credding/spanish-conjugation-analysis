# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass

from .grammar_base_model import BaseLemma, BaseVerb, BaseVerbForm, Verb


@dataclass
class DLELemma(BaseLemma):
    dle_url: str


@dataclass
class DLEVerb(BaseVerb, DLELemma):
    is_model_verb: bool
    model_verbs: list[Verb]


@dataclass
class DLEVerbForm(BaseVerbForm):
    preference: int
