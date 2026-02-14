# src/pokecode/map_parser.py

import logging
from pathlib import Path

from lxml import etree
from lxml.etree import _ElementTree, _Element

from pokecode.logconfig import setup_logging

KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}

logger = logging.getLogger(__name__)
setup_logging(logger=logger, level="DEBUG")


def parse_kml(filepath: Path) -> _ElementTree:
    return etree.parse(filepath)


def find_placemarks(tree: _ElementTree) -> list[_Element]:
    placemarks = tree.xpath(
        "//kml:Placemark[starts-with(kml:styleUrl, '#icon')]",
        namespaces=KML_NS,
    )

    if not isinstance(placemarks, list):
        raise TypeError("placemarksがlistでない。")

    return [p for p in placemarks if isinstance(p, _Element)]


def get_names_of_place(placemarks: list[_Element]) -> list[str]:
    names: set[str] = set()
    for pm in placemarks:
        text = pm.findtext(
            "kml:name", namespaces=KML_NS
        )  # ここはElementPathでOK
        if text is None:
            continue
        name = text.strip()
        if name:
            names.add(name)
    names_sorted = list(sorted(names))
    return names_sorted


def main():
    from pokecode.config import ConfigGetter

    cget = ConfigGetter()
    dirpath = cget.get_data_dir()
    filename = cget.get_map_file()
    filepath = dirpath / filename
    tree = parse_kml(filepath)
    placemarks = find_placemarks(tree)
    names_of_place = get_names_of_place(placemarks)
    logger.debug(f"place: {len(names_of_place)}")
    for index, np in enumerate(names_of_place):
        if index % 500 != 0:
            continue
        logger.debug(f"{index} is {np}")


if __name__ == "__main__":
    main()
