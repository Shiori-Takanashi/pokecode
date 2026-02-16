# src/pokecode/tools/path/builder.py

from pathlib import Path


def build_dirpath(
    *parts: str,
    root: Path,
) -> Path:
    """
    ディレクトリパスを構築する。
    """
    return root.joinpath(*parts)


def build_filepath(
    *parts: str,
    filename: str,
    root: Path,
) -> Path:
    """
    ファイルパスを構築する。
    """
    return root.joinpath(*parts, filename)
