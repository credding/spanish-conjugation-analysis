# SPDX-License-Identifier: GPL-3.0-or-later

import logging
from pathlib import Path

import __main__


def configure_logging() -> None:
    _main_file = __main__.__file__
    assert _main_file  # noqa: S101

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(Path(_main_file).with_suffix(".log").name),
        ],
    )
