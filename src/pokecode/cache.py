import json
import logging
from pathlib import Path

from pokecode.logconfig import setup_logging

logger = logging.getLogger(__name__)


class TranslationCache:
    """翻訳結果をキャッシュするクラス"""

    def __init__(self, cache_dir: str = ".cache"):
        setup_logging(logger=logger, level="INFO")
        self.cache_dir = Path(cache_dir)
        self.cache_file = self.cache_dir / "translations.json"
        self.cache: dict[str, str] = {}
        self.load()

    def load(self) -> None:
        """キャッシュファイルからデータをロードする"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self.cache = json.load(f)
                logger.info(f"キャッシュをロード: {len(self.cache)}件")
            except Exception as e:
                logger.error(f"キャッシュのロードに失敗: {e!r}")
                self.cache = {}
        else:
            logger.info(f"キャッシュファイルが存在しません: {self.cache_file}")
            self.cache = {}

    def save(self) -> None:
        """キャッシュをファイルに保存する"""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            logger.info(f"キャッシュを保存: {len(self.cache)}件")
        except Exception as e:
            logger.error(f"キャッシュの保存に失敗: {e!r}")

    def get(self, key: str) -> str | None:
        """キャッシュから値を取得する

        Args:
            key: 検索キー（英語の国名）

        Returns:
            日本語の国名、またはキャッシュに存在しない場合はNone
        """
        return self.cache.get(key)

    def set(self, key: str, value: str) -> None:
        """キャッシュに値を設定する

        Args:
            key: キー（英語の国名）
            value: 値（日本語の国名）
        """
        self.cache[key] = value

    def set_batch(self, items: dict[str, str]) -> None:
        """複数の値をキャッシュに設定する

        Args:
            items: キーと値のマッピング
        """
        self.cache.update(items)

    def delete(self) -> None:
        self.cache = {}
        self.cache_file.unlink(missing_ok=True)

    def __len__(self) -> int:
        """キャッシュのサイズを返す"""
        return len(self.cache)

    def __contains__(self, key: str) -> bool:
        """キーがキャッシュに存在するか確認する"""
        return key in self.cache
