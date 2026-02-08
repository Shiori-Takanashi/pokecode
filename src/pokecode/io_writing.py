"""入出力モジュール

ファイルの読み書きやデータの保存を行う関数を提供します。
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def save_json(
    data: Any, filepath: Path, *, indent: int = 2
) -> None:
    """
    データをJSONファイルに保存

    Args:
        data: 保存するデータ（辞書、リスト等）
        filepath: 保存先ファイルパス
        indent: インデント設定（デフォルト: 2）

    Raises:
        OSError: ファイル書き込みエラー
        TypeError: JSON変換不可能なデータ
    """
    logger.info("Saving JSON to: %s", filepath)

    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with filepath.open("w", encoding="utf-8") as f:
            json.dump(
                data, f, ensure_ascii=False, indent=indent
            )

        logger.info(
            "JSON saved successfully: %d bytes",
            filepath.stat().st_size,
        )
    except Exception as e:
        logger.error("Failed to save JSON: %s", e)
        raise


# def load_json(filepath: Path) -> Any:
#     """
#     JSONファイルを読み込み

#     Args:
#         filepath: 読み込むファイルパス

#     Returns:
#         JSONデータ（辞書、リスト等）

#     Raises:
#         FileNotFoundError: ファイルが存在しない
#         json.JSONDecodeError: JSON解析エラー
#     """
#     logger.info("Loading JSON from: %s", filepath)

#     if not filepath.exists():
#         logger.error("File not found: %s", filepath)
#         raise FileNotFoundError(f"ファイルが見つかりません: {filepath}")

#     try:
#         with filepath.open("r", encoding="utf-8") as f:
#             data = json.load(f)

#         logger.info("JSON loaded successfully: type=%s", type(data).__name__)
#         return data
#     except Exception as e:
#         logger.error("Failed to load JSON: %s", e)
#         raise


# def save_text(text: str, filepath: Path, *, encoding: str = "utf-8") -> None:
#     """
#     テキストをファイルに保存

#     Args:
#         text: 保存するテキスト
#         filepath: 保存先ファイルパス
#         encoding: 文字エンコーディング（デフォルト: utf-8）

#     Raises:
#         OSError: ファイル書き込みエラー
#     """
#     logger.info("Saving text to: %s", filepath)

#     try:
#         filepath.parent.mkdir(parents=True, exist_ok=True)

#         with filepath.open("w", encoding=encoding) as f:
#             f.write(text)

#         logger.info("Text saved successfully: %d bytes", filepath.stat().st_size)
#     except Exception as e:
#         logger.error("Failed to save text: %s", e)
#         raise


# def load_text(filepath: Path, *, encoding: str = "utf-8") -> str:
#     """
#     テキストファイルを読み込み

#     Args:
#         filepath: 読み込むファイルパス
#         encoding: 文字エンコーディング（デフォルト: utf-8）

#     Returns:
#         ファイルの内容

#     Raises:
#         FileNotFoundError: ファイルが存在しない
#         UnicodeDecodeError: エンコーディングエラー
#     """
#     logger.info("Loading text from: %s", filepath)

#     if not filepath.exists():
#         logger.error("File not found: %s", filepath)
#         raise FileNotFoundError(f"ファイルが見つかりません: {filepath}")

#     try:
#         with filepath.open("r", encoding=encoding) as f:
#             text = f.read()

#         logger.info("Text loaded successfully: %d characters", len(text))
#         return text
#     except Exception as e:
#         logger.error("Failed to load text: %s", e)
#         raise


# def save_lines(lines: list[str], filepath: Path, *, encoding: str = "utf-8") -> None:
#     """
#     行のリストをファイルに保存

#     Args:
#         lines: 保存する行のリスト
#         filepath: 保存先ファイルパス
#         encoding: 文字エンコーディング（デフォルト: utf-8）

#     Raises:
#         OSError: ファイル書き込みエラー
#     """
#     logger.info("Saving %d lines to: %s", len(lines), filepath)

#     try:
#         filepath.parent.mkdir(parents=True, exist_ok=True)

#         with filepath.open("w", encoding=encoding) as f:
#             for line in lines:
#                 f.write(f"{line}\n")

#         logger.info("Lines saved successfully: %d bytes", filepath.stat().st_size)
#     except Exception as e:
#         logger.error("Failed to save lines: %s", e)
#         raise


# def load_lines(filepath: Path, *, encoding: str = "utf-8") -> list[str]:
#     """
#     ファイルを行ごとに読み込み

#     Args:
#         filepath: 読み込むファイルパス
#         encoding: 文字エンコーディング（デフォルト: utf-8）

#     Returns:
#         行のリスト（末尾の改行文字は削除）

#     Raises:
#         FileNotFoundError: ファイルが存在しない
#         UnicodeDecodeError: エンコーディングエラー
#     """
#     logger.info("Loading lines from: %s", filepath)

#     if not filepath.exists():
#         logger.error("File not found: %s", filepath)
#         raise FileNotFoundError(f"ファイルが見つかりません: {filepath}")

#     try:
#         with filepath.open("r", encoding=encoding) as f:
#             lines = [line.rstrip("\n\r") for line in f]

#         logger.info("Lines loaded successfully: %d lines", len(lines))
#         return lines
#     except Exception as e:
#         logger.error("Failed to load lines: %s", e)
#         raise


# def print_codes(codes: list[str]) -> None:
#     """
#     コードリストをコンソールに表示

#     Args:
#         codes: 表示するコードのリスト
#     """
#     logger.info("Printing %d codes", len(codes))

#     if not codes:
#         print("コードが見つかりませんでした。")
#         return

#     print("\n" + "=" * 50)
#     print(f"取得したコード: {len(codes)}件")
#     print("=" * 50)

#     for i, code in enumerate(codes, 1):
#         print(f"{i}. {code}")

#     print("=" * 50 + "\n")
