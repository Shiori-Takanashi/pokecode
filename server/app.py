import json
import logging
from pathlib import Path

import tomllib
from flask import Flask, jsonify, render_template

from server.paths import PYPROJECT, STATIC_DIR, TEMPLATES_DIR
from server.utils.create_qr import create_qr

app = Flask(__name__, template_folder=str(TEMPLATES_DIR))

logger = logging.getLogger(__name__)


def load_config(pyproject_path: Path = PYPROJECT) -> dict:
    """pyproject.toml から設定を読み込む"""
    if not pyproject_path.exists():
        logger.error("Config file not found: %s", pyproject_path)
        raise FileNotFoundError(f"pyproject.toml not found: {pyproject_path}")

    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)

    logger.info("Config loaded successfully")
    return data


@app.route("/json", methods=["GET"])
def get_json():
    """JSON データを返すエンドポイント"""
    sample_path = STATIC_DIR / "sample.json"
    if not sample_path.exists():
        return jsonify({"error": "File not found"}), 404
    with open(sample_path, "r") as f:
        data = json.load(f)
    res = jsonify(data)
    return res


@app.route("/", methods=["GET"])
def index():
    """HTML ページを返すエンドポイント"""
    return render_template("sample.html")


if __name__ == "__main__":
    data = load_config()
    host = data["tool"]["common"]["host"]
    port = int(data["tool"]["common"]["port"])
    create_qr("JAPAN")
    create_qr("UNITED STATES OF AMERICA")
    app.run(host=host, port=port, debug=False)
