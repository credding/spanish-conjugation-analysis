from importlib.resources import files
from pathlib import Path

resources_path = files() / "resources"

artifacts_path = Path("artifacts").resolve()
obj_path = artifacts_path / "obj"
out_path = artifacts_path / "out"
