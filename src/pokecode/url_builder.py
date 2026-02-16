import logging

from pokecode.config.env import require
from pokecode.logconfig import setup_logging

logger = logging.getLogger(__name__)


def build_url_with_code(*, domain: str = "None", code: str = "None") -> str:
    setup_logging(logger=logger, level="INFO")
    if code == "None" or len(code) != 3:
        logger.error(f"codeが不正です :{code}")
        raise ValueError("codeが不正です。")
    if domain == "None":
        url = require("DOMAIN")
        url_with_code = f"{url}/?country={code}"
    else:
        url_with_code = f"{domain}/?country={code}"
    logger.debug(url_with_code)
    return url_with_code
