import requests
import time
import random
from bs4 import BeautifulSoup
from bs4.element import Tag
from pathlib import Path
from requests import Response
from logging import Logger
import base64
import binascii

from pokecode.logs import create_logger

DOMAIN = "https://www.pokemongofriendcodes.com"

# 可読性のための型エイリアス
HtmlText = str
CountryName = str
CountryISO = str
Country = dict[CountryName, CountryISO]
Countries = list[Country]
QrUri = str
QrUris = list[QrUri]
QrBinary = bytes
QrBinaries = list[QrBinary]

# このモジュール用のロガーを作成
logger = create_logger(__name__)


def ensure_type(variable, expected_type, var_name: str, logger: Logger) -> None:
    """
    変数が期待される型であることを確認する。そうでない場合はエラーをログに記録しTypeErrorを発生させる。
    """
    # If expected_type is a tuple of types, collect their names for logging
    if isinstance(expected_type, tuple):
        expected_names = ", ".join(t.__name__ for t in expected_type)
    else:
        expected_names = expected_type.__name__
    if not isinstance(variable, expected_type):
        logger.info(
            f"TypeError: {var_name} must be of type {expected_names}, got {type(variable).__name__}"
        )
        raise TypeError(
            f"{var_name} must be of type {expected_names}, got {type(variable).__name__}"
        )


def ensure_elements_type(
    collection, expected_type, collection_name: str, logger: Logger
) -> None:
    """
    コレクションのすべての要素が期待される型であることを確認する。
    要素が該当しない場合はエラーをログに記録しTypeErrorを発生させる。
    """
    # First ensure the collection itself is a list
    ensure_type(collection, list, collection_name, logger)
    # Check each element's type
    for index, element in enumerate(collection):
        if not isinstance(element, expected_type):
            if isinstance(expected_type, tuple):
                expected_names = ", ".join(t.__name__ for t in expected_type)
            else:
                expected_names = expected_type.__name__
            logger.info(
                f"TypeError: {collection_name}[{index}] must be of type {expected_names}, got {type(element).__name__}"
            )
            raise TypeError(
                f"{collection_name}[{index}] must be of type {expected_names}, got {type(element).__name__}"
            )


def get_request(url: str, logger: Logger, max_retries: int = 5) -> Response:
    """
    指定されたURLからコンテンツを取得し、Responseオブジェクトを返す。
    503(Service Unavailable) の場合のみリトライを行う。
    """
    ensure_type(url, str, "url", logger)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
    }

    logger.info(f"Fetching URL: {url}")

    for attempt in range(1, max_retries + 1):
        try:
            res = requests.get(url, headers=headers, timeout=(10, 30))

            if res.status_code == 503:
                wait = min(2 ** (attempt - 1), 30) + random.random()
                logger.warning(
                    f"503 Service Unavailable (attempt {attempt}/{max_retries}), "
                    f"retrying after {wait:.1f}s"
                )
                time.sleep(wait)
                continue

            res.raise_for_status()

            logger.info(
                f"Successfully fetched URL: {url} (status code {res.status_code})"
            )
            return res

        except requests.RequestException as e:
            logger.warning(f"Request attempt {attempt}/{max_retries} failed: {e}")
            if attempt >= max_retries:
                logger.error(f"Giving up fetching URL: {url}")
                raise

            wait = min(2 ** (attempt - 1), 30) + random.random()
            time.sleep(wait)

    # 通常ここには到達しないが、制御フロー上の安全策
    raise RuntimeError(f"Failed to fetch URL after {max_retries} retries: {url}")


def get_soup(res: Response, logger: Logger) -> BeautifulSoup:
    return BeautifulSoup(res.text, "html.parser")


# def extract_text(soup: BeautifulSoup, logger: Logger) -> HtmlText:
#     """
#     BeautifulSoupオブジェクトからすべてのテキストコンテンツを抽出して返す。
#     """
#     ensure_type(soup, BeautifulSoup, "soup", logger)
#     logger.info("Extracting text from BeautifulSoup object")
#     try:
#         text = soup.get_text()
#         logger.info(f"Extracted text of length {len(text)} characters")
#         return text
#     except Exception as e:
#         logger.info(f"Unexpected error extracting text: {e}")
#         raise


