# src/pokecode/translate.py
import json
from pathlib import Path

from pokecode.translate_cache import TranslationCache
from pokecode.translate_service import TranslationService


def get_data(*, input_path: Path | None, input_data: Path | None):
    if (input_path is not None) and (input_data is not None):
        raise RuntimeError("引数が2個。")

    if (input_path is None) and (input_data is None):
        raise RuntimeError("引数が0個。")

    if input_path is not None:
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data

    if input_data is not None:
        return input_data


def translate(data: list) -> None:
    ts = TranslationService()
