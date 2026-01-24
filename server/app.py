from pathlib import Path
from flask import Flask, Response
import logging

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
HTML_PATH = BASE_DIR / "sample.html"


def load_html() -> str:
    if not HTML_PATH.exists():
        raise FileNotFoundError(f"{HTML_PATH} not found")
    return HTML_PATH.read_text(encoding="utf-8")


@app.route("/", methods=["GET"])
def index() -> Response:
    try:
        html = load_html()
    except Exception:
        logging.exception("failed to load html")
        return Response("internal error", status=500)

    return Response(html, content_type="text/html; charset=utf-8")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app.run(host="127.0.0.1", port=5000, debug=False)
