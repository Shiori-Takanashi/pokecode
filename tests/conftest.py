import logging
import pytest


@pytest.fixture(autouse=False)
def reset_logging():
    root = logging.getLogger()

    # handler をすべて除去
    for h in root.handlers[:]:
        root.removeHandler(h)

    # 状態を初期値へ
    root.setLevel(logging.NOTSET)
    root.propagate = True

    yield

    # 後処理も同様に念のためリセット
    for h in root.handlers[:]:
        root.removeHandler(h)
    root.setLevel(logging.NOTSET)
    root.propagate = True
