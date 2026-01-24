from pathlib import Path
import tomllib


def load_config(pyproject_path: Path | None = None) -> dict:
    if pyproject_path is None:
        pyproject_path = Path("pyproject.toml")

    if not pyproject_path.exists():
        return {}

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    return data
