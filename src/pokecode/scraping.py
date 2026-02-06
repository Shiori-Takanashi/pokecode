import logging
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

TargetElement = str | BeautifulSoup | Tag


def make_soup(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "html.parser")
    except Exception as e:
        raise RuntimeError(f"soupオブジェクトの作成に失敗: {e!r}") from e


def scrape_tag_of_html(soup: BeautifulSoup) -> Tag:
    html = soup.select_one("html")
    if html is None:
        raise ValueError("html tagが存在しない。")
    return html


def scrape_from_tagname(elm: TargetElement, *, tagname: str) -> TargetElement:
    if not isinstance(elm, TargetElement):
        raise TypeError("解析不能なオブジェクトが渡されました。")
    result_of_find = elm.find(tagname)
    if result_of_find is None:
        raise ValueError("発見できませんでした。")
    if isinstance(result_of_find, int):
        raise ValueError("int型は発見されないはずです。")
    logger.info(type(result_of_find))
    return result_of_find


def scrape_cards_from_html(html: Tag) -> list[Tag]:
    container = html.select_one("body > div.container")
    if not isinstance(container, Tag):
        logger.error(f"{type(container)}")
        raise TypeError("container is invalid.")

    card_body = container.select_one("div.card-body")
    if not isinstance(card_body, Tag):
        logger.error(f"{type(card_body)}")
        raise TypeError("card-body is invalid.")

    cards = list(card_body.select("div.card"))
    if not cards:
        raise ValueError("card not found.")

    return cards


def scrape_correct_card(cards: list[Tag]) -> Tag:
    for card in cards:
        if is_target_card(card, title_expected="📱 Friend Codes"):
            return card
    raise ValueError("適切な card が見つかりません。")


def is_target_card(card: Tag, *, title_expected: str) -> bool:
    heading2 = card.select_one("div.card-body > h2.card-title")
    if heading2 is None:
        return False
    text = heading2.get_text(strip=True)
    return title_expected in text


def scrape_trainers(card: Tag) -> list[Tag]:
    trainers_parent = card.select_one("div.card-body > div.row")
    if trainers_parent is None:
        raise ValueError("trainersの親要素が見つかりません。")

    trainers = list(trainers_parent.select("div.col"))
    if not trainers:
        raise ValueError("trainersが見つかりません。")
    return trainers
