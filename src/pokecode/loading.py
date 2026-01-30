import logging
import tomllib
from pathlib import Path

from pokecode.config import PYPROJECT

logger = logging.getLogger(__name__)


def load_config(pyproject_path: Path = PYPROJECT) -> dict:
    logger.info("Loading config: %s", pyproject_path)

    if not pyproject_path.exists():
        logger.error("Config file not found: %s", pyproject_path)
        raise FileNotFoundError("'pyproject.toml'が発見不可。")

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    logger.info("Config loaded successfully")
    return data
