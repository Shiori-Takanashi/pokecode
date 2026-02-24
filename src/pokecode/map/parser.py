from lxml.etree import XMLParser


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
