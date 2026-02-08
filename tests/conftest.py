import logging
import pytest


def _reset_all_loggers():
    """すべてのロガーとハンドラーをリセット"""
    for logger_name in list(logging.Logger.manager.loggerDict.keys()):
        logger = logging.getLogger(logger_name)
        for h in logger.handlers[:]:
            logger.removeHandler(h)
        logger.setLevel(logging.NOTSET)
        logger.propagate = True

    root = logging.getLogger()
    for h in root.handlers[:]:
        root.removeHandler(h)
    root.setLevel(logging.NOTSET)
    root.propagate = True


@pytest.fixture
def reset_logging():
    _reset_all_loggers()
    yield
    _reset_all_loggers()
