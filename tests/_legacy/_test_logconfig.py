def test_setup_logging_smoke(tmp_path):
    from pokecode.logconfig import setup_logging

    setup_logging(logdir=tmp_path, logname="test.log")

    log_file = tmp_path / "test.log"
    assert log_file.exists()


def test_setup_logging_creates_file(tmp_path):
    from pokecode.logconfig import setup_logging
    import logging

    setup_logging(logdir=tmp_path, logname="test.log")

    logging.getLogger(__name__).info("hello")

    assert (tmp_path / "test.log").exists()
