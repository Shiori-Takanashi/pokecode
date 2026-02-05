from pathlib import Path

# server ディレクトリを基準にパスを解決
SERVER_DIR = Path(__file__).parent
PROJECT_ROOT = SERVER_DIR.parent
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
STATIC_DIR = SERVER_DIR / "static"
TEMPLATES_DIR = SERVER_DIR / "templates"
