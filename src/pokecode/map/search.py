from pokecode.map.const import SRC, KML_NS
from lxml import etree
from pathlib import Path
import logging
from pokecode.map.kml_io import read_kml
from pokecode.map.parser import build_parser
from pokecode.logconfig import setup_logging
from lxml.etree import _ElementTree, _Element
from pokecode.io_writing import save_json


def extract(eltree: _ElementTree):
    pms = extract_placemarks(eltree)
    results = []
    if not isinstance(pms, list):
        raise
    for pm in pms:
        if isinstance(pm, _Element):
            if is_description(pm):
                city = get_text_of_name(pm)
                results.append(city)
    return results


def extract_placemarks(eltree: _ElementTree):
    els = eltree.xpath("//kml:Placemark", namespaces=KML_NS)
    return els


def is_description(el: _Element):
    de = el.xpath(".//kml:description", namespaces=KML_NS)
    return isinstance(de, list) and len(de) > 0


def get_text_of_name(el: _Element):
    names = el.xpath(".//kml:name", namespaces=KML_NS)
    if not isinstance(names, list) or len(names) == 0:
        return None
    first = names[0]
    if isinstance(first, _Element):
        return first.text
    return None


def save_object_by_tagname(
    tree: _ElementTree,
    tagname: str,
):
    elements = tree.xpath(f"//kml:{tagname}", namespaces=KML_NS)
    if not isinstance(elements, list):
        raise TypeError()
    for idx, el in enumerate(elements):
        if not isinstance(el, _Element):
            raise TypeError
        dst = Path(f"data/map/{tagname}{int(idx + 1):02d}.like.kml")
        # 要素を直接ファイルに書き出す
        dst.parent.mkdir(parents=True, exist_ok=True)
        with open(dst, "wb") as f:
            f.write(
                etree.tostring(
                    el,
                    pretty_print=False,
                    xml_declaration=True,
                    encoding="UTF-8",
                )
            )


def get_all_names(tree: _ElementTree) -> list[str]:
    objects = tree.xpath("//kml:name", namespaces=KML_NS)
    if not isinstance(objects, list):
        raise TypeError()
    names = [
        obj.text
        for obj in objects
        if isinstance(obj, _Element) and obj.text is not None
    ]
    if names is None:
        raise TypeError()
    for name in names:
        if not isinstance(name, str):
            raise TypeError()
    return names


def estimate_city(cities: list[str]) -> list[str]:
    result = []
    for city in cities:
        if ", " in city:
            result.append(city)
        else:
            continue
    return result


def write_all_placemarks_txt(eltree: _ElementTree, dst: Path) -> None:
    placemarks = extract_placemarks(eltree)
    if not isinstance(placemarks, list):
        raise TypeError()
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        for idx, pm in enumerate(placemarks):
            if not isinstance(pm, _Element):
                raise TypeError()
            if idx > 0:
                f.write("\n\n")
            f.write(f"# Placemark {idx + 1}\n")
            f.write(
                etree.tostring(
                    pm,
                    pretty_print=False,
                    xml_declaration=False,
                    encoding="unicode",
                )
            )


def write_duplicate_city_placemarks_txt(
    eltree: _ElementTree, dst: Path
) -> None:
    placemarks = extract_placemarks(eltree)
    if not isinstance(placemarks, list):
        raise TypeError()

    cities = [city for city in extract(eltree) if isinstance(city, str)]
    counts: dict[str, int] = {}
    for city in cities:
        counts[city] = counts.get(city, 0) + 1
    duplicates = {city for city, count in counts.items() if count > 1}

    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        idx = 0
        for pm in placemarks:
            if not isinstance(pm, _Element):
                raise TypeError()
            if not is_description(pm):
                continue
            name = get_text_of_name(pm)
            if name is None or name not in duplicates:
                continue
            idx += 1
            if idx > 1:
                f.write("\n\n")
            f.write(f"# Placemark {idx} ({name})\n")
            f.write(
                etree.tostring(
                    pm,
                    pretty_print=False,
                    xml_declaration=False,
                    encoding="unicode",
                )
            )


def main() -> None:
    logger = logging.getLogger("map")
    setup_logging(logger=logger, level="DEBUG")
    eltree = read_kml(filepath=SRC, parser=build_parser())
    cities = extract(eltree)
    save_json(cities, Path("data/map/json/city_info.json"))
    logger.debug(f"{len(cities)}")
    logger.debug(f"{len(set(cities))}")
    write_all_placemarks_txt(eltree, Path("data/map/placemarks.txt"))
    write_duplicate_city_placemarks_txt(
        eltree, Path("data/map/placemarks_duplicates.txt")
    )


# def main() -> None:
#     tree = read_kml(filepath=SRC, parser=build_parser())
#     names = get_all_names(tree)
#     estimated = estimate_city(names)
#     print(len(estimated))
#     print(len(set(estimated)))
#     save_json(estimated, Path("data/city_names.json"))


main()
