import logging

from lxml.etree import _Element, _ElementTree

from pokecode.map.const import KML_NS


logger = logging.getLogger(__name__)


def find_icon_placemarks(tree: _ElementTree) -> list[_Element]:
    nodes = tree.xpath(
        "//kml:Placemark[starts-with(kml:styleUrl, '#icon')]",
        namespaces=KML_NS,
    )

    if not isinstance(nodes, list):
        raise TypeError("xpath結果がlistではありません。")

    return [n for n in nodes if isinstance(n, _Element)]


def extract_place_names(placemarks: list[_Element]) -> list[str]:
    names: set[str] = set()

    for pm in placemarks:
        text = pm.findtext("kml:name", namespaces=KML_NS)
        if not text:
            continue

        name = text.strip()
        if name:
            names.add(name)

    return sorted(names)


def main() -> None:
    pass
