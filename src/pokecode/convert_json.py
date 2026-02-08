import json
from pathlib import Path
from typing import Any, TypeGuard


JsonResult = dict | list


def is_json_structure(obj: Any) -> TypeGuard[JsonResult]:
    """オブジェクトが JSON として有効な構造か判定する。

    JSON として扱える最上位構造は dict または list に限定されるため、
    それ以外の型は不正とみなす。

    Args:
        obj: 検証対象のオブジェクト。

    Returns:
        bool: obj が dict または list の場合 True。
    """
    return isinstance(obj, (dict, list))


def load_json(json_path: Path) -> JsonResult:
    """JSONファイルを読み込み、検証済みのデータを返す。

    ファイルを読み込んで JSON としてパースし、
    最上位構造が dict または list であることを保証する。

    Args:
        json_path (Path): 読み込む JSON ファイルのパス。

    Returns:
        JsonResult: 検証済みの JSON データ（dict または list）。

    Raises:
        FileNotFoundError: 指定されたファイルが存在しない場合。
        json.JSONDecodeError: JSON としてパースできない場合。
        TypeError: JSON の最上位構造が dict または list でない場合。
        RuntimeError: JSON データが空の場合。
    """
    with json_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # JSON の最上位構造を検証する
    if not is_json_structure(data):
        raise TypeError(
            f"Invalid JSON structure: expected dict or list, got {type(data).__name__}"
        )

    # 空データの検出（dict / list 共通）
    if len(data) == 0:
        raise RuntimeError("JSON data is empty.")

    return data
