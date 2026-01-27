from pokecode.logconfig import setup_logging
from pokecode.load import load_config
import logging

config = load_config(pyproject_path_str="pyproject.toml")
tools = config["tool"]["pokecode"]

logdir = tools["debug_logdir"]
logfile = tools["debug_logfile"]

setup_logging(logdir=logdir, logname=logfile)
setup_logging()
setup_logging(logname="debug.log")

logger = logging.getLogger("debug")
logger.info("this is debug")
