"""Upload CSV, JSON, or log files and extract structured fields."""

from flask import Flask, jsonify, request

from extractor.llm import client_from_env
from extractor.pipeline import extract_content

PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>LLM Data Extraction Assistant</title>
</head>
<body>
  <h1>LLM Data Extraction Assistant</h1>
  <p>Upload a CSV, JSON, or log file. The app parses it and returns structured fields.</p>
  <form action="/extract" method="post" enctype="multipart/form-data">
    <input type="file" name="file" accept=".csv,.json,.log" required>
    <button type="submit">Extract</button>
  </form>
</body>
</html>
"""


def create_app(client=None):
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 1_000_000
    model = client if client is not None else client_from_env()

    @app.get("/")
    def index():
        return PAGE

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/extract")
    def extract():
        uploaded = request.files.get("file")
        if uploaded is None or not uploaded.filename:
            return jsonify({"error": "Choose a CSV, JSON, or log file."}), 400
        try:
            content = uploaded.read().decode("utf-8")
            result = extract_content(uploaded.filename, content, client=model)
        except (UnicodeDecodeError, ValueError) as error:
            return jsonify({"error": str(error)}), 400
        return jsonify(result)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=False, port=5000)
