import logging

from pokecode.paths import PROJECT_ROOT

# ハードコードは後に削除すべき
TARGET_JSON = PROJECT_ROOT / "countries_translated.json"

logger = logging.getLogger(__name__)


def check_exist_json() -> None:
    if not TARGET_JSON.exists():
        print(
            f"{TARGET_JSON.relative_to(PROJECT_ROOT)} exists."
        )
    raise FileExistsError(
        f"{TARGET_JSON.relative_to(PROJECT_ROOT)} does not exist."
    )


check_exist_json()
