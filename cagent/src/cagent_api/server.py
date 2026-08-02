"""cluster-agent API HTTP server (loopback MVP). See p1/contract.md."""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .opencode_client import OpenCodeClient, OpenCodeError
from .store import Identity, NotFoundError, OwnershipError, Store, TERMINAL_STATES
from .worker import Worker

MAX_IDENTITY_NAME_LENGTH = 200
VALID_IDENTITY_CLASSES = {"node", "human"}

_ROUTE_REQUESTS = re.compile(r"^/requests$")
_ROUTE_SESSION_REQUESTS = re.compile(r"^/sessions/(?P<session_id>[^/]+)/requests$")
_ROUTE_REQUEST_GET = re.compile(r"^/requests/(?P<request_id>[^/]+)$")
_ROUTE_REQUEST_CANCEL = re.compile(r"^/requests/(?P<request_id>[^/]+)/cancel$")
_ROUTE_SESSIONS_LIST = re.compile(r"^/sessions$")


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, request_id: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.request_id = request_id


def make_handler(store: Store, opencode: OpenCodeClient, worker: Worker):
    class Handler(BaseHTTPRequestHandler):
        server_version = "cagent-api/0.0.1"

        def log_message(self, fmt: str, *args) -> None:  # quieter default logging
            pass

        def _identity(self) -> Identity:
            identity_class = self.headers.get("X-Cluster-Agent-Identity-Class", "")
            name = self.headers.get("X-Cluster-Agent-Identity-Name", "")
            if identity_class not in VALID_IDENTITY_CLASSES:
                raise ApiError(400, "bad_request", "X-Cluster-Agent-Identity-Class must be 'node' or 'human'")
            if not name or len(name) > MAX_IDENTITY_NAME_LENGTH:
                raise ApiError(400, "bad_request", "X-Cluster-Agent-Identity-Name must be 1-200 chars")
            return Identity(identity_class=identity_class, name=name)

        def _body(self) -> dict:
            length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(length) if length else b""
            if not raw:
                return {}
            try:
                return json.loads(raw)
            except json.JSONDecodeError as exc:
                raise ApiError(400, "bad_request", f"invalid JSON body: {exc}") from exc

        def _write_json(self, status: int, payload: dict) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _write_error(self, err: ApiError) -> None:
            self._write_json(
                err.status,
                {"error": {"code": err.code, "message": err.message, "request_id": err.request_id}},
            )

        def do_POST(self) -> None:  # noqa: N802 (stdlib naming)
            try:
                self._dispatch_post()
            except ApiError as err:
                self._write_error(err)
            except Exception as exc:  # last-resort guard, not routine control flow
                self._write_error(ApiError(500, "internal_error", str(exc)))

        def do_GET(self) -> None:  # noqa: N802
            try:
                self._dispatch_get()
            except ApiError as err:
                self._write_error(err)
            except Exception as exc:
                self._write_error(ApiError(500, "internal_error", str(exc)))

        def _dispatch_post(self) -> None:
            path = self.path.split("?", 1)[0]

            if _ROUTE_REQUESTS.match(path):
                return self._create_request()

            m = _ROUTE_SESSION_REQUESTS.match(path)
            if m:
                return self._continue_session(m.group("session_id"))

            m = _ROUTE_REQUEST_CANCEL.match(path)
            if m:
                return self._cancel_request(m.group("request_id"))

            raise ApiError(404, "not_found", f"no such route: POST {path}")

        def _dispatch_get(self) -> None:
            path = self.path.split("?", 1)[0]

            m = _ROUTE_REQUEST_GET.match(path)
            if m:
                return self._get_request(m.group("request_id"))

            if _ROUTE_SESSIONS_LIST.match(path):
                return self._list_sessions()

            m = _ROUTE_SESSION_REQUESTS.match(path)
            if m:
                return self._list_session_requests(m.group("session_id"))

            raise ApiError(404, "not_found", f"no such route: GET {path}")

        def _create_request(self) -> None:
            identity = self._identity()
            body = self._body()
            message = body.get("message")
            if not isinstance(message, str) or not message:
                raise ApiError(400, "bad_request", "'message' is required and must be a non-empty string")

            title = message[:60]
            try:
                session_id = opencode.create_session(title)
            except OpenCodeError as exc:
                raise ApiError(502, "opencode_unavailable", str(exc))

            request = store.create_session_and_request(session_id, identity, message)
            worker.enqueue(request.request_id)
            self._write_json(202, {
                "request_id": request.request_id,
                "session_id": request.session_id,
                "state": request.state,
            })

        def _continue_session(self, session_id: str) -> None:
            identity = self._identity()
            body = self._body()
            message = body.get("message")
            if not isinstance(message, str) or not message:
                raise ApiError(400, "bad_request", "'message' is required and must be a non-empty string")

            try:
                request = store.continue_session(session_id, identity, message)
            except NotFoundError as exc:
                raise ApiError(404, "not_found", str(exc))
            except OwnershipError as exc:
                raise ApiError(403, "forbidden", str(exc))

            worker.enqueue(request.request_id)
            self._write_json(202, {
                "request_id": request.request_id,
                "session_id": request.session_id,
                "state": request.state,
            })

        def _get_request(self, request_id: str) -> None:
            try:
                request = store.get_request(request_id)
            except NotFoundError as exc:
                raise ApiError(404, "not_found", str(exc), request_id=request_id)
            self._write_json(200, request.as_dict())

        def _cancel_request(self, request_id: str) -> None:
            try:
                request = store.get_request(request_id)
            except NotFoundError as exc:
                raise ApiError(404, "not_found", str(exc), request_id=request_id)

            if request.state in TERMINAL_STATES:
                self._write_json(200, request.as_dict())
                return

            if request.state == "queued":
                request = store.update_request(request_id, state="cancelled")
            else:
                worker.request_cancel(request_id)
                request = store.get_request(request_id)

            self._write_json(200, request.as_dict())

        def _list_sessions(self) -> None:
            sessions = store.list_sessions()
            self._write_json(200, [s.as_dict() for s in sessions])

        def _list_session_requests(self, session_id: str) -> None:
            try:
                requests = store.list_session_requests(session_id)
            except NotFoundError as exc:
                raise ApiError(404, "not_found", str(exc))
            self._write_json(200, [r.as_dict() for r in requests])

    return Handler


def build_server(host: str, port: int, store: Store, opencode: OpenCodeClient, worker: Worker) -> ThreadingHTTPServer:
    handler_cls = make_handler(store, opencode, worker)
    return ThreadingHTTPServer((host, port), handler_cls)
