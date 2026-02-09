import logging
from pathlib import Path
from typing import Any, TypeGuard

from pokecode.search_json import (
    check_exist_json,
    normalize_path,
)
from pokecode.convert_json import load_json
from pokecode.logconfig import setup_logging
from pokecode.paths import PROJECT_ROOT

# ハードコードは後に削除すべき
TARGET_DIR = PROJECT_ROOT / "output"
TARGET_JSON = TARGET_DIR / "country_ja.json"

mlogger = logging.getLogger(__name__)


def is_list_of_dicts(
    obj: Any,
) -> TypeGuard[list[dict]]:
    """オブジェクトが dict のリストであるか判定する。

    Args:
        obj: 検証対象のオブジェクト。

    Returns:
        bool: obj が list かつ全要素が dict の場合 True。
    """
    return isinstance(obj, list) and all(isinstance(item, dict) for item in obj)


def validate_list_of_dicts(data: Any) -> list[dict]:
    """データが dict のリストであることを検証する。

    Args:
        data: 検証するデータ。

    Returns:
        list[dict]: 検証済みのデータ。

    Raises:
        TypeError: データが list[dict] でない場合。
    """
    if not is_list_of_dicts(data):
        if not isinstance(data, list):
            raise TypeError(f"Expected list, got {type(data).__name__}")
        raise TypeError("All elements in the list must be dict")
    return data


def get_raw_data(
    target_json: Path = TARGET_JSON,
) -> list[dict]:
    setup_logging(logger=mlogger, level="DEBUG")

    check_exist_json(target_json)
    np = normalize_path(p=target_json)
    mlogger.debug(f"{np} is found.")

    data = load_json(target_json)
    mlogger.debug(f"{np} is loaded.")

    # list[dict] の形式であることを検証
    validated_data = validate_list_of_dicts(data)

    return validated_data


def extract(data: list[dict], keyname: str) -> list[str]:
    return [
        value for elm in data if isinstance((value := elm.get(keyname)), str)
    ]


def all_process() -> list[str]:
    data = get_raw_data()
    result = extract(data, "country_ja")
    return result
