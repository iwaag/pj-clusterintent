"""Thin client for the legacy OpenCode session API (see p1/opencode_api_notes.md).

Deliberately stdlib-only (urllib) — this is a loopback-only MVP with a
single, trusted peer (the dedicated cluster-agent OpenCode instance from
Step 2), not a general-purpose HTTP client.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass


class OpenCodeError(Exception):
    """Raised when OpenCode returns an unexpected response."""


@dataclass
class AssistantMessage:
    completed: bool
    text: str
    error_name: str | None
    is_final_step: bool


class OpenCodeClient:
    def __init__(self, base_url: str, directory: str, timeout: float = 15.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.directory = directory
        self.timeout = timeout

    def _url(self, path: str, **query: str) -> str:
        q = dict(query)
        q["directory"] = self.directory
        return f"{self.base_url}{path}?{urllib.parse.urlencode(q)}"

    def _request(self, method: str, path: str, body: dict | None = None, **query: str) -> dict | None:
        url = self._url(path, **query)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                raw = resp.read()
                if not raw:
                    return None
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            raise OpenCodeError(f"{method} {path} -> HTTP {exc.code}: {raw!r}") from exc
        except urllib.error.URLError as exc:
            raise OpenCodeError(f"{method} {path} -> {exc}") from exc

    def create_session(self, title: str) -> str:
        result = self._request("POST", "/session", body={"title": title})
        return result["id"]

    def prompt_async(self, session_id: str, text: str) -> None:
        self._request(
            "POST",
            f"/session/{session_id}/prompt_async",
            body={"parts": [{"type": "text", "text": text}]},
        )

    def list_messages(self, session_id: str) -> list[dict]:
        return self._request("GET", f"/session/{session_id}/message") or []

    def count_assistant_messages(self, session_id: str) -> int:
        return sum(
            1 for entry in self.list_messages(session_id)
            if entry["info"].get("role") == "assistant"
        )

    def latest_assistant_message(self, session_id: str) -> AssistantMessage | None:
        messages = self.list_messages(session_id)
        for entry in reversed(messages or []):
            info = entry["info"]
            if info.get("role") != "assistant":
                continue
            completed = "completed" in info.get("time", {})
            error = info.get("error")
            text = "".join(
                part.get("text", "")
                for part in entry.get("parts", [])
                if part.get("type") == "text"
            )
            # A multi-step tool-calling turn produces one assistant message
            # per step, each independently completed; only a step whose
            # `finish` is not "tool-calls" (or one that ended in an error,
            # e.g. abort) is the turn's actual end. Verified live: a
            # 5-step turn had `finish: "tool-calls"` on steps 1-4 and
            # `finish: "stop"` only on the final step. Treating step 1's
            # completion as the turn's completion previously produced an
            # empty response mid-turn.
            return AssistantMessage(
                completed=completed,
                text=text,
                error_name=error.get("name") if error else None,
                is_final_step=bool(error) or info.get("finish") != "tool-calls",
            )
        return None

    def abort(self, session_id: str) -> bool:
        result = self._request("POST", f"/session/{session_id}/abort")
        return bool(result)
