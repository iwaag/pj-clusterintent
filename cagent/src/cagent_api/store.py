"""In-memory request/session state.

Step 3 scope only: state lives in process memory. Step 4 replaces this with
an evidence-backed store where the durable copy is authoritative and
process memory is just a cache — see p1/contract.md's note that "request
state lives on the evidence side, not only in process memory."
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass, field

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
    identity_class: str
    name: str

    def as_dict(self) -> dict:
        return {"class": self.identity_class, "name": self.name}


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
    """Thread-safe in-memory store. One lock guards all mutation."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._requests: dict[str, Request] = {}
        self._sessions: dict[str, Session] = {}

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
            if (
                session.identity.identity_class != identity.identity_class
                or session.identity.name != identity.name
            ):
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
