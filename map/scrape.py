import requests
from bs4 import BeautifulSoup

URL = "https://www.google.com/maps/d/u/0/viewer?mid=1Qg1CTqpOv0QLUVFRNW5svHNplRtAzWU&hl=ja&ll=33.63198206071317%2C61.04474896167899&z=6"


class GetPatternInfo:
    def __init__(self) -> None:
        self.pattern = 0
        self.area = 0

    def setup(self, url: str = URL) -> BeautifulSoup:
        res = requests.get(url)
        res.raise_for_status()

        try:
            soup = BeautifulSoup(res.text, "html.parser")
        except Exception:
            raise RuntimeError("soup作成に失敗")

        return soup

    def scrape_areas(self, soup: BeautifulSoup) -> None:
        arrow = soup.find_all("div", role="checkbox")
        print(len(arrow))
        return
        if arrow is None:
            raise RuntimeError("arrowが発見不能")
        content = arrow.parent
        if content is None:
            raise RuntimeError("contentが発見不能")
        labels = content.select("label")
        if labels is None:
            RuntimeError("labelsが発見不能")
        print(len(list(labels)))


gti = GetPatternInfo()
soup = gti.setup()
gti.scrape_areas(soup)
