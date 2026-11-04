"""Parse CSV, JSON, and log files into one record structure."""

import csv
import json
import re
from io import StringIO
from pathlib import Path

LOG_LINE = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2})\s+"
    r"(?P<level>DEBUG|INFO|WARNING|ERROR|CRITICAL)\s+"
    r"(?P<message>.*)$"
)


def parse_content(filename: str, content: str) -> dict:
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        return _parse_csv(content)
    if suffix == ".json":
        return _parse_json(content)
    if suffix == ".log":
        return _parse_log(content)
    raise ValueError("Upload a .csv, .json, or .log file.")


def _parse_csv(content: str) -> dict:
    reader = csv.DictReader(StringIO(content))
    if not reader.fieldnames:
        raise ValueError("The CSV file has no header row.")
    fields = [name.strip() for name in reader.fieldnames if name]
    records = []
    for row in reader:
        if not any((value or "").strip() for value in row.values()):
            continue
        records.append({field: (row.get(field) or "").strip() for field in fields})
    return _payload("csv", fields, records)


def _parse_json(content: str) -> dict:
    parsed = json.loads(content)
    if isinstance(parsed, list):
        records = [item if isinstance(item, dict) else {"value": item} for item in parsed]
    elif isinstance(parsed, dict):
        records = [parsed]
    else:
        records = [{"value": parsed}]
    fields = []
    for record in records:
        for key in record:
            if key not in fields:
                fields.append(str(key))
    return _payload("json", fields, records)


def _parse_log(content: str) -> dict:
    records = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = LOG_LINE.match(stripped)
        if match:
            records.append(match.groupdict())
        else:
            records.append({"timestamp": "", "level": "", "message": stripped})
    return _payload("log", ["timestamp", "level", "message"], records)


def _payload(source_type: str, fields: list, records: list) -> dict:
    return {
        "source_type": source_type,
        "record_count": len(records),
        "fields": fields,
        "records": records,
    }
