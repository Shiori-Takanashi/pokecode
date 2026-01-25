import logging
import pytest
from logging.handlers import TimedRotatingFileHandler


@pytest.fixture(autouse=True)
def reset_root_logger():
    """テスト隔離用ロガーリセット（TimedRotatingFileHandler のみ削除）"""
    root = logging.getLogger()

    timed_rotating_handlers = [
        h for h in root.handlers if isinstance(h, TimedRotatingFileHandler)
    ]

    for h in timed_rotating_handlers:
        root.removeHandler(h)
        h.close()

    yield

    timed_rotating_handlers = [
        h for h in root.handlers if isinstance(h, TimedRotatingFileHandler)
    ]

    for h in timed_rotating_handlers:
        root.removeHandler(h)
        h.close()
