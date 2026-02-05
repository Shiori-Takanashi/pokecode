"""プロジェクトパス定数モジュール

getpath を使ってプロジェクトルートを検出し、
各種パスの定数を提供します。
"""

from pathlib import Path

from pokecode.getpath import get_project_root_to_parent

# プロジェクトルート検出
PROJECT_ROOT = get_project_root_to_parent(Path(__file__).parent)

# 各種パス定数
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
DOT_ENV_LOCAL = PROJECT_ROOT / ".env.local"
DOT_ENV = PROJECT_ROOT / ".env"