# def parse_html(html_text: HtmlText, logger: Logger) -> BeautifulSoup:
#     """
#     指定されたHTMLテキストをBeautifulSoupオブジェクトに解析する。
#     """
#     ensure_type(html_text, str, "html_text", logger)
#     logger.info("Parsing HTML text into BeautifulSoup")
#     try:
#         soup = BeautifulSoup(html_text, "html.parser")
#         logger.info("HTML parsed successfully into BeautifulSoup")
#         return soup
#     except Exception as e:
#         logger.info(f"Failed to parse HTML text: {e}")
#         raise


def scrape_countries(soup: BeautifulSoup, logger: Logger) -> Countries:
    """
    BeautifulSoupオブジェクトから国名とISOコードをスクレイピングする。
    国名をキー、ISOコードを値とする辞書のリストを返す。
    """
    ensure_type(soup, BeautifulSoup, "soup", logger)
    logger.info("Scraping countries from HTML soup")
    countries: Countries = []
    try:
        country_divs = soup.find_all("div", class_="country")
        for div in country_divs:
            iso = div.get("data-iso")
            name_tag = div.find("span", class_="name")
            if not iso or not name_tag:
                continue  # ISOコードまたは名前がない場合はスキップ
            name = name_tag.get_text(strip=True)
            countries.append({name: iso})
            logger.info(f"Found country: {name} (ISO: {iso})")
        logger.info(f"Total countries found: {len(countries)}")
        return countries
    except Exception as e:
        logger.info(f"Error while scraping countries: {e}")
        raise


def scrape_target_from_parent(
    parent: Tag, elm: str, attribue_name: str, attribute_value
) -> Tag:
    results = parent.find_all(elm, attrs={attribue_name: attribute_value})
    if len(results) != 1:
        raise RuntimeError(
            f"<{elm} {attribue_name})='{attribute_value}'> is not single."
        )
    result = results[0]
    logger.critical(type(result))
    return


def scrape_cols(soup: BeautifulSoup, logger: Logger) -> list[Tag]:
    ensure_type(soup, BeautifulSoup, "soup", logger)
    logger.info("Extracting Friend Code cols from HTML soup.")

    body = soup.body
    if body is None:
        raise RuntimeError("body not found.")

    containers = body.find_all("div", class_="container", recursive=False, limit=2)
    if len(containers) != 1:
        raise RuntimeError(f"container is invalid. found={len(containers)}")
    container = containers[0]

    cards = container.find_all("div", class_="card", recursive=False, limit=2)
    if len(cards) != 1:
        raise RuntimeError(f"cards is invalid. found={len(cards)}")
    card = cards[0]

    card_bodies = card.find_all("div", class_="card-body", recursive=False, limit=2)
    if len(card_bodies) != 1:
        raise RuntimeError(f"card bodies is invalid. found={len(card_bodies)}")
    card_body = card_bodies[0]

    inner_cards = card_body.find_all("div", class_="card", recursive=False)

    for inner_card in inner_cards:
        class_names = inner_card.get("class", [])

        if "card" not in class_names:
            continue

        rows = inner_card.find_all("div", class_="row", recursive=False)

        if len(rows) != 1:
            continue

        row = rows[0]

    return

    cols = row.find_all("div", class_="col")
    logger.critical(f"{len(cols)}")

    imgs = []
    for col in cols:
        img = col.find("img")
        imgs.append(img)

    logger.critical(type(imgs))

    return imgs
    # h2 = card_body.find_all("h2")
    # if h2 is None:
    #     raise RuntimeError("h2 'Friend Code' not found in card_body.")
    # logger.critical(h2.text)
    # return

    # parent = h2.parent
    # if not isinstance(parent, Tag):
    #     raise RuntimeError("h2 parent is invalid.")

    # rows = parent.find_all("div", class_="row", recursive=False, limit=2)
    # if len(rows) != 1:
    #     raise RuntimeError(f"row is invalid. found={len(rows)}")
    # row = rows[0]

    # cols = row.find_all("div", class_="col", recursive=False)
    # if not cols:
    #     raise RuntimeError("col not found under row.")

    # logger.info(f"cols found: {len(cols)}")
    # return cols


