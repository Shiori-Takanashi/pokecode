"""プロジェクト設定モジュール

環境変数または .env ファイルから設定値を読み込みます。
優先順位: 環境変数 → .env.local → .env → デフォルト値
"""

import logging
import os
from pathlib import Path

from pokecode.getpath import get_project_root_to_parent

logger = logging.getLogger(__name__)

# プロジェクトパス（定数）
PROJECT_ROOT = get_project_root_to_parent(Path(__file__).parent)
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
DOT_ENV_LOCAL = PROJECT_ROOT / ".env.local"
DOT_ENV = PROJECT_ROOT / ".env"


def _load_env() -> None:
    """
    .env ファイルを読み込む (python-dotenv を使用)
    
    .env.local が優先され、他の .env ファイルは上書きされない
    """
    env_file = None
    if DOT_ENV_LOCAL.exists():
        env_file = DOT_ENV_LOCAL
    elif DOT_ENV.exists():
        env_file = DOT_ENV

    if env_file:
        try:
            from dotenv import load_dotenv

            load_dotenv(env_file, override=False)
            logger.debug("Loaded .env file: %s", env_file)
        except ImportError:
            logger.warning(
                "python-dotenv is not installed. "
                "Install it with: pip install python-dotenv"
            )


def _get_env(key: str, default: str) -> str:
    """
    環境変数を取得
    
    Args:
        key: 環境変数名
        default: デフォルト値
        
    Returns:
        環境変数の値、またはデフォルト値
    """
    return os.getenv(key, default)


# .env ファイルを読み込む (モジュール初期化時)
_load_env()


# 設定値をアクセスするための関数
def get_log_dir() -> Path:
    """ログディレクトリを取得"""
    return Path(_get_env("POKECODE_LOG_DIR", "logs"))


def get_log_file() -> str:
    """ログファイル名を取得"""
    return _get_env("POKECODE_LOG_FILE", "app.log")


def get_debug_log_dir() -> Path:
    """デバッグログディレクトリを取得"""
    return Path(_get_env("POKECODE_DEBUG_LOG_DIR", "debug_log"))


def get_debug_log_file() -> str:
    """デバッグログファイル名を取得"""
    return _get_env("POKECODE_DEBUG_LOG_FILE", "debug.log")


def get_host() -> str:
    """サーバーホストを取得"""
    return _get_env("POKECODE_HOST", "127.0.0.1")


def get_port() -> int:
    """サーバーポートを取得"""
    return int(_get_env("POKECODE_PORT", "5000"))


def get_local_html_url() -> str:
    """ローカル HTML API URL を取得"""
    return _get_env("POKECODE_LOCAL_HTML_URL", "http://localhost:5000")


def get_local_json_url() -> str:
    """ローカル JSON API URL を取得"""
    return _get_env(
        "POKECODE_LOCAL_JSON_URL", "http://localhost:5000/json"
    )


def get_all() -> dict:
    """すべての設定を辞書で取得 (デバッグ用)"""
    return {
        "PROJECT_ROOT": str(PROJECT_ROOT),
        "PYPROJECT": str(PYPROJECT),
        "log_dir": str(get_log_dir()),
        "log_file": get_log_file(),
        "debug_log_dir": str(get_debug_log_dir()),
        "debug_log_file": get_debug_log_file(),
        "host": get_host(),
        "port": get_port(),
        "local_html_url": get_local_html_url(),
        "local_json_url": get_local_json_url(),
    }
