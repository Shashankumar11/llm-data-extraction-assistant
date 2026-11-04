# LLM Data Extraction Assistant

Python application that parses CSV, JSON, and log files and returns structured fields. A prompt asks for JSON with a summary, field names, and sample records.

If `OPENAI_API_KEY` is set, the app sends that prompt to an OpenAI-compatible chat API (`OPENAI_BASE_URL` and `OPENAI_MODEL` are optional). Without a key, a local prompt reader returns the same JSON shape from the parsed file so the workflow still runs.

## Run

```bash
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 and upload `samples/people.csv`, `samples/events.json`, or `samples/app.log`.

## Test

```bash
python -m unittest discover -s tests
```
