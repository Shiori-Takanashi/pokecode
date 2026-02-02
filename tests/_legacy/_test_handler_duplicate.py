def test_check_stream_handler_duplication_version_simple():
    import logging
    from pokecode.logconfig import setup_logging

    root = logging.getLogger()
    print(f"\n[Before setup_logging] All handlers: {len(root.handlers)}")

    setup_logging()
    print(f"[After 1st setup_logging] All handlers: {len(root.handlers)}")

    setup_logging()
    print(f"[After 2nd setup_logging] All handlers: {len(root.handlers)}")

    logger = logging.getLogger()
    logger.info("MSG")

    stream_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler)]

    print(f"\n StreamHandler Count: {len(stream_handlers)}")
    for i, h in enumerate(stream_handlers):
        print(f"  [{i + 1}] {type(h).__name__} - stream: {h.stream}")
