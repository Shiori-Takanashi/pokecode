# src/pokecode/map/extract_place.py

import logging

from lxml.etree import _ElementTree, _Element

from pokecode.logconfig import setup_logging

from pokecode.map.const import KML_NS


logger = logging.getLogger(__name__)
setup_logging(logger=logger, level="DEBUG")


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
