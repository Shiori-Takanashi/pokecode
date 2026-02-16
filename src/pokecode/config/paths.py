# src/pokecode/config/paths.py
from pathlib import Path
from pokecode.tools.path.root import get_project_root_path

# プロジェクトルート検出
PROJECT_ROOT = get_project_root_path(Path(__file__).parent)

# 各種パス定数
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
DOT_ENV_LOCAL = PROJECT_ROOT / ".env.local"
DOT_ENV = PROJECT_ROOT / ".env"
