import logging
from pathlib import Path

from pokecode.paths import PROJECT_ROOT

# ハードコードは後に削除すべき
TARGET_DIR = PROJECT_ROOT / "output"
TARGET_JSON = TARGET_DIR / "countries_translated.json"

logger = logging.getLogger(__name__)


def check_exist_json() -> None:
    """TARGET_JSONの存在を確認する。存在しない場合は例外を投げる。"""
    if not TARGET_JSON.exists():
        raise FileNotFoundError(
            f"{TARGET_JSON.relative_to(PROJECT_ROOT)} does not exist."
        )
    logger.debug(f"target_json exists: {TARGET_JSON}")


def normalize_path(*, p: Path, project: Path = PROJECT_ROOT) -> Path:
    """パスをプロジェクトルートからの相対パスに正規化する。"""
    if not project.is_dir():
        raise ValueError(f"project must be a directory: {project}")

    try:
        p_normalized = p.relative_to(project)
    except ValueError as e:
        raise ValueError(f"Path {p} is not relative to {project}") from e

    return p_normalized


if __name__ == "__main__":
    # 存在確認
    check_exist_json()

    # パスの正規化例
    normalized = normalize_path(p=TARGET_JSON, project=PROJECT_ROOT)
    print(f"Normalized path: {normalized}")
