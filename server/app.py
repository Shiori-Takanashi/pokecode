import logging
from pathlib import Path

import tomllib
from flask import Flask, Response, jsonify

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = PROJECT_ROOT / "pyproject.toml"

app = Flask(__name__)

logger = logging.getLogger(__name__)


def load_config(pyproject_path: Path = PYPROJECT) -> dict:
    if not pyproject_path.exists():
        logger.error("Config file not found: %s", pyproject_path)
        raise FileNotFoundError("'pyproject.toml'が発見不可。")

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    logger.info("Config loaded successfully")
    return data


@app.route("/api/hello", methods=["GET"])
def index() -> Response:
    return jsonify({"MSG": "Hello."})


if __name__ == "__main__":
    data = load_config()
    host = data["tool"]["common"]["host"]
    port = int(data["tool"]["common"]["port"])
    app.run(host=host, port=port, debug=False)
