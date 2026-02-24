from pokecode.map.const import SRC, DST
from pokecode.map.kml_io import read_kml, write_kml
from pokecode.map.escape import get_text_safe, set_element_text
from lxml.etree import XMLParser, _ElementTree, _Element


def build_parser() -> XMLParser:
    return XMLParser(
        remove_blank_text=False,  # 触らない
        recover=False,
        huge_tree=True,
        strip_cdata=False,  # 必須
        remove_comments=False,
        remove_pis=False,
        ns_clean=False,  # 触らない
    )


def collapse(*, tree: _ElementTree) -> _ElementTree:
    for el in tree.iter():
        collapse_text_elements(element=el)
    return tree


def collapse_text_elements(
    *,
    element: _Element,
    max_length: int = 600,
) -> None:
    if len(element) != 0:
        return

    text = get_text_safe(element)
    if text is None:
        return

    set_element_text(
        element,
        text=text,
        preserve_cdata=True,
        normalize=True,
        max_length=max_length,
    )


def main() -> None:
    parser: XMLParser = build_parser()
    tree = read_kml(filepath=SRC, parser=parser)
    tree = collapse(tree=tree)
    write_kml(tree=tree, filepath=DST)
    print("DONE")


main()
