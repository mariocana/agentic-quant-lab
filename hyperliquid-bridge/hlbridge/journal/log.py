"""Append-only JSONL journal. One line per event; the post-mortem agent (phase 2)
reads this, never the exchange directly."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from hlbridge.config import VAR

JOURNAL_PATH = VAR / "journal.jsonl"


def record(kind: str, payload: BaseModel | dict, path: Path = JOURNAL_PATH) -> None:
    body = payload.model_dump(mode="json") if isinstance(payload, BaseModel) else payload
    line = {"ts": datetime.now(timezone.utc).isoformat(), "kind": kind, **body}
    with open(path, "a") as f:
        f.write(json.dumps(line, default=str) + "\n")


def read(path: Path = JOURNAL_PATH, kind: str | None = None) -> list[dict]:
    if not path.exists():
        return []
    rows = [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    return [r for r in rows if kind is None or r["kind"] == kind]
