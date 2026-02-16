# tools/json/schema.py
from typing import Any


def ensure_root(obj: Any) -> dict | list:
    if not isinstance(obj, (dict, list)):
        raise TypeError(f"Expected dict or list, got {type(obj).__name__}")
    return obj


def ensure_list_of_dict(obj: Any) -> list[dict]:
    if not isinstance(obj, list):
        raise TypeError("Expected list")
    if not all(isinstance(x, dict) for x in obj):
        raise TypeError("All elements must be dict")
    return obj
