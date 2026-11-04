"""Turn an uploaded file into a structured extraction."""

import json

from extractor.llm import SYSTEM_PROMPT, client_from_env
from extractor.parse import parse_content


def build_messages(parsed: dict) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Extract structured fields from this parsed file.\n\n"
                "PARSED_JSON:\n"
                + json.dumps(parsed)
            ),
        },
    ]


def parse_model_json(raw: str) -> dict:
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("The model response did not contain a JSON object.")
    parsed = json.loads(text[start : end + 1])
    required = ["source_type", "record_count", "summary", "fields", "records"]
    missing = [key for key in required if key not in parsed]
    if missing:
        raise ValueError(f"Extraction JSON is missing: {', '.join(missing)}")
    return parsed


def extract_content(filename: str, content: str, client=None) -> dict:
    parsed = parse_content(filename, content)
    model = client or client_from_env()
    messages = build_messages(parsed)
    extracted = parse_model_json(model.complete(messages))
    extracted["mode"] = "llm" if model.__class__.__name__ == "OpenAICompatibleClient" else "local"
    return extracted
