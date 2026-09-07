# SPDX-License-Identifier: GPL-3.0-or-later

from spanish_grammar import Verb

from .resources import resources_path


def get_verb_list(list_name: str) -> list[Verb]:
    return [
        Verb(base_form)
        for base_form in (resources_path / list_name).read_text().splitlines()
        if not base_form.startswith("#")
    ]
