import logging
from pokecode.logconfig import setup_logging

setup_logging()

root_logger = logging.getLogger()

# print("=== ルートロガー情報 ===")
# print(f"ロガー名: '{root_logger.name}' (空文字列はルートロガーを示す)")
# print(f"レベル: {root_logger.level} ({logging.getLevelName(root_logger.level)})")
# print(f"有効状態: {not root_logger.disabled}")
# print(f"ハンドラー数: {len(root_logger.handlers)}")

# print("\n=== ハンドラー詳細 ===")
# for i, handler in enumerate(root_logger.handlers, 1):
#     print(f"ハンドラー {i}: {type(handler).__name__}")
#     print(f"  レベル: {handler.level} ({logging.getLevelName(handler.level)})")
#     if hasattr(handler, "stream"):
#         print(f"  出力先: {handler.stream}")
#     if hasattr(handler, "baseFilename"):
#         print(f"  ファイルパス: {handler.baseFilename}")
#     if handler.formatter:
#         print(f"  フォーマット: {handler.formatter._fmt}")
#         print(f"  日付フォーマット: {handler.formatter.datefmt}")
#     print()

# print("=== テストログ出力 ===")
# root_logger.debug("デバッグメッセージ")
# root_logger.info("情報メッセージ")
# root_logger.warning("警告メッセージ")
# root_logger.error("エラーメッセージ")
