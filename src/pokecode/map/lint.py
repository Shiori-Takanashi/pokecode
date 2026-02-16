# src/pokecode/map/lint.py
from pathlib import Path

from lxml import etree

from pokecode.map.parser import parse_kml


def format_kml(src: Path, dst: Path) -> None:
    parser = etree.XMLParser(
        remove_blank_text=True,
        recover=False,
        huge_tree=True,
    )
    tree = parse_kml(src, parser)
    tree.write(
        dst,
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=True,
    )
