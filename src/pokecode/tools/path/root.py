# src/pokecode/tools/path/root.py


from pathlib import Path


def get_project_root_path(start: Path) -> Path:
    current = start.resolve()

    while True:
        if (current / "pyproject.toml").is_file():
            return current

        if current.parent == current:
            raise FileNotFoundError(
                "pyproject.toml not found in parent hierarchy."
            )

        current = current.parent
