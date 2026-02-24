# src/pokecode/map/kml_io.py

from pathlib import Path

from lxml import etree
from lxml.etree import XMLParser, _ElementTree


def read_kml(
    *, filepath: Path, parser: XMLParser | None = None
) -> _ElementTree:
    if parser is None:
        parser = etree.XMLParser(
            remove_blank_text=False,
            recover=False,
            huge_tree=True,
        )
    return etree.parse(filepath, parser)


def write_kml(
    *,
    tree: _ElementTree,
    filepath: Path,
    encoding: str = "utf-8",
    xml_declaration: bool = True,
    pretty_print: bool = False,
) -> None:
    """
    KMLを書き出す。
    lxmlのtree.writeをラップするだけのI/O関数。
    """

    tree.write(
        filepath,
        encoding=encoding,
        xml_declaration=xml_declaration,
        pretty_print=pretty_print,
    )
