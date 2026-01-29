import tomllib
from pathlib import Path

from pokecode.config import PYPROJECT


def load_config(pyproject_path: Path = PYPROJECT) -> dict:
    if not pyproject_path.exists():
        raise FileNotFoundError("'pyproject.toml'が発見不可。")

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    return data
