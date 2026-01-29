from flask import Flask, Response, jsonify

app = Flask(__name__)


@app.route("/api/hello", methods=["GET"])
def index() -> Response:
    return jsonify({"MSG": "Hello."})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
