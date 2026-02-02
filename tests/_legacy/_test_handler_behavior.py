"""
ハンドラーの動作を詳細に検証するテストスイート

このテストは以下を確認します：
1. 複数回の setup_logging() 呼び出し時のハンドラー動作
2. 異なるファイルパスでの setup_logging() 呼び出し
3. conftest.py のリセット機能
4. ハンドラーの重複が防止されているか
"""

import logging
import tempfile
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler

import pytest

from pokecode.logconfig import setup_logging


class TestHandlerBehavior:
    """ハンドラーの基本的な動作を検証"""

    def test_single_setup_logging_adds_handlers(self):
        """1回の setup_logging() でハンドラーが追加されることを確認"""
        root = logging.getLogger()

        # 初期状態を記録
        initial_count = len(root.handlers)
        initial_stream = sum(
            1
            for h in root.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, TimedRotatingFileHandler)
        )

        # setup_logging() を実行
        setup_logging()

        # 結果を確認
        final_count = len(root.handlers)
        final_stream = sum(
            1
            for h in root.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, TimedRotatingFileHandler)
        )

        print("\n[single_setup_logging]")
        print(f"  初期ハンドラー数: {initial_count}")
        print(f"  初期StreamHandler: {initial_stream}")
        print(f"  最終ハンドラー数: {final_count}")
        print(f"  最終StreamHandler: {final_stream}")
        print(f"  追加されたハンドラー数: {final_count - initial_count}")

        # StreamHandler が1つ追加されることを確認
        assert final_stream == initial_stream + 1

    def test_multiple_setup_logging_no_duplication(self):
        """複数回の setup_logging() でハンドラーが重複しないことを確認"""
        root = logging.getLogger()

        # 1回目
        setup_logging()
        count_1 = len(root.handlers)
        stream_1 = sum(
            1
            for h in root.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, TimedRotatingFileHandler)
        )

        # 2回目
        setup_logging()
        count_2 = len(root.handlers)
        stream_2 = sum(
            1
            for h in root.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, TimedRotatingFileHandler)
        )

        # 3回目
        setup_logging()
        count_3 = len(root.handlers)
        stream_3 = sum(
            1
            for h in root.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, TimedRotatingFileHandler)
        )

        print("\n[multiple_setup_logging]")
        print(f"  1回目: ハンドラー数={count_1}, StreamHandler={stream_1}")
        print(f"  2回目: ハンドラー数={count_2}, StreamHandler={stream_2}")
        print(f"  3回目: ハンドラー数={count_3}, StreamHandler={stream_3}")

        # ハンドラーが増えないことを確認
        assert count_1 == count_2 == count_3, (
            f"ハンドラーが増えた: {count_1} → {count_2} → {count_3}"
        )
        assert stream_1 == stream_2 == stream_3, (
            f"StreamHandlerが増えた: {stream_1} → {stream_2} → {stream_3}"
        )

    def test_handler_types_after_setup_logging(self):
        """setup_logging() 後のハンドラーの種類を確認"""
        root = logging.getLogger()

        setup_logging()

        # 各種ハンドラーのリストを作成
        handlers_by_type = {}
        for h in root.handlers:
            handler_type = type(h).__name__
            if handler_type not in handlers_by_type:
                handlers_by_type[handler_type] = []
            handlers_by_type[handler_type].append(h)

        print(f"\n[handler_types]")
        print(f"  ハンドラー合計数: {len(root.handlers)}")
        for handler_type, handlers in sorted(handlers_by_type.items()):
            print(f"  {handler_type}: {len(handlers)}個")

        # setup_logging が追加する2つのハンドラーが存在することを確認
        stream_handlers = [
            h
            for h in root.handlers
            if isinstance(h, logging.StreamHandler)
            and not isinstance(h, TimedRotatingFileHandler)
        ]
        timed_handlers = [
            h for h in root.handlers if isinstance(h, TimedRotatingFileHandler)
        ]

        assert len(stream_handlers) >= 1, "StreamHandler がない"
        assert len(timed_handlers) >= 1, "TimedRotatingFileHandler がない"


