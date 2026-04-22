from pathlib import Path

resources_path = Path(__file__).resolve().parent.joinpath("resources")

artifacts_path = Path("artifacts").resolve()
obj_path = artifacts_path.joinpath("obj")
out_path = artifacts_path.joinpath("out")
