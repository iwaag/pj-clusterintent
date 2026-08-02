"""Durable per-request evidence, same shape as `nctl ops`: an ID directory
plus JSON/JSONL (see `~/.local/state/nctl/events/<operation_id>/`).

`<evidence_dir>/<request_id>/`:
  - `request.json` — fields fixed at receipt time: request_id, session_id,
    identity, message, created_at.
  - `events.jsonl` — one line per state transition, append-only:
    {"ts", "state", "detail"}. `detail` carries the terminal response text
    or error object; empty for `queued`/`running`.

This is the durable copy contract.md requires ("request state lives on the
evidence side, not only in process memory"). `Store` (store.py) calls
`EvidenceWriter` synchronously on every mutation; `scan_and_load` rebuilds
`Store` from evidence at startup and marks any request found in a
non-terminal state `interrupted` — this is what exit criterion 4 needs.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

TERMINAL_STATES = {"completed", "failed", "cancelled", "interrupted"}


class EvidenceWriter:
    def __init__(self, evidence_dir: Path) -> None:
        self.evidence_dir = evidence_dir
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    def _dir(self, request_id: str) -> Path:
        d = self.evidence_dir / request_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def record_created(
        self, request_id: str, session_id: str, identity: dict, message: str, created_at: float
    ) -> None:
        d = self._dir(request_id)
        record = {
            "request_id": request_id,
            "session_id": session_id,
            "identity": identity,
            "message": message,
            "created_at": created_at,
        }
        (d / "request.json").write_text(json.dumps(record, indent=2))
        self.append_event(request_id, "queued", {})

    def append_event(self, request_id: str, state: str, detail: dict) -> None:
        d = self._dir(request_id)
        line = json.dumps({"ts": time.time(), "state": state, "detail": detail})
        with (d / "events.jsonl").open("a") as f:
            f.write(line + "\n")

    def read_request(self, request_id: str) -> dict:
        d = self.evidence_dir / request_id
        return json.loads((d / "request.json").read_text())

    def read_latest_event(self, request_id: str) -> dict | None:
        d = self.evidence_dir / request_id
        events_path = d / "events.jsonl"
        if not events_path.exists():
            return None
        latest = None
        with events_path.open() as f:
            for line in f:
                line = line.strip()
                if line:
                    latest = json.loads(line)
        return latest

    def list_request_ids(self) -> list[str]:
        if not self.evidence_dir.exists():
            return []
        return sorted(
            p.name for p in self.evidence_dir.iterdir()
            if p.is_dir() and (p / "request.json").exists()
        )
