"""XML/KML text escaping helpers.

Keep text safe for XML output while preserving CDATA when requested.
"""

from typing import Optional
from xml.sax.saxutils import escape
from lxml import etree
from lxml.etree import _Element


def strip_bom(text: str) -> str:
    return text.replace("\ufeff", "")


def normalize_whitespace(text: str, max_length: int = 600) -> str:
    normalized = " ".join(text.split()).strip()
    if len(normalized) <= max_length:
        return normalized
    return text


def needs_cdata(text: str) -> bool:
    return "<" in text or "&" in text


def escape_xml_text(text: str) -> str:
    return escape(text, entities={'"': "&quot;", "'": "&apos;"})


def set_element_text(
    element: _Element,
    *,
    text: str,
    preserve_cdata: bool = True,
    normalize: bool = True,
    max_length: int = 600,
) -> None:
    clean = strip_bom(text)
    if normalize and not isinstance(element.text, etree.CDATA):
        clean = normalize_whitespace(clean, max_length=max_length)

    if " ]] > " in clean.replace("]]>", " ]] > "):
        element.text = escape_xml_text(clean)
        return

    if preserve_cdata and (
        isinstance(element.text, etree.CDATA) or needs_cdata(clean)
    ):
        element.text = etree.CDATA(clean)
        return

    element.text = clean


def get_text_safe(element: _Element) -> Optional[str]:
    if element.text is None:
        return None
    return strip_bom(element.text)
