# tools/json/transform.py
def drop_key_from_dicts(
    data: list[dict],
    key: str,
) -> list[dict]:
    return [{k: v for k, v in d.items() if k != key} for d in data]


def extract_key(
    data: list[dict],
    key: str,
) -> list:
    return [d[key] for d in data if key in d]
