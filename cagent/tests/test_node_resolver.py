from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from cagent_api.node_resolver import NautobotNodeResolver, NodeResolverError

UUID = "c82421c3-c42a-4bea-91ce-7468ae8a249c"


def _stub_server(response_body: dict, expected_auth: str | None = None):
    captured = {}

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_POST(self):
            captured["path"] = self.path
            captured["auth"] = self.headers.get("Authorization")
            length = int(self.headers.get("Content-Length", "0"))
            captured["body"] = json.loads(self.rfile.read(length))
            payload = json.dumps(response_body).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    port = httpd.server_address[1]
    return httpd, thread, f"http://127.0.0.1:{port}", captured


def test_is_valid_true_for_active_node():
    httpd, thread, url, captured = _stub_server(
        {"data": {"desired_nodes": [{"id": UUID, "lifecycle": "ACTIVE"}]}}
    )
    try:
        resolver = NautobotNodeResolver(url, token="secret-token")
        assert resolver.is_valid(UUID) is True
        assert captured["path"] == "/api/graphql/"
        assert captured["auth"] == "Token secret-token"
        assert "desired_nodes" in captured["body"]["query"]
    finally:
        httpd.shutdown()


def test_is_valid_false_for_retired_node():
    httpd, thread, url, _ = _stub_server(
        {"data": {"desired_nodes": [{"id": UUID, "lifecycle": "RETIRED"}]}}
    )
    try:
        resolver = NautobotNodeResolver(url, token=None)
        assert resolver.is_valid(UUID) is False
    finally:
        httpd.shutdown()


def test_is_valid_false_for_unknown_uuid_pruned_node():
    httpd, thread, url, _ = _stub_server({"data": {"desired_nodes": []}})
    try:
        resolver = NautobotNodeResolver(url, token=None)
        assert resolver.is_valid(UUID) is False
    finally:
        httpd.shutdown()


def test_graphql_errors_raise_node_resolver_error():
    httpd, thread, url, _ = _stub_server({"errors": [{"message": "boom"}]})
    try:
        resolver = NautobotNodeResolver(url, token=None)
        with pytest.raises(NodeResolverError):
            resolver.is_valid(UUID)
    finally:
        httpd.shutdown()


def test_unreachable_host_raises_node_resolver_error():
    resolver = NautobotNodeResolver("http://127.0.0.1:1", token=None, timeout=1.0)
    with pytest.raises(NodeResolverError):
        resolver.is_valid(UUID)


def test_load_nautobot_connection_reads_token_from_env(tmp_path, monkeypatch):
    from cagent_api.node_resolver import load_nautobot_connection

    toml_path = tmp_path / "nctl.toml"
    toml_path.write_text('[nautobot]\nurl = "http://localhost:8000"\ntoken_env = "TEST_NAUTOBOT_TOKEN"\n')
    monkeypatch.setenv("TEST_NAUTOBOT_TOKEN", "env-token")

    url, token = load_nautobot_connection(toml_path)
    assert url == "http://localhost:8000"
    assert token == "env-token"


def test_load_nautobot_connection_falls_back_to_token_file(tmp_path, monkeypatch):
    from cagent_api.node_resolver import load_nautobot_connection

    monkeypatch.delenv("TEST_NAUTOBOT_TOKEN", raising=False)
    secret_path = tmp_path / "secret"
    secret_path.write_text("file-token\n")
    toml_path = tmp_path / "nctl.toml"
    toml_path.write_text(
        "[nautobot]\n"
        'url = "http://localhost:8000"\n'
        'token_env = "TEST_NAUTOBOT_TOKEN"\n'
        f'token_file = "{secret_path}"\n'
    )

    _, token = load_nautobot_connection(toml_path)
    assert token == "file-token"
