# src/pokecode/map/const.py
from pathlib import Path

from pokecode.config.env import load_env, require

load_env()

KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}
SRC = Path(require("MAP_DIR")) / require("MAP_FILE")
DST = Path(require("MAP_DIR")) / require("RE_MAP_FILE")
