# src/pokecode/tools/path/is_exist.py

from pathlib import Path


def file_exists(path: Path) -> bool:
    return path.is_file()


def directory_exists(path: Path) -> bool:
    return path.is_dir()
