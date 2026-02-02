import requests
from bs4 import BeautifulSoup
from bs4.element import ResultSet
from pathlib import Path
from requests import Response
from logging import Logger
from pokecode import url
import base64

from pokecode.logs import create_logger


def get_request(url: str) -> Response | None:
    """_summary_

    Args:
        url (str): _description_

    Returns:
        Response | None: _description_
    """
    return


def scrape_countries_from_response(res: Response) -> list[dict[str, str]]:
    """

    Args:
        res (Response): _description_

    Returns:
        list[dict[str, str]]: _description_
    """
    return


def scrape_uri_from_response(res: Response) -> list[str]:
    """_summary_

    Args:
        res (Response): _description_

    Returns:
        list[str]: _description_
    """
    return


def convert_binary_from_strings(strs: list[str]) -> list[bytes]:
    """_summary_

    Args:
        res (Response): _description_
        country_ios (str): _description_

    Returns:
        list[bytes]: _description_
    """
    return


def save_binary_as_png(binaries: list[bytes], country_ios: str) -> None:
    """_summary_

    Args:
        binaries (list[bytes]): _description_
        country_ios (str): _description_
    """
    return


def get_request_of_country_code(country_code: str, logger: Logger) -> Response | None:
    full_url = url.BASE + url.COUNTRY_PRE + country_code
    res = requests.get(full_url)
    if res.status_code != 200:
        return None
    return res


def get_request_of_countries(base_url: str, logger: Logger) -> Response | None:
    logger.info("Function Started.")
    res = requests.get(base_url)
    if res.status_code != 200:
        logger.info("ResponseCode Is Not Valid.")
        logger.info("Function Is Not Valid.")
        logger.info("Function Is Finishing.")
        return
    else:
        logger.info("ResponseCode Is Valid.")
        logger.info("Function Is Valid.")
        logger.info("Function Is Finishing.")
        return res


def scrape_countries_v1(res: Response) -> list[str] | None:
    soup = BeautifulSoup(res.text, "html.parser")

    container = soup.find("div", class_="container")
    if container is None:
        print("container.text is None(line:38)")
        return
    print(container.text[:200])

    if container is None:
        print("container is not found")
        return

    print("********************")

    alert_content = container.find("div", class_="alert")
    print(str(alert_content)[:200])
    return

    print("********************")

    country_select_area = alert_content.find("div", class_="form-group")
    print(str(country_select_area)[:600])
    return


def scrape_countries_v2(res: Response, logger: Logger) -> list[str]:
    soup = BeautifulSoup(res.text, "html.parser")

    selection = soup.find("select", id="filter_country")
    if selection is None:
        logger.info("selection is not valid.")
        return

    options = selection.find_all("option")
    if options is None:
        logger.info("options is not valid.")
        return

    values = [opt.get("value") for opt in options]
    if values is None:
        logger.info("values is not valid.")
        return

    if not isinstance(values, list):
        logger.info("values is not list.")
        return

    for value in values:
        if not isinstance(value, str):
            logger.info("value is not str.")
            return

    return values


def scrape_countries(res: Response, logger: Logger) -> list[dict[str, str]] | None:
    if not isinstance(res.text, str):
        logger.info("res.text is not str.")
        return
    if res.text == "":
        logger.info("res.text is ''.")
        return

    soup = BeautifulSoup(res.text, "html.parser")
    selection = soup.find("select", id="filter_country")
    if selection is None:
        logger.info("selection is not valid.")
        return

    options = selection.find_all("option")
    if options is None:
        logger.info("options is not valid.")
        return

    return [{"name": opt.text, "ios": opt.get("value")} for opt in options]


def scrape_qr_of_binary(res: Response) -> list[str] | None:
    soup = BeautifulSoup(res.text, "html.parser")

    container = soup.find("div", class_="container")
    print(container.text[:200])
    if container is None:
        print("container is not found")
        return None

    row = container.find("div", class_="row")
    print(row.text[:200])
    if row is None:
        print("row is not found")
        return None

    cards = row.find_all("div", recursive=False)
    if not cards:
        print("cards is not found")
        return None

    imgs = []

    for card in cards:
        img = card.find("img")
        if img is None:
            continue

        src = img.get("src")
        if not src:
            continue

        imgs.append(src)

    return imgs


def extract_qr_area(
    res: Response, country_code: str, dirpath: Path, logger: Logger
) -> ResultSet | None:
    soup = BeautifulSoup(res.text, "html.parser")

    if soup is None:
        logger.info("soup is invalid.")

    # data-qr-id 属性を持っている div をすべて取得
    elements = soup.find_all("div", attrs={"data-qr-id": True})

    if elements is None:
        logger.info("data-qr-id is invalid.")

    return elements


def save_qr_by_png(
    elms: ResultSet, country_code: str, dirpath: Path, logger: Logger
) -> None:
    for idx, elm in enumerate(elms):
        raw = elm.find("img").get("src")
        if not raw:
            logger.info("data is invalid.")
            return

        _, body = raw.split("base64,")
        if not body:
            logger.info("data-body is invalid.")

        binary = base64.b64decode(body)
        logger.debug(type(binary))

        filename = f"{country_code}{idx + 1:03d}.png"

        dirpath.mkdir(parents=True, exist_ok=True)
        filepath = dirpath / filename

        with open(filepath, "wb") as f:
            f.write(binary)

        logger.info(f"{filepath} is saved.")

    return


# res = get_request_of_country_code("NOR")
# imgs = scrape_qr_of_binary(res)
# print(len(imgs))


def main() -> None:
    logger = create_logger("request.main")
    # res = get_request_of_countries(
    #     url.BASE, create_logger("request.main.get_request_of_countries")
    # )
    # if res is None:
    #     logger.info("Response is None.")
    #     return
    # else:
    #     logger.info("Response is valid.")
    # countries = scrape_countries(res, create_logger("request.main.scrape_countries"))
    # if countries is None:
    #     logger.info("countries is not valid.")
    #     return
    # # for c in countries:
    # #     logger.info(f"{c}")
    # # return

    # countries_by_ios = [c.get("ios") for c in countries]
    # for c in countries_by_ios:
    #     logger.info(c)
    logger.info("Program start.")
    res = requests.get("https://www.pokemongofriendcodes.com/?country=NOR")
    elms = extract_qr_area(
        res, "IRL", Path("data"), create_logger("request.main.scrape_qr_area")
    )
    save_qr_by_png(
        elms, "IRL", Path("./png/NOR"), create_logger("request.main.save_qr_by_png")
    )


if __name__ == "__main__":
    main()
