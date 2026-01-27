from pathlib import Path
import tomllib


def load_config(pyproject_path_str: str | None = None) -> dict:
    pyproject_path = Path(pyproject_path_str)
    if pyproject_path is None:
        pyproject_path = Path("pyproject.toml")

    if not pyproject_path.exists():
        return {}

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    return data
