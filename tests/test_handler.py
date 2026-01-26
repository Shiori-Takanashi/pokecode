def test_v1() -> None:
    import logging
    from pokecode.logconfig import setup_logging

    setup_logging()

    root = logging.getLogger()

    for h in root.handlers:
        print(
            type(h),
            getattr(h, "level", None),
            getattr(h, "formatter", None),
        )
