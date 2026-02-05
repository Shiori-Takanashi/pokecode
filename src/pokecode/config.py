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

            load_dotenv(env_file, override=False)  # 既存の環境変数を上書きしない
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

    すべての設定に対して classmethod でアクセスすることで、
    動的に値を取得する（テスト時の環境変数変更にも対応）
    """

    # プロジェクトパス（不変）
    PROJECT_ROOT: Path = PROJECT_ROOT
    PYPROJECT: Path = PYPROJECT

    @classmethod
    def log_dir(cls) -> Path:
        """ログディレクトリを取得"""
        return Path(_get_env("POKECODE_LOG_DIR", "logs"))

    @classmethod
    def log_file(cls) -> str:
        """ログファイル名を取得"""
        return _get_env("POKECODE_LOG_FILE", "app.log")

    @classmethod
    def debug_log_dir(cls) -> Path:
        """デバッグログディレクトリを取得"""
        return Path(_get_env("POKECODE_DEBUG_LOG_DIR", "debug_log"))

    @classmethod
    def debug_log_file(cls) -> str:
        """デバッグログファイル名を取得"""
        return _get_env("POKECODE_DEBUG_LOG_FILE", "debug.log")

    @classmethod
    def host(cls) -> str:
        """サーバーホストを取得"""
        return _get_env("POKECODE_HOST", "127.0.0.1")

    @classmethod
    def port(cls) -> int:
        """サーバーポートを取得"""
        return int(_get_env("POKECODE_PORT", "5000"))

    @classmethod
    def local_html_url(cls) -> str:
        """ローカル HTML API URL を取得"""
        return _get_env("POKECODE_LOCAL_HTML_URL", "http://localhost:5000")

    @classmethod
    def local_json_url(cls) -> str:
        """ローカル JSON API URL を取得"""
        return _get_env("POKECODE_LOCAL_JSON_URL", "http://localhost:5000/json")

    # 下位互換性のため、大文字でもアクセス可能に
    @classmethod
    def LOG_DIR(cls) -> Path:
        """ログディレクトリ（下位互換性）"""
        return cls.log_dir()

    @classmethod
    def LOG_FILE(cls) -> str:
        """ログファイル名（下位互換性）"""
        return cls.log_file()

    @classmethod
    def HOST(cls) -> str:
        """ホスト（下位互換性）"""
        return cls.host()

    @classmethod
    def PORT(cls) -> int:
        """ポート（下位互換性）"""
        return cls.port()

    @classmethod
    def LOCAL_HTML_URL(cls) -> str:
        """HTML URL（下位互換性）"""
        return cls.local_html_url()

    @classmethod
    def LOCAL_JSON_URL(cls) -> str:
        """JSON URL（下位互換性）"""
        return cls.local_json_url()

    @classmethod
    def to_dict(cls) -> dict:
        """設定を dict に変換（デバッグ用）"""
        return {
            "PROJECT_ROOT": str(cls.PROJECT_ROOT),
            "PYPROJECT": str(cls.PYPROJECT),
            "LOG_DIR": str(cls.log_dir()),
            "LOG_FILE": cls.log_file(),
            "DEBUG_LOG_DIR": str(cls.debug_log_dir()),
            "DEBUG_LOG_FILE": cls.debug_log_file(),
            "HOST": cls.host(),
            "PORT": cls.port(),
            "LOCAL_HTML_URL": cls.local_html_url(),
            "LOCAL_JSON_URL": cls.local_json_url(),
        }

    @classmethod
    def log_current(cls) -> None:
        """現在の設定をログ出力（デバッグ用）"""
        logger.debug("Current configuration: %s", cls.to_dict())


# 下位互換性のため、従来のエクスポート
config = Config
