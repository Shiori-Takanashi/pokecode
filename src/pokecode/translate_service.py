import logging
import os

from dotenv import load_dotenv

from pokecode.translate_cache import TranslationCache
from pokecode.logconfig import setup_logging

logger = logging.getLogger(__name__)


class TranslationService:
    """OpenAI APIを使用した国名翻訳サービス"""

    def __init__(self, cache_dir: str = ".cache"):
        load_dotenv()
        setup_logging(logger=logger, level="INFO")
        self.cache = TranslationCache(cache_dir=cache_dir)
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        self.timeout = int(os.getenv("OPENAI_REQUEST_TIMEOUT", "30"))

        if not self.api_key:
            logger.warning("OPENAI_API_KEYが環境変数に設定されていません")

    def translate_country_en(self, country_en: str) -> str:
        """単一の国名を翻訳する

        Args:
            country_en: 英語の国名

        Returns:
            日本語の国名
        """
        # キャッシュから取得
        cached = self.cache.get(country_en)
        if cached:
            logger.debug(f"キャッシュから取得: {country_en} -> {cached}")
            return cached

        # APIで翻訳
        try:
            result = self._call_openai_api([country_en])
            if result and country_en in result:
                ja_name = result[country_en]
                self.cache.set(country_en, ja_name)
                self.cache.save()
                logger.info(f"翻訳成功: {country_en} -> {ja_name}")
                return ja_name
        except Exception as e:
            logger.error(f"翻訳に失敗: {country_en} - {e!r}")

        # フォールバック: 元の名前を返す
        logger.warning(f"翻訳失敗、元の名前を返す: {country_en}")
        return country_en

    def translate_countries_batch(
        self,
        *,
        countries: list[dict[str, str]],
        ignore_cache: bool = True,
        batch_size: int = 10,
    ) -> list[dict[str, str]]:
        """複数の国を一括翻訳する

        Args:
            countries: 国情報のリスト（country_enを含む）
            batch_size: 1回のAPI呼び出しで処理する国の数

        Returns:
            country_jaフィールドが追加された国情報のリスト
        """
        result = []
        country_ens = [c["country_en"] for c in countries]

        if ignore_cache:
            self.cache.delete()

        # キャッシュにない国を特定
        to_translate = [name for name in country_ens if name not in self.cache]

        if to_translate:
            logger.info(
                f"翻訳が必要な国: {len(to_translate)}/{len(country_ens)}"
            )
            self._translate_batch(to_translate, batch_size)
        else:
            logger.info("すべての国がキャッシュに存在します")

        # 結果を構築
        for country in countries:
            country_copy = country.copy()
            country_en = country["country_en"]
            ja_name = self.cache.get(country_en) or country_en
            country_copy["country_ja"] = ja_name
            result.append(country_copy)

        return result

    def _translate_batch(
        self,
        country_ens: list[str],
        batch_size: int = 10,
    ) -> None:
        """複数の国名を分割してAPI呼び出しする

        Args:
            country_ens: 翻訳対象の国名リスト
            batch_size: 1回のAPI呼び出しで処理する数
        """
        for i in range(0, len(country_ens), batch_size):
            batch = country_ens[i : i + batch_size]
            logger.info(
                f"バッチ処理: {i + 1}-{min(i + batch_size, len(country_ens))}"
            )

            try:
                result = self._call_openai_api(batch)
                if result:
                    self.cache.set_batch(result)
            except Exception as e:
                logger.error(f"バッチ翻訳に失敗: {e!r}")
                # 失敗時は元の名前を使用
                for name in batch:
                    self.cache.set(name, name)

        self.cache.save()

    def _call_openai_api(self, country_ens: list[str]) -> dict[str, str] | None:
        """OpenAI APIを呼び出して翻訳する

        Args:
            country_ens: 翻訳対象の国名リスト

        Returns:
            元の名前をキーとする日本語翻訳のマッピング
        """
        if not self.api_key:
            logger.error("APIキーが設定されていません")
            return None

        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=self.api_key,
                timeout=self.timeout,
            )

            country_list = "\n".join(country_ens)
            prompt = (
                "あなたは地理と地名について正確な知識を持つ翻訳者です。\n"
                "以下の英語の国名を日本語に翻訳してください。\n"
                "「ココス（キーリング）諸島」のような翻訳は、分かりづらいので不可です。\n"
                "正式名称ではなく、普通の人が読みやすい翻訳です。\n"
                "出力は日本語のみで行ってください。\n"
                "日本語の翻訳のみを1行に1つずつ、入力と同じ順序で返してください。\n"
                "番号付け、説明、その他の文章は含めないでください。\n"
                f"\n{country_list}"
            )

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0,
            )

            content = response.choices[0].message.content
            if content is None:
                logger.error("API応答がNoneです")
                return None

            translations_text = content.strip()
            translations = translations_text.split("\n")

            if len(translations) != len(country_ens):
                logger.warning(
                    f"翻訳数が一致しません: {len(translations)} != {len(country_ens)}"
                )
                return None

            result = {
                name: translation.strip()
                for name, translation in zip(country_ens, translations)
            }
            logger.debug(f"API翻訳結果: {result}")
            return result

        except ImportError:
            logger.error("openaiライブラリがインストールされていません")
            logger.info("以下を実行してください: pip install openai")
            return None
        except Exception as e:
            logger.error(f"OpenAI API呼び出しに失敗: {e!r}")
            return None
