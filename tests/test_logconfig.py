import logging


def test_setup_logging_smoke(tmp_path) -> None:
    from pokecode.logconfig import setup_logging

    setup_logging()
