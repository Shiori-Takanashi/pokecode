import logging
from logging import StreamHandler

from pokecode.logconfig import setup_logging


def test_setup_logging_adds_console_handler(reset_logging):
    """
    setup_logging を1回呼び出したときに、
    対象 logger に console 用 StreamHandler が
    正確に1つ追加されることを確認するテスト。

    ・handler が追加されない
    ・複数個追加される
    といった初期化不備を検出する目的である。
    """
    logger = logging.getLogger("pokecode.test")

    setup_logging(logger=logger)

    handlers = [
        h
        for h in logger.handlers
        if isinstance(h, StreamHandler) and getattr(h, "name", None) == "console"
    ]

    assert len(handlers) == 1


def test_setup_logging_is_idempotent(reset_logging):
    """
    setup_logging を同一 logger に対して
    複数回呼び出しても、
    console 用 StreamHandler が
    重複して追加されないことを確認するテスト。

    初期化関数が冪等であることを保証する。
    """
    logger = logging.getLogger("pokecode.test")

    setup_logging(logger=logger)
    setup_logging(logger=logger)

    handlers = [
        h
        for h in logger.handlers
        if isinstance(h, StreamHandler) and getattr(h, "name", None) == "console"
    ]

    assert len(handlers) == 1


def test_setup_logging_sets_level_and_propagate(reset_logging):
    """
    setup_logging に level を指定した場合に、
    logger.level が期待通り設定され、
    propagate が False に固定されることを確認するテスト。

    ・ログレベルが反映されない
    ・親 logger へ伝播してしまう
    といった設定漏れを検出する目的である。
    """
    logger = logging.getLogger("pokecode.test")

    setup_logging(logger=logger, level="DEBUG")

    assert logger.level == logging.DEBUG
    assert logger.propagate is False
