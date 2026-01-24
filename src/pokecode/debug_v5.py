from pokecode.logconfig import setup_logging
import logging

setup_logging()
logger = logging.getLogger("pokecode.debug_v5")
logger.info("hello")
