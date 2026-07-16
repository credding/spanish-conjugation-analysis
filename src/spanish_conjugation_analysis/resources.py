# SPDX-License-Identifier: GPL-3.0-or-later

from importlib.resources import files
from pathlib import Path
from typing import cast

resources_path = files(cast("str", __package__)) / "resources"

artifacts_path = Path("artifacts").resolve()
obj_path = artifacts_path / "obj"
out_path = artifacts_path / "out"
