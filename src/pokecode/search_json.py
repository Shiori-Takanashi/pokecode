import logging
from pathlib import Path

from pokecode.paths import PROJECT_ROOT


logger = logging.getLogger(__name__)


def check_exist_json(target_json: Path) -> None:
    """target_jsonの存在を確認する。存在しない場合は例外を投げる。"""
    if not target_json.exists():
        raise FileNotFoundError(
            f"{target_json.relative_to(PROJECT_ROOT)} does not exist."
        )
    logger.debug(f"target_json exists: {target_json}")


def normalize_path(*, p: Path, project: Path = PROJECT_ROOT) -> Path:
    """パスをプロジェクトルートからの相対パスに正規化する。"""
    if not project.is_dir():
        raise ValueError(f"project must be a directory: {project}")

    try:
        p_normalized = p.relative_to(project)
    except ValueError as e:
        raise ValueError(f"Path {p} is not relative to {project}") from e

    return p_normalized