def scrape_qr_uris_from_tag(target: Tag, logger: Logger) -> QrUris:
    return ["demo", "demo"]


def scrape_qr_uris(soup: BeautifulSoup, logger: Logger) -> QrUris:
    """
    BeautifulSoupオブジェクトからすべてのQRコード画像URIをスクレイピングする。
    URI文字列のリストを返す。
    """
    ensure_type(soup, BeautifulSoup, "soup", logger)
    logger.info("Scraping QR code image URIs from HTML soup")
    uris: QrUris = []
    try:
        img_tags = soup.find_all("img", class_="qr")
        for img in img_tags:
            src = img.get("src")
            if src:
                uris.append(src)
                logger.info(f"Found QR image URI (length {len(src)} characters)")
        logger.info(f"Total QR image URIs found: {len(uris)}")
        return uris
    except Exception as e:
        logger.info(f"Error while scraping QR URIs: {e}")
        raise


def fetch_qr_binaries(qr_uris: QrUris, logger: Logger) -> QrBinaries:
    """
    データURI文字列のリスト（base64エンコードされたPNG画像）をバイナリデータに変換する。
    デコードされた各画像のbytesオブジェクトのリストを返す。
    """
    ensure_elements_type(qr_uris, str, "qr_uris", logger)
    binaries: QrBinaries = []
    prefix = "data:image/png;base64,"
    total_uris = len(qr_uris)
    logger.info(f"Decoding {total_uris} QR image URIs to binary data")
    skip_count = 0
    try:
        for uri in qr_uris:
            if not uri.startswith(prefix):
                skip_count += 1
                continue  # base64画像URIでない場合はスキップ
            encoded = uri[len(prefix) :]  # プレフィックスを除去
            try:
                binary = base64.b64decode(encoded)
            except (binascii.Error, ValueError) as e:
                logger.info(f"Invalid base64 data for image: {e}")
                # デコードが失敗した場合はコンテキスト付きでValueErrorを発生
                raise ValueError("Invalid base64 image data") from e
            binaries.append(binary)
        if skip_count > 0:
            logger.info(
                f"Skipped {skip_count} URIs that were not base64-encoded images"
            )
        logger.info(f"Decoded {len(binaries)} out of {total_uris} URIs to binary data")
        return binaries
    except Exception as e:
        logger.info(f"Error in fetch_qr_binaries: {e}")
        raise


def save_qr_pngs(
    qr_binaries: QrBinaries, country_iso: CountryISO, logger: Logger
) -> None:
    """
    qr_binaries内の各bytesオブジェクトをPNGファイルとして保存する。
    ファイルは国のISOコードとインデックスを使用して命名され、'output'ディレクトリに保存される。
    """
    ensure_elements_type(qr_binaries, bytes, "qr_binaries", logger)
    ensure_type(country_iso, str, "country_iso", logger)
    logger.info(f"Saving {len(qr_binaries)} QR code images for country {country_iso}")
    try:
        output_dir = Path("../output")
        output_dir.mkdir(exist_ok=True)
        logger.info(f"Output directory set to: {output_dir.resolve()}")
        for idx, binary in enumerate(qr_binaries, start=1):
            file_path = output_dir / f"{country_iso}_{idx}.png"
            try:
                file_path.write_bytes(binary)
                logger.info(f"Saved image file: {file_path}")
            except OSError as e:
                logger.info(f"Failed to write file {file_path}: {e}")
                # ファイル書き込みが失敗した場合は処理を停止
                raise
        logger.info(
            f"Successfully saved {len(qr_binaries)} files to {output_dir.resolve()}"
        )
    except Exception as e:
        logger.info(f"Error saving QR code images for country {country_iso}: {e}")
        raise


def main() -> None:
    res = get_request(DOMAIN, create_logger("get_request"))
    soup = get_soup(res, create_logger("get_soup"))
    scrape_cols(soup, create_logger("scrape_cols"))


if __name__ == "__main__":
    main()
