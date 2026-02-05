import logging
import os
from pathlib import Path
from typing import Optional

from pokecode.getpath import get_project_root_to_parent

logger = logging.getLogger(__name__)

# プロジェクトルート（動的検出）
PROJECT_ROOT = get_project_root_to_parent(Path(__file__).parent)
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
DOT_ENV_LOCAL = PROJECT_ROOT / ".env.local"
DOT_ENV = PROJECT_ROOT / ".env"


def _load_env() -> None:
    """
    .env ファイルを読み込む（python-dotenv を使用）
    """
    env_file = None
    if DOT_ENV_LOCAL.exists():
        env_file = DOT_ENV_LOCAL
    elif DOT_ENV.exists():
        env_file = DOT_ENV

    if env_file:
        try:
            from dotenv import load_dotenv

            load_dotenv(env_file)
            logger.debug("Loaded .env file: %s", env_file)
        except ImportError:
            logger.warning(
                "python-dotenv is not installed. Install it with: pip install python-dotenv"
            )


def _get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    環境変数を取得

    Args:
        key: 環境変数名
        default: デフォルト値

    Returns:
        環境変数の値、なければデフォルト値
    """
    return os.getenv(key, default)


# .env ファイルを読み込む（初期化時）
_load_env()


class Config:
    """プロジェクト設定の一元化

    環境変数 → .env ファイル → デフォルト値の順で値を決定
    """

    # プロジェクトパス
    PROJECT_ROOT: Path = PROJECT_ROOT
    PYPROJECT: Path = PYPROJECT

    # ログ設定（環境変数 POKECODE_* で上書き可能）
    LOG_DIR: Path = Path(_get_env("POKECODE_LOG_DIR", "logs"))
    LOG_FILE: str = _get_env("POKECODE_LOG_FILE", "app.log")
    DEBUG_LOG_DIR: Path = Path(_get_env("POKECODE_DEBUG_LOG_DIR", "debug_log"))
    DEBUG_LOG_FILE: str = _get_env("POKECODE_DEBUG_LOG_FILE", "debug.log")

    # サーバー設定
    HOST: str = _get_env("POKECODE_HOST", "127.0.0.1")
    PORT: int = int(_get_env("POKECODE_PORT", "5000"))

    # API URL（環境ごとに異なる）
    LOCAL_HTML_URL: str = _get_env(
        "POKECODE_LOCAL_HTML_URL", "http://localhost:5000"
    )
    LOCAL_JSON_URL: str = _get_env(
        "POKECODE_LOCAL_JSON_URL", "http://localhost:5000/json"
    )

    @classmethod
    def to_dict(cls) -> dict:
        """設定を dict に変換（デバッグ用）"""
        return {
            "PROJECT_ROOT": str(cls.PROJECT_ROOT),
            "PYPROJECT": str(cls.PYPROJECT),
            "LOG_DIR": str(cls.LOG_DIR),
            "LOG_FILE": cls.LOG_FILE,
            "DEBUG_LOG_DIR": str(cls.DEBUG_LOG_DIR),
            "DEBUG_LOG_FILE": cls.DEBUG_LOG_FILE,
            "HOST": cls.HOST,
            "PORT": cls.PORT,
            "LOCAL_HTML_URL": cls.LOCAL_HTML_URL,
            "LOCAL_JSON_URL": cls.LOCAL_JSON_URL,
        }

    @classmethod
    def log_current(cls) -> None:
        """現在の設定をログ出力（デバッグ用）"""
        logger.debug("Current configuration: %s", cls.to_dict())


# 下位互換性のため、従来のエクスポート
config = Config