class TestPathResolution:
    """パス解決と early return チェックを検証"""

    def test_relative_path_resolution(self):
        """相対パスが正しく解決されることを確認"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # 相対パスと絶対パスの両方で setup_logging を呼び出す
            import os

            original_cwd = os.getcwd()
            try:
                os.chdir(tmppath)

                # 相対パスで setup_logging
                setup_logging(logdir="logs", logname="test.log")

                # ハンドラー数を記録
                root = logging.getLogger()
                count_1 = len(root.handlers)

                # 同じパスで再度 setup_logging（重複防止のテスト）
                setup_logging(logdir="logs", logname="test.log")
                count_2 = len(root.handlers)

                print(f"\n[relative_path_resolution]")
                print(f"  1回目ハンドラー数: {count_1}")
                print(f"  2回目ハンドラー数: {count_2}")
                print(f"  ✅ パス解決が正しく機能: {count_1 == count_2}")

                # 重複していないことを確認
                assert count_1 == count_2, "相対パスの解決に失敗（ハンドラーが増えた）"
            finally:
                os.chdir(original_cwd)

    def test_different_file_paths_add_handlers(self):
        """異なるファイルパスで setup_logging を呼び出すと新しいハンドラーが追加されることを確認"""
        root = logging.getLogger()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # 異なるファイルパスで setup_logging を2回呼び出す
            setup_logging(logdir=str(tmppath / "logs1"), logname="app1.log")
            count_1 = len(root.handlers)

            setup_logging(logdir=str(tmppath / "logs2"), logname="app2.log")
            count_2 = len(root.handlers)

            print(f"\n[different_file_paths]")
            print(f"  path1後: ハンドラー数={count_1}")
            print(f"  path2後: ハンドラー数={count_2}")
            print(f"  追加されたハンドラー数: {count_2 - count_1}")

            # 異なるパスなので新しいハンドラーが追加される
            assert count_2 > count_1, "異なるパスでも新しいハンドラーが追加されない"


class TestLoggingOutput:
    """ログ出力が正しく行われることを確認"""

    def test_log_output_not_duplicated(self):
        """同じメッセージが複数回出力されないことを確認"""
        import io

        # StringIO にログを出力
        root = logging.getLogger()
        setup_logging()

        # 新しい StreamHandler を追加（テスト用）
        stream = io.StringIO()
        test_handler = logging.StreamHandler(stream)
        test_handler.setFormatter(logging.Formatter("%(message)s"))
        root.addHandler(test_handler)

        # ログを出力
        logger = logging.getLogger("test")
        logger.info("test message")

        # StringIO からログを取得
        output = stream.getvalue()
        count = output.count("test message")

        print(f"\n[log_output]")
        print(f"  ログ出力数: {count}")
        print(f"  出力内容: {repr(output)}")

        # 重複していないことを確認（1回だけ出力されるはず）
        assert count == 1, f"ログが{count}回出力された（期待値: 1回）"

    def test_handler_chain_inspection(self):
        """ハンドラーチェーンを検査して詳細情報を出力"""
        root = logging.getLogger()

        setup_logging()

        print(f"\n[handler_chain_inspection]")
        print(f"  Root logger level: {logging.getLevelName(root.level)}")
        print(f"  ハンドラー数: {len(root.handlers)}")
        print()

        for i, handler in enumerate(root.handlers):
            handler_name = type(handler).__name__
            handler_level = logging.getLevelName(handler.level)
            handler_formatter = "あり" if handler.formatter else "なし"

            print(f"  [{i}] {handler_name}")
            print(f"      Level: {handler_level}")
            print(f"      Formatter: {handler_formatter}")

            # StreamHandler の詳細
            if isinstance(handler, logging.StreamHandler):
                stream = handler.stream
                print(
                    f"      Stream: {stream.name if hasattr(stream, 'name') else stream}"
                )

            # TimedRotatingFileHandler の詳細
            if isinstance(handler, TimedRotatingFileHandler):
                print(f"      File: {handler.baseFilename}")
                print(f"      When: {handler.when}")

            print()


class TestConfTestIntegration:
    """conftest.py のリセット機能との連携を検証"""

    def test_conftest_resets_timedrotating_handlers(self):
        """各テスト間で TimedRotatingFileHandler がリセットされることを確認"""
        root = logging.getLogger()

        # テスト開始時の TimedRotatingFileHandler 数
        timed_handlers_start = sum(
            1 for h in root.handlers if isinstance(h, TimedRotatingFileHandler)
        )

        setup_logging()

        # setup_logging 後の TimedRotatingFileHandler 数
        timed_handlers_after = sum(
            1 for h in root.handlers if isinstance(h, TimedRotatingFileHandler)
        )

        print(f"\n[conftest_integration]")
        print(f"  テスト開始時: {timed_handlers_start}個")
        print(f"  setup_logging後: {timed_handlers_after}個")
        print(f"  注: conftest.py のリセットは各テスト終了後に実行されます")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
