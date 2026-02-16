# src/pokecode/config/env.py

"""プロジェクト設定モジュール"""

import logging
import os

from pokecode.config.paths import (
    DOT_ENV,
    DOT_ENV_LOCAL,
    PROJECT_ROOT,
)

logger = logging.getLogger(__name__)


def require(name: str) -> str:
    v = os.getenv(name)
    if v is None:
        raise RuntimeError(f'環境変数"{name}"は未定義です。')
    return v


def load_env() -> None:
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
            logger.info(
                f"環境変数を{env_file.relative_to(PROJECT_ROOT)}から読み込みました。"
            )
        except ImportError:
            logger.warning(
                "python-dotenv is not installed. "
                "Install it with: pip install python-dotenv"
            )
