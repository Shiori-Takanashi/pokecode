from __future__ import annotations

import re
from pathlib import Path

from lxml import etree
from lxml.etree import _Element, _ElementTree

from pokecode.map.const import KML_NS
from pokecode.map.kml_io import read_kml


_RE_WS = re.compile(r"\s+")
_RE_SPLIT_WS = re.compile(r"\s+")


def format_kml_for_review(
    src: Path,
    dst: Path,
    *,
    compact_text: bool = True,
    huge_tree: bool = True,
    coordinate_single_line_max: int = 200,
) -> None:
    parser = etree.XMLParser(
        remove_blank_text=True,
        recover=False,
        huge_tree=huge_tree,
    )
    tree = read_kml(src, parser=parser)

    if compact_text:
        compact_kml_text(
            tree, coordinate_single_line_max=coordinate_single_line_max
        )

    tree.write(
        dst,
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=True,
    )


def compact_kml_text(
    tree: _ElementTree,
    *,
    coordinate_single_line_max: int = 200,
) -> None:
    root = tree.getroot()

    targets = root.xpath(
        ".//kml:name | .//kml:styleUrl | .//kml:coordinates",
        namespaces=KML_NS,
    )

    if not isinstance(targets, list):
        raise TypeError("xpath結果がlistではありません。")

    for el in targets:
        if not isinstance(el, _Element):
            continue
        if el.text is None:
            continue

        local = etree.QName(el).localname

        if local in ("name", "styleUrl"):
            el.text = collapse_whitespace(el.text)

        elif local == "coordinates":
            el.text = normalize_coordinates(
                el.text,
                single_line_max=coordinate_single_line_max,
            )


def collapse_whitespace(text: str) -> str:
    return _RE_WS.sub(" ", text).strip()


def normalize_coordinates(text: str, *, single_line_max: int) -> str:
    raw = text.strip()
    if not raw:
        return ""

    tokens = [t for t in _RE_SPLIT_WS.split(raw) if t]

    normalized = []
    for t in tokens:
        normalized.append(_RE_WS.sub("", t))

    one_line = " ".join(normalized)
    if len(one_line) <= single_line_max:
        return one_line

    return "\n".join(normalized)
