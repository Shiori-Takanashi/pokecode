# src/pokecode/map/parser.py

import logging
from pathlib import Path

from lxml import etree
from lxml.etree import _ElementTree

from pokecode.logconfig import setup_logging

logger = logging.getLogger(__name__)


def parse_kml(filepath: Path, parser) -> _ElementTree:
    setup_logging(logger=logger)
    try:
        tree = etree.parse(filepath, parser)
    except Exception:
        raise Exception
    return tree
