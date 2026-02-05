import logging
import tomllib
from pathlib import Path

from pokecode.config import Config

logger = logging.getLogger(__name__)


def load_config(pyproject_path: Path = Config.PYPROJECT) -> dict:
    """
    pyproject.toml から設定を読み込む

    Args:
        pyproject_path: pyproject.toml のパス

    Returns:
        読み込んだ設定 dict

    Raises:
        FileNotFoundError: pyproject.toml が見つからない
    """
    logger.info("Loading config: %s", pyproject_path)

    if not pyproject_path.exists():
        logger.error("Config file not found: %s", pyproject_path)
        raise FileNotFoundError(f"pyproject.toml not found: {pyproject_path}")

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    logger.info("Config loaded successfully")
    return data


def get_app_config() -> dict:
    """
    アプリケーション設定を取得（pyproject.toml + 環境変数）

    環境変数が優先される

    Returns:
        アプリケーション設定 dict
    """
    pyproject = load_config()

    # Config クラスから値を取得（環境変数を反映済み）
    return {
        "log_dir": str(Config.LOG_DIR),
        "log_file": Config.LOG_FILE,
        "debug_log_dir": str(Config.DEBUG_LOG_DIR),
        "debug_log_file": Config.DEBUG_LOG_FILE,
        "host": Config.HOST,
        "port": Config.PORT,
        "local_html_url": Config.LOCAL_HTML_URL,
        "local_json_url": Config.LOCAL_JSON_URL,
        **pyproject.get("tool", {}).get("pokecode", {}),
    }
