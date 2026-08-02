"""Auth ledger: "which public key of which DesiredNode is currently
trusted" (p2/contract.md, roadmap.md). nintent/Nautobot keeps owning
DesiredNode existence/validity — this module never checks that; callers
(the API server, Step 4) combine both checks separately.

Storage: a single append-only JSONL event log under `.local/cagent-ledger/`
(same durable-evidence spirit as `nctl ops` / cagent evidence) — a database
is not warranted at this scale. Every mutation (`register`, `revoke`,
`reactivate`) appends one event; current state per certificate serial is
derived by folding the log. This file is read and written by two different
processes (the long-running `cagent-api` server, and one-shot
`cagent-ledger` CLI invocations), so every read re-reads the file from disk
— no cross-process in-memory cache — and every write takes an advisory
`flock` so a concurrent CLI write and API-server read/write don't
interleave a torn line.

Public identifiers only: DesiredNode UUID, certificate serial, public-key
fingerprint, timestamps, state. Never a private key or raw cert blob.
"""

from __future__ import annotations

import datetime
import fcntl
import json
import time
from dataclasses import dataclass
from pathlib import Path

ACTIVE = "active"
REVOKED = "revoked"


class LedgerError(Exception):
    pass


class NotRegisteredError(LedgerError):
    pass


@dataclass(frozen=True)
class LedgerEntry:
    uuid: str
    serial: str
    fingerprint: str
    issued_at: float
    not_after: str
    state: str
    revoked_at: float | None = None

    def as_dict(self) -> dict:
        return {
            "uuid": self.uuid,
            "serial": self.serial,
            "fingerprint": self.fingerprint,
            "issued_at": self.issued_at,
            "not_after": self.not_after,
            "state": self.state,
            "revoked_at": self.revoked_at,
        }


class Ledger:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.touch()

    def _append(self, event: dict) -> None:
        with self.path.open("a") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                f.write(json.dumps(event) + "\n")
                f.flush()
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)

    def _read_events(self) -> list[dict]:
        if not self.path.exists():
            return []
        events = []
        with self.path.open() as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            try:
                for line in f:
                    line = line.strip()
                    if line:
                        events.append(json.loads(line))
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
        return events

    def _fold(self) -> dict[str, LedgerEntry]:
        entries: dict[str, LedgerEntry] = {}
        for event in self._read_events():
            serial = event["serial"]
            action = event["action"]
            if action == "register":
                entries[serial] = LedgerEntry(
                    uuid=event["uuid"],
                    serial=serial,
                    fingerprint=event["fingerprint"],
                    issued_at=event["ts"],
                    not_after=event["not_after"],
                    state=ACTIVE,
                    revoked_at=None,
                )
            elif action == "revoke":
                current = entries.get(serial)
                if current is not None:
                    entries[serial] = LedgerEntry(
                        uuid=current.uuid, serial=serial, fingerprint=current.fingerprint,
                        issued_at=current.issued_at, not_after=current.not_after,
                        state=REVOKED, revoked_at=event["ts"],
                    )
            elif action == "reactivate":
                current = entries.get(serial)
                if current is not None:
                    entries[serial] = LedgerEntry(
                        uuid=current.uuid, serial=serial, fingerprint=current.fingerprint,
                        issued_at=current.issued_at, not_after=current.not_after,
                        state=ACTIVE, revoked_at=None,
                    )
        return entries

    def register(self, uuid: str, serial: str, fingerprint: str, not_after: str) -> LedgerEntry:
        self._append({
            "ts": time.time(), "action": "register", "uuid": uuid, "serial": serial,
            "fingerprint": fingerprint, "not_after": not_after,
        })
        return self.get(serial)

    def revoke(self, serial: str) -> LedgerEntry:
        if self.get(serial) is None:
            raise NotRegisteredError(f"serial not registered: {serial}")
        self._append({"ts": time.time(), "action": "revoke", "serial": serial})
        return self.get(serial)

    def reactivate(self, serial: str) -> LedgerEntry:
        if self.get(serial) is None:
            raise NotRegisteredError(f"serial not registered: {serial}")
        self._append({"ts": time.time(), "action": "reactivate", "serial": serial})
        return self.get(serial)

    def get(self, serial: str) -> LedgerEntry | None:
        return self._fold().get(serial)

    def list(self) -> list[LedgerEntry]:
        return sorted(self._fold().values(), key=lambda e: e.issued_at)

    def is_active(self, serial: str) -> bool:
        entry = self.get(serial)
        return entry is not None and entry.state == ACTIVE

    def is_expired(self, serial: str, now: datetime.datetime | None = None) -> bool:
        entry = self.get(serial)
        if entry is None:
            return True
        not_after = datetime.datetime.fromisoformat(entry.not_after)
        now = now or datetime.datetime.now(datetime.timezone.utc)
        return now >= not_after
