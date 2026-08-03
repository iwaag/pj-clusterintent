"""cluster-agent API HTTP server. See p2/contract.md (identity is mTLS-derived;
see p1/contract.md for the resources/state-machine parts unchanged since Phase 1)."""

from __future__ import annotations

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .auth import AuthError
from .opencode_client import OpenCodeClient, OpenCodeError
from .store import Identity, NotFoundError, OwnershipError, Store, TERMINAL_STATES
from .worker import Worker

_ROUTE_REQUESTS = re.compile(r"^/requests$")
_ROUTE_SESSION_REQUESTS = re.compile(r"^/sessions/(?P<session_id>[^/]+)/requests$")
_ROUTE_REQUEST_GET = re.compile(r"^/requests/(?P<request_id>[^/]+)$")
_ROUTE_REQUEST_CANCEL = re.compile(r"^/requests/(?P<request_id>[^/]+)/cancel$")
_ROUTE_SESSIONS_LIST = re.compile(r"^/sessions$")
_ROUTE_UI_ROOT = re.compile(r"^/$")
_ROUTE_LLMS_TXT = re.compile(r"^/llms\.txt$")

_CHAT_HTML_PATH = Path(__file__).parent / "static" / "chat.html"
_LLMS_TXT_PATH = Path(__file__).parent / "static" / "llms.txt"


def _load_chat_html() -> bytes:
    """Read on every request rather than caching at import time — this is a
    handful of KB served rarely (once per browser tab load), and it keeps
    editing the static file during local development a no-restart change."""
    return _CHAT_HTML_PATH.read_bytes()


def _load_llms_txt() -> bytes:
    return _LLMS_TXT_PATH.read_bytes()


class ApiError(Exception):
    def __init__(self, status: int, code: str, message: str, request_id: str | None = None) -> None:
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.request_id = request_id


def make_handler(store: Store, opencode: OpenCodeClient, worker: Worker, authenticate, serve_ui: bool = False):
    """`authenticate(handler) -> Identity` is the mTLS identity/connect-time-check
    seam (p2/contract.md): production wires `auth.CertAuthenticator`
    (reads `handler.connection.getpeercert()`, checks the ledger and
    DesiredNode validity); tests inject a fake that needs no real TLS
    handshake (see tests/fakes.py).

    `serve_ui` gates `GET /` (the chat HTML, unauthenticated — the page
    itself carries no data, only the fetch calls it makes need the token).
    `main.py` passes `True` only for the human listener build_server() call
    (p4/contract.md: 'UI routes exist only on the human listener')."""

    class Handler(BaseHTTPRequestHandler):
        server_version = "cagent-api/0.0.1"

        def log_message(self, fmt: str, *args) -> None:  # quieter default logging
            pass

        def _identity(self) -> Identity:
            try:
                return authenticate(self)
            except AuthError as exc:
                raise ApiError(exc.status, exc.code, exc.message)

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

            if _ROUTE_LLMS_TXT.match(path):
                return self._serve_llms_txt()

            if serve_ui and _ROUTE_UI_ROOT.match(path):
                return self._serve_ui()

            m = _ROUTE_REQUEST_GET.match(path)
            if m:
                return self._get_request(m.group("request_id"))

            if _ROUTE_SESSIONS_LIST.match(path):
                return self._list_sessions()

            m = _ROUTE_SESSION_REQUESTS.match(path)
            if m:
                return self._list_session_requests(m.group("session_id"))

            raise ApiError(404, "not_found", f"no such route: GET {path}")

        def _serve_llms_txt(self) -> None:
            """Unauthenticated on both listeners — a discovery doc for agent
            consumers (llms.txt convention), same spirit as robots.txt: no
            data behind it, so no reason to gate it on identity/TLS mode."""
            body = _load_llms_txt()
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _serve_ui(self) -> None:
            body = _load_chat_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

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
            identity = self._identity()
            try:
                request = store.get_request(request_id)
            except NotFoundError as exc:
                raise ApiError(404, "not_found", str(exc), request_id=request_id)
            if identity.identity_class != "human" and request.identity.owner_key() != identity.owner_key():
                raise ApiError(403, "forbidden", "identity does not own this request", request_id=request_id)
            self._write_json(200, request.as_dict())

        def _cancel_request(self, request_id: str) -> None:
            identity = self._identity()
            try:
                request = store.get_request(request_id)
            except NotFoundError as exc:
                raise ApiError(404, "not_found", str(exc), request_id=request_id)
            if request.identity.owner_key() != identity.owner_key():
                raise ApiError(403, "forbidden", "identity does not own this request", request_id=request_id)

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
            identity = self._identity()
            if identity.identity_class == "human":
                sessions = store.list_sessions()
            else:
                sessions = [s for s in store.list_sessions() if s.identity.owner_key() == identity.owner_key()]
            self._write_json(200, [s.as_dict() for s in sessions])

        def _list_session_requests(self, session_id: str) -> None:
            identity = self._identity()
            try:
                requests = store.list_session_requests(session_id)
            except NotFoundError as exc:
                raise ApiError(404, "not_found", str(exc))
            if (
                requests
                and identity.identity_class != "human"
                and requests[0].identity.owner_key() != identity.owner_key()
            ):
                raise ApiError(403, "forbidden", "identity does not own this session")
            self._write_json(200, [r.as_dict() for r in requests])

    return Handler


def build_server(
    host: str,
    port: int,
    store: Store,
    opencode: OpenCodeClient,
    worker: Worker,
    authenticate,
    ssl_context=None,
    serve_ui: bool = False,
) -> ThreadingHTTPServer:
    handler_cls = make_handler(store, opencode, worker, authenticate, serve_ui=serve_ui)
    httpd = ThreadingHTTPServer((host, port), handler_cls)
    if ssl_context is not None:
        httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)
    return httpd
