import json
import unittest
from pathlib import Path

from app import create_app
from extractor.llm import SYSTEM_PROMPT
from extractor.pipeline import build_messages, extract_content, parse_model_json

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"


class ScriptedClient:
    def __init__(self):
        self.messages = None

    def complete(self, messages):
        self.messages = messages
        parsed = json.loads(messages[1]["content"].split("PARSED_JSON:\n", 1)[1])
        return (
            "```json\n"
            + json.dumps(
                {
                    "source_type": parsed["source_type"],
                    "record_count": parsed["record_count"],
                    "summary": "Scripted extraction.",
                    "fields": parsed["fields"],
                    "records": parsed["records"][:2],
                }
            )
            + "\n```"
        )


class ExtractionTest(unittest.TestCase):
    def test_prompt_includes_instructions_and_file_rows(self):
        content = (SAMPLES / "people.csv").read_text(encoding="utf-8")
        result = extract_content("people.csv", content)
        self.assertEqual(result["source_type"], "csv")
        self.assertEqual(result["record_count"], 3)
        self.assertEqual(result["fields"], ["name", "city", "role", "years"])
        self.assertEqual(result["records"][0]["name"], "Asha")
        self.assertIn("3 csv", result["summary"])

    def test_json_and_log_files(self):
        events = extract_content("events.json", (SAMPLES / "events.json").read_text(encoding="utf-8"))
        logs = extract_content("app.log", (SAMPLES / "app.log").read_text(encoding="utf-8"))
        self.assertEqual(events["records"][2]["status"], "error")
        self.assertEqual(logs["records"][1]["level"], "ERROR")
        self.assertEqual(logs["records"][1]["message"], "Disk full on /data")

    def test_fenced_model_json_and_prompt_text(self):
        client = ScriptedClient()
        result = extract_content("people.csv", (SAMPLES / "people.csv").read_text(encoding="utf-8"), client=client)
        self.assertEqual(client.messages[0]["content"], SYSTEM_PROMPT)
        self.assertIn("Asha", client.messages[1]["content"])
        self.assertEqual(result["summary"], "Scripted extraction.")
        self.assertEqual(result["mode"], "local")
        self.assertEqual(len(result["records"]), 2)

    def test_each_sample_upload(self):
        client = create_app().test_client()
        home = client.get("/")
        self.assertEqual(home.status_code, 200)
        self.assertIn(b"Upload a CSV", home.data)
        for name in ("people.csv", "events.json", "app.log"):
            with (SAMPLES / name).open("rb") as handle:
                response = client.post(
                    "/extract",
                    data={"file": (handle, name)},
                    content_type="multipart/form-data",
                )
            self.assertEqual(response.status_code, 200, response.data)
            body = response.get_json()
            self.assertGreater(body["record_count"], 0)
            self.assertTrue(body["fields"])

    def test_parse_model_json_rejects_plain_text(self):
        with self.assertRaises(ValueError):
            parse_model_json("no json here")
        messages = build_messages({"source_type": "csv", "record_count": 0, "fields": [], "records": []})
        self.assertIn("PARSED_JSON:", messages[1]["content"])


if __name__ == "__main__":
    unittest.main()
