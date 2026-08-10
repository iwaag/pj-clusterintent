"""Request/session state, backed by durable evidence (see evidence.py).

Process memory is a cache; `EvidenceWriter` is the durable copy of record,
written synchronously on every mutation, matching contract.md's "request
state lives on the evidence side, not only in process memory." Module-level
`scan_and_load` rebuilds a `Store` from evidence at startup and marks any
non-terminal request `interrupted` — see p1/report4.md for why this is
needed beyond process-restart alone (a wedged backend call can also leave a
request stuck `running` forever without a restart; that case is left
`running` here deliberately, only a restart re-scans evidence).
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field

from .evidence import EvidenceWriter

VALID_STATES = {
    "queued",
    "running",
    "completed",
    "failed",
    "cancelled",
    "interrupted",
}
TERMINAL_STATES = {"completed", "failed", "cancelled", "interrupted"}


@dataclass
class Identity:
    """Class-tagged identity (p4/contract.md, breaking change over Phase 2's
    fixed node-only shape). A node identity carries `uuid`/`cert_serial`; a
    human identity carries only `name` (a fixed operator label, not
    per-token — see contract's single-operator assumption). `owner_key()` is
    the value session/request ownership comparisons use, so callers never
    compare `uuid` directly (which is `None` for humans)."""

    identity_class: str
    uuid: str | None = None
    cert_serial: str | None = None
    name: str | None = None

    def as_dict(self) -> dict:
        if self.identity_class == "human":
            return {"class": "human", "name": self.name}
        return {"class": "node", "uuid": self.uuid, "cert_serial": self.cert_serial}

    def owner_key(self) -> str:
        """Every human-authenticated request is the same owner (single
        operator, p4/contract.md); nodes are keyed by DesiredNode UUID."""
        if self.identity_class == "human":
            return "human"
        return f"node:{self.uuid}"


@dataclass
class Request:
    request_id: str
    session_id: str
    identity: Identity
    message: str
    state: str = "queued"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    response: str | None = None
    error: dict | None = None
    # USD this turn cost, as the OpenCode session's own accounting reports it
    # (the per-turn delta of `GET /session/{id}`.cost). `None` means not
    # measured — a turn that never reached the backend, or a pre-existing
    # evidence record written before cost was recorded at all.
    cost_usd: float | None = None

    def as_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "state": self.state,
            "identity": self.identity.as_dict(),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "response": self.response,
            "error": self.error,
            "cost_usd": self.cost_usd,
        }


@dataclass
class Session:
    session_id: str
    identity: Identity
    created_at: float = field(default_factory=time.time)
    request_ids: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "identity": self.identity.as_dict(),
            "created_at": self.created_at,
            "last_activity_at": self.created_at,
            "turn_count": len(self.request_ids),
        }


class NotFoundError(Exception):
    pass


class OwnershipError(Exception):
    pass


class Store:
    """Thread-safe store. One lock guards all mutation and evidence writes."""

    def __init__(self, evidence: EvidenceWriter | None = None) -> None:
        self._lock = threading.Lock()
        self._requests: dict[str, Request] = {}
        self._sessions: dict[str, Session] = {}
        self._evidence = evidence

    def create_session_and_request(
        self, session_id: str, identity: Identity, message: str
    ) -> Request:
        with self._lock:
            session = Session(session_id=session_id, identity=identity)
            self._sessions[session_id] = session
            return self._new_request_locked(session, identity, message)

    def continue_session(
        self, session_id: str, identity: Identity, message: str
    ) -> Request:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise NotFoundError(f"session not found: {session_id}")
            if session.identity.owner_key() != identity.owner_key():
                raise OwnershipError("identity does not own this session")
            return self._new_request_locked(session, identity, message)

    def _new_request_locked(
        self, session: Session, identity: Identity, message: str
    ) -> Request:
        request_id = f"req_{uuid.uuid4().hex}"
        request = Request(
            request_id=request_id,
            session_id=session.session_id,
            identity=identity,
            message=message,
        )
        if self._evidence is not None:
            self._evidence.record_created(
                request_id, session.session_id, identity.as_dict(), message, request.created_at
            )
        self._requests[request_id] = request
        session.request_ids.append(request_id)
        return request

    def get_request(self, request_id: str) -> Request:
        with self._lock:
            request = self._requests.get(request_id)
            if request is None:
                raise NotFoundError(f"request not found: {request_id}")
            return request

    def update_request(self, request_id: str, **fields) -> Request:
        with self._lock:
            request = self._requests.get(request_id)
            if request is None:
                raise NotFoundError(f"request not found: {request_id}")
            for key, value in fields.items():
                setattr(request, key, value)
            request.updated_at = time.time()
            if self._evidence is not None and "state" in fields:
                detail = {}
                if request.response is not None:
                    detail["response"] = request.response
                if request.error is not None:
                    detail["error"] = request.error
                if request.cost_usd is not None:
                    detail["cost_usd"] = request.cost_usd
                self._evidence.append_event(request_id, request.state, detail)
            return request

    def list_sessions(self) -> list[Session]:
        with self._lock:
            return sorted(self._sessions.values(), key=lambda s: s.created_at)

    def list_session_requests(self, session_id: str) -> list[Request]:
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                raise NotFoundError(f"session not found: {session_id}")
            return [self._requests[rid] for rid in session.request_ids]


def _identity_from_record(d: dict) -> Identity:
    """Tolerant of both the Phase 2 shape (`{class, uuid, cert_serial}`,
    always `class: "node"`) and the Phase 4 class-tagged shape on disk —
    old evidence is read as history, not migrated (p4/contract.md)."""
    if d.get("class") == "human":
        return Identity(identity_class="human", name=d.get("name"))
    return Identity(identity_class=d.get("class", "node"), uuid=d.get("uuid"), cert_serial=d.get("cert_serial"))


def scan_and_load(evidence: EvidenceWriter) -> tuple[Store, list[str]]:
    """Rebuild a Store from evidence on startup.

    Any request whose latest recorded event is not a terminal state
    (`queued` or `running`) is stuck: either the process was killed
    mid-turn (exit criterion 4), or — per the Step 2 finding that OpenCode
    can retry a dead backend forever without ever settling a message — the
    process is still running OpenCode's underlying wait but restarting
    fresh means that in-flight wait is gone too. Either way, this process
    has no way to resume it, so it is marked `interrupted` here, once, at
    startup.

    Returns `(store, newly_interrupted_request_ids)` — the second element
    is only the requests transitioned *by this call*, not every request
    that happens to already be `interrupted` from a previous restart, so a
    caller logging it doesn't misreport an idle restart as having found
    fresh damage.
    """
    store = Store(evidence=evidence)
    by_session: dict[str, list[Request]] = {}
    newly_interrupted: list[str] = []

    for request_id in evidence.list_request_ids():
        record = evidence.read_request(request_id)
        latest = evidence.read_latest_event(request_id)
        state = latest["state"] if latest else "queued"
        detail = latest.get("detail", {}) if latest else {}

        if state not in TERMINAL_STATES:
            evidence.append_event(request_id, "interrupted", {})
            state = "interrupted"
            newly_interrupted.append(request_id)

        identity = _identity_from_record(record["identity"])
        request = Request(
            request_id=record["request_id"],
            session_id=record["session_id"],
            identity=identity,
            message=record["message"],
            state=state,
            created_at=record["created_at"],
            updated_at=latest["ts"] if latest else record["created_at"],
            response=detail.get("response"),
            error=detail.get("error"),
            cost_usd=detail.get("cost_usd"),
        )
        store._requests[request_id] = request
        by_session.setdefault(request.session_id, []).append(request)

    for session_id, requests in by_session.items():
        requests.sort(key=lambda r: r.created_at)
        owner = requests[0].identity
        session = Session(session_id=session_id, identity=owner, created_at=requests[0].created_at)
        session.request_ids = [r.request_id for r in requests]
        store._sessions[session_id] = session

    return store, newly_interrupted
