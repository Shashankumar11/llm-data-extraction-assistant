"""LLM and offline clients that return an extraction JSON object."""

import json
import os
import urllib.error
import urllib.request

SYSTEM_PROMPT = (
    "You extract structured information from a parsed file. "
    "Return only a JSON object with the keys source_type, record_count, summary, fields, and records. "
    "summary is one sentence describing what the file contains. "
    "fields must come from the parsed input. "
    "records must be at most 5 records copied from the parsed input. "
    "Do not invent values that are not in the parsed input."
)


class LocalStructuredClient:
    """Prompt-driven extractor used when no LLM API key is configured."""

    def complete(self, messages: list[dict]) -> str:
        user = next(message["content"] for message in reversed(messages) if message["role"] == "user")
        marker = "PARSED_JSON:\n"
        if marker not in user:
            raise ValueError("The extraction prompt is missing the parsed file.")
        parsed = json.loads(user.split(marker, 1)[1])
        fields = parsed["fields"]
        field_text = ", ".join(fields) if fields else "no named fields"
        result = {
            "source_type": parsed["source_type"],
            "record_count": parsed["record_count"],
            "summary": (
                f"Parsed {parsed['record_count']} {parsed['source_type']} "
                f"record(s) with fields: {field_text}."
            ),
            "fields": fields,
            "records": parsed["records"][:5],
        }
        return json.dumps(result)


class OpenAICompatibleClient:
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def complete(self, messages: list[dict]) -> str:
        body = json.dumps(
            {"model": self.model, "messages": messages, "temperature": 0}
        ).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"LLM API returned {error.code}: {detail}") from error
        return payload["choices"][0]["message"]["content"]


def client_from_env():
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return LocalStructuredClient()
    return OpenAICompatibleClient(
        api_key=api_key,
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
    )
