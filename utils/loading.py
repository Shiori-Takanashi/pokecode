import tomllib
from pathlib import Path


def load_pyproject(pyproject_name: str | Path = "pyproject.toml") -> dict:
    path = Path(pyproject_name)

    if not path.exists():
        return {}

    with path.open("rb") as f:
        data = tomllib.load(f)

    return data
