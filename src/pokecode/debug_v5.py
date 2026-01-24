from pokecode.logconfig import setup_logging
import logging

setup_logging(logdir="debug", logfile="debug.log")
logger = logging.getLogger("pokecode.debug_v5")
logger.info("hello")
