import logging
import pytest
from logging import StreamHandler
from logging.handlers import TimedRotatingFileHandler

from pokecode.logconfig import setup_logging


@pytest.mark.usefixtures("reset_logging")
def test_setup_logging_adds_console_handler():
    """ """
    logger = logging.getLogger("pokecode.test")

    setup_logging(logger=logger)

    configured_handlers = logger.handlers

    console_handlers = [
        h
        for h in configured_handlers
        if isinstance(h, StreamHandler) and getattr(h, "name", None) == "console"
    ]

    file_handlers = [
        h
        for h in configured_handlers
        if isinstance(h, TimedRotatingFileHandler)
        and getattr(h, "name", None) == "file"
    ]

    assert len(console_handlers) == 1
    assert len(file_handlers) == 1


# @pytest.mark.usefixtures("reset_logging")
# def test_setup_logging_is_idempotent():
#     """
#     setup_logging を同一 logger に対して
#     複数回呼び出しても、
#     console 用 StreamHandler が
#     重複して追加されないことを確認するテスト。

#     初期化関数が冪等であることを保証する。
#     """
#     logger = logging.getLogger("pokecode.test")

#     setup_logging(logger=logger)
#     setup_logging(logger=logger)

#     handlers = [
#         h
#         for h in logger.handlers
#         if isinstance(h, StreamHandler) and getattr(h, "name", None) == "console"
#     ]

#     assert len(handlers) == 1


# @pytest.mark.usefixtures("reset_logging")
# def test_setup_logging_sets_level_and_propagate():
#     """
#     setup_logging に level を指定した場合に、
#     logger.level が期待通り設定され、
#     propagate が False に固定されることを確認するテスト。

#     ・ログレベルが反映されない
#     ・親 logger へ伝播してしまう
#     といった設定漏れを検出する目的である。
#     """
#     logger = logging.getLogger("pokecode.test")

#     setup_logging(logger=logger, level="DEBUG")

#     assert logger.level == logging.DEBUG
#     assert logger.propagate is False
