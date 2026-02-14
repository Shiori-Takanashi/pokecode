# src/pokecode/map_format.py
from pathlib import Path

from lxml import etree


def format_kml(src: Path, dst: Path) -> None:
    parser = etree.XMLParser(
        remove_blank_text=True,  # インデント由来の空白ノードを消す
        recover=False,
        huge_tree=True,  # 大きいKMLでも落ちにくくする
    )
    tree = etree.parse(src, parser)
    tree.write(
        dst,
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=True,
    )


def main() -> None:
    from pokecode.config import ConfigGetter

    cget = ConfigGetter()
    outdir = cget.get_data_dir()
    filename = cget.get_map_file()
    src = outdir / filename
    dst = cget.get_output_file("map_format", ext="kml")
    format_kml(src, dst)


if __name__ == "__main__":
    main()
