from pathlib import Path

from lxml import etree
from lxml.etree import XMLParser, _ElementTree


def read_kml(
    filepath: Path, *, parser: XMLParser | None = None
) -> _ElementTree:
    if parser is None:
        parser = etree.XMLParser(
            remove_blank_text=False,
            recover=False,
            huge_tree=True,
        )
    return etree.parse(filepath, parser)
