# src/pokecode/config.py

"""プロジェクト設定モジュール

環境変数または .env ファイルから設定値を読み込みます。
優先順位: 環境変数 → .env.local → .env → デフォルト値
"""

import logging
import os
from pathlib import Path

from pokecode.paths import (
    DOT_ENV,
    DOT_ENV_LOCAL,
    PROJECT_ROOT,
)


class NotFoundDirectoryError(Exception):
    pass


logger = logging.getLogger(__name__)


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
            # logger.debug("Loaded .env file: %s", env_file)
        except ImportError:
            logger.warning(
                "python-dotenv is not installed. "
                "Install it with: pip install python-dotenv"
            )


class ConfigGetter:
    def __init__(self) -> None:
        load_env()

    # 設定値をアクセスするための関数
    def access(self, string: str) -> str:
        value = os.getenv(f"{string}", None)
        if value is None:
            msg = f"環境変数{string}が読み込めません。"
            logger.warning(msg)
            raise RuntimeError(msg)
        return value

    def get_stream_handler_name(self) -> str:
        return self.access("STREAM_HANDLER_NAME")

    def get_file_handler_name(self) -> str:
        return self.access("FILE_HANDLER_NAME")

    def get_base_fmt(self) -> str:
        return self.access("BASE_FMT")

    def get_date_fmt(self) -> str:
        return self.access("DATE_FMT")

    def get_dirname_of_log(self) -> str:
        """ログディレクトリを取得"""
        return self.access("LOG_DIR")

    def get_filename_log(self) -> str:
        """ログファイル名を取得"""
        return self.access("LOG_FILE")

    def get_host(self) -> str:
        """サーバーホストを取得"""
        return self.access("HOST")

    def get_port(self) -> str:
        """サーバーポートを取得"""
        return self.access("PORT")

    def get_local_html_url(self) -> str:
        """ローカル HTML API URL を取得"""
        return self.access("LOCAL_HTML_URL")

    def get_local_json_url(self) -> str:
        """ローカル JSON API URL を取得"""
        return self.access("LOCAL_JSON_URL")

    def get_domain(self) -> str:
        """本番でのurlを取得"""
        return self.access("DOMAIN")

    def get_data_dir(self) -> Path:
        dirname = self.access("DATA_DIR")
        dirpath = PROJECT_ROOT / dirname
        if not dirpath.exists():
            raise NotFoundDirectoryError(
                f"存在するべきはずのディレクトリが存在しない。:{dirpath.relative_to(PROJECT_ROOT)}"
            )
        return dirpath

    def get_map_file(self) -> str:
        return self.access("MAP_FILE")

    def get_output_file(self, name: str, ext: str) -> Path:
        """出力ファイルパスを取得"""
        outdir = Path(self.access("OUTPUT_DIR"))
        outfile = outdir / f"{name}.{ext}"
        return outfile

    def get_input_file(
        self, name: str, ext: str, dirname: str | None = None
    ) -> Path:
        """出力ファイルパスを作成"""
        if dirname is None:
            inputdir = Path(self.access("INPUT_DIR"))
        else:
            inputdir = PROJECT_ROOT / dirname
            inputdir.mkdir()
        inputfile = inputdir / f"{name}.{ext}"
        return inputfile
