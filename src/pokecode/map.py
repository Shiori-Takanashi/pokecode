# map.py

import logging

from pokecode.map_process import (
    parse_kml,
    find_placemarks,
    get_names_of_place,
)
from pokecode.map_format import format_kml
from pokecode.io_writing import save_json
from pokecode.config import ConfigGetter
from pokecode.logconfig import setup_logging

logger = logging.getLogger(__name__)


def format() -> None:
    setup_logging(logger=logger)
    cget = ConfigGetter()
    dirpath = cget.get_data_dir()
    filename = cget.get_map_file()
    src = dirpath / filename
    dst = cget.get_output_file("map_format", "kml")
    format_kml(src, dst)


def process() -> None:
    setup_logging(logger=logger)
    cget = ConfigGetter()
    filepath = cget.get_data_dir() / cget.get_map_file()
    tree = parse_kml(filepath)
    placemarks = find_placemarks(tree)
    cities = get_names_of_place(placemarks)
    save_json(cities, cget.get_output_file("city_from_map", "json"))
    return


def main() -> None:
    format()
    process()


if __name__ == "__main__":
    main()
