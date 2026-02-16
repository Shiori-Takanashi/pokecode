# tools/json/query.py
def filter_by_key_value(
    data: list[dict],
    key: str,
    value,
) -> list[dict]:
    return [d for d in data if d.get(key) == value]
