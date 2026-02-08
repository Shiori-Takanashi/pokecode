import logging
from bs4 import BeautifulSoup, Tag
import re

logger = logging.getLogger(__name__)


def make_soup(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "html.parser")
    except Exception as e:
        raise RuntimeError(f"soupオブジェクトの作成に失敗: {e!r}") from e


def scrape_html(soup: BeautifulSoup) -> Tag:
    html = soup.select_one("html")
    if html is None:
        raise ValueError("html tagが存在しない。")
    return html


def scrape_cards_from_html(
    html: Tag,
) -> list[Tag]:
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


def scrape_correct_card(cards: list[Tag], expected: str) -> Tag:
    for card in cards:
        if is_target_card(card, title_expected=expected):
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


def scrape_friend_code_from_trainer(
    trainer: Tag,
) -> str:
    button = trainer.select_one("div.card > div.card-body > button")
    if button is None:
        raise ValueError("buttonが発見できません。")
    friend_code = button["data-friend-code"]
    if isinstance(friend_code, str):
        return str(friend_code)
    else:
        return ""


def scrape_code(trainer: Tag) -> str:
    button = trainer.select_one("button")
    if button is None:
        raise ValueError()
    try:
        code = button["data-friend-code"]
    except Exception:
        raise RuntimeError()
    return str(code).strip()


def scrape_selection(card: Tag) -> Tag:
    selection = card.select_one("select#filter_country")
    if selection is None:
        raise ValueError("selectionが見つかりません。")
    return selection


def scrape_options(selection: Tag) -> list[Tag]:
    options = selection.select("option")
    if options is None:
        raise ValueError("optionsが見つかりません。")
    return options


def scrape_country(option: Tag) -> dict[str, str]:
    code = option.get("value", None)
    if code is None:
        raise ValueError("codeが見つかりません。")
    name = option.text.strip()
    code = str(code)
    return {
        "iso_alpha3": code,
        "country_name": name,
    }


def get_country_without_extra_chars(
    country: dict[str, str],
) -> dict[str, str] | None:
    # iso_alpha3が3文字でない場合は除外
    iso_code = country.get("iso_alpha3", "")
    if len(iso_code) != 3:
        return None

    values = list(country.values())
    results = [without_extra_chars(text) for text in values]
    if all(results):
        return country
    else:
        return None


def without_extra_chars(text: str) -> bool:
    pattern = r"[^a-zA-Z,() '\-À-ÿ]"  # アクセント付きラテン文字を追加

    if re.search(pattern, text):
        return False
    else:
        return True
