import requests

from requests import Response


def requests_json(url: str) -> dict | list:
    res: Response = requests.get(url)

    res.raise_for_status()

    if "application/json" in res.headers.get("Content-Type", ""):
        data = res.json()
    else:
        raise RuntimeError("Response is not JSON.")

    if isinstance(data, dict):
        return data
    elif isinstance(data, list):
        return data
    else:
        raise RuntimeError("JSON is invalid.")
