from pathlib import Path


class DirectoryNotFoundError(Exception):
    """プロジェクトルートが見つからない場合の例外"""

    pass


def get_project_root_to_parent(dirpath: Path) -> Path:
    """
    ディレクトリから親方向へ探索し、プロジェクトルートを検出

    .git または .venv を見つけたら、そのディレクトリをプロジェクトルートとする

    Args:
        dirpath: 探索を開始するディレクトリ

    Returns:
        プロジェクトルートのパス

    Raises:
        ValueError: dirpath がディレクトリでない
        DirectoryNotFoundError: プロジェクトルートが見つからない
    """
    if not dirpath.is_dir():
        raise ValueError(f"引数がディレクトリではありません: {dirpath}")

    if (dirpath / ".git").exists() or (dirpath / ".venv").exists():
        return dirpath.resolve()

    if dirpath == dirpath.parent:
        raise DirectoryNotFoundError("プロジェクトルートが見つかりませんでした。")

    return get_project_root_to_parent(dirpath.parent)


def get_pyproject_to_parent(dirpath: Path) -> Path:
    """
    ディレクトリから親方向へ探索し、pyproject.toml を検出

    Args:
        dirpath: 探索を開始するディレクトリ

    Returns:
        pyproject.toml のパス

    Raises:
        ValueError: dirpath がファイルである
        FileNotFoundError: pyproject.toml が見つからない
    """
    if dirpath.is_file():
        raise ValueError(f"引数がファイルです: {dirpath}")

    pyproject = dirpath / "pyproject.toml"

    if pyproject.is_file():
        return pyproject

    if (dirpath / ".git").exists() or (dirpath / ".venv").exists():
        raise FileNotFoundError(
            "プロジェクトルートまで遡りましたが、pyproject.toml がありません。"
        )

    if dirpath == dirpath.parent:
        raise FileNotFoundError(
            "ルートディレクトリまで到達しましたが、pyproject.toml が見つかりません。"
        )

    return get_pyproject_to_parent(dirpath.parent)
