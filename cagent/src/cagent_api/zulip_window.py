"""The Cagent bot's chat entrance: a Zulip DM becomes one `POST /window`.

Deliberately dumb, like agforge's listener: no queue persistence, no delivery
guarantees, one answer per message. A DM that arrives while this is down is
lost and the sender resends.

It holds no cluster capability of its own — it is an adapter between Zulip and
the window's HTTP door, so everything it can cause is bounded by the window's
tool set. The mechanics of the Zulip side live in `agag.zulip`.
"""

from __future__ import annotations

import json
import os
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

from agag.zulip import ZulipClient, dm_partners, log

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ZULIP_ENV = REPO_ROOT / ".local" / "zulip" / "cagent.env"
DEFAULT_WINDOW_URL = "http://127.0.0.1:8790"

HISTORY_MESSAGES = 50
ACK_PREFIX = "Got it — thinking."
ACK_TEMPLATE = ACK_PREFIX + " (request `{request_id}`)"
POLL_INTERVAL_SECONDS = 3.0
TERMINAL_STATES = {"completed", "failed", "cancelled", "interrupted"}

TEXT_TEMPLATE = """\
This message arrived as a Zulip direct message. You are talking with someone in
a chat window, so answer like a chat reply: short, plain, no preamble.

If this reports a defect or a wrong answer, record it with
`uv run cagent/window/incident.py` using exactly these values:
`--reporter "{reporter}" --source zulip-dm --ref "{ref}"`.

Recent conversation, oldest first, exactly as the participants see it on
screen. Lines marked "(you)" are your own earlier replies:

{transcript}

The last line is what to answer now; the earlier lines are context.
"""


def format_transcript(messages: list[dict], self_id: int) -> str:
    lines = []
    for message in messages:
        content = str(message.get("content", "")).strip()
        if message.get("sender_id") == self_id and content.startswith(ACK_PREFIX):
            continue  # our own "thinking" acks are noise, not conversation
        speaker = message.get("sender_full_name") or f"user{message.get('sender_id')}"
        if message.get("sender_id") == self_id:
            speaker = f"{speaker} (you)"
        lines.append(f"[{speaker}] {content}")
    return "\n".join(lines)


def compose_text(transcript: str, reporter: str, ref: str) -> str:
    return TEXT_TEMPLATE.format(transcript=transcript, reporter=reporter, ref=ref)


def reporter_label(message: dict) -> str:
    """Who to credit a report to. Numeric id first: this realm hides emails."""
    return f"zulip:{message.get('sender_id')} {message.get('sender_full_name') or ''}".strip()


def answer_text(request: dict) -> str:
    """What to send back to the chat, including when the turn did not work."""
    if request.get("state") == "completed" and (request.get("response") or "").strip():
        return request["response"].strip()
    error = request.get("error") or {}
    detail = error.get("message") or request.get("state") or "no answer"
    return f"That turn did not produce an answer ({detail})."


class WindowClient:
    """`POST /window` + poll, over plain HTTP — the window has no auth."""

    def __init__(self, base_url: str = DEFAULT_WINDOW_URL, timeout_seconds: float = 420.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _call(self, path: str, body: dict | None = None) -> dict:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            f"{self.base_url}{path}", data=data, method="POST" if data else "GET",
            headers={"Content-Type": "application/json"} if data else {},
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))

    def ask(self, text: str) -> str:
        return self._call("/window", {"text": text})["request_id"]

    def wait(self, request_id: str, sleep=time.sleep) -> dict:
        deadline = time.monotonic() + self.timeout_seconds
        while True:
            request = self._call(f"/requests/{request_id}")
            if request.get("state") in TERMINAL_STATES:
                return request
            if time.monotonic() > deadline:
                request["error"] = {
                    "code": "listener_timeout",
                    "message": f"still {request.get('state')} after {self.timeout_seconds:.0f}s",
                }
                return request
            sleep(POLL_INTERVAL_SECONDS)


def run_and_reply(zulip: ZulipClient, window: WindowClient, message: dict, self_id: int) -> None:
    partners = dm_partners(message, self_id)
    history = zulip.dm_history(partners, num_before=HISTORY_MESSAGES)
    text = compose_text(
        format_transcript(history, self_id),
        reporter=reporter_label(message),
        ref=f"zulip message {message.get('id')}",
    )
    request_id = window.ask(text)
    # The ack goes out after the request exists, so it can name it, and before
    # the wait, because a silent chat reads as broken.
    zulip.send_dm(partners, ACK_TEMPLATE.format(request_id=request_id))
    log(f"window request {request_id}: {len(history)} messages of context, partners={partners}")
    request = window.wait(request_id)
    log(
        f"window request {request_id}: state={request.get('state')} "
        f"cost_usd={request.get('cost_usd')} backend={request.get('backend')}"
    )
    zulip.send_dm(partners, answer_text(request))


def make_handler(window: WindowClient):
    """Listener handler: answer each DM on its own thread, so a slow turn does
    not stop the loop from seeing the next message."""

    def react(zulip: ZulipClient, message: dict, self_id: int) -> None:
        if not dm_partners(message, self_id):
            return

        def worker() -> None:
            try:
                run_and_reply(zulip, window, message, self_id)
            except Exception as error:
                log(f"window run failed: {error!r}")
                try:
                    zulip.send_dm(
                        dm_partners(message, self_id),
                        f"Something broke between the chat and the window: {error}",
                    )
                except Exception as send_error:
                    log(f"could not report the failure to the chat: {send_error!r}")

        threading.Thread(target=worker, daemon=True).start()

    return react


def log_only(zulip: ZulipClient, message: dict, self_id: int) -> None:
    """`CAGENT_ZULIP_LOG_ONLY=1`: watch without spending a turn."""
    log(
        f"DM #{message.get('id')} from {message.get('sender_full_name')!r} "
        f"(id={message.get('sender_id')}): {str(message.get('content', ''))[:200]!r}"
    )


def main() -> None:
    from agag.zulip import serve

    env_path = Path(os.environ.get("CAGENT_ZULIP_ENV", str(DEFAULT_ZULIP_ENV)))
    window = WindowClient(
        os.environ.get("CAGENT_WINDOW_URL", DEFAULT_WINDOW_URL),
        timeout_seconds=float(os.environ.get("CAGENT_WINDOW_TIMEOUT_SECONDS", "420")),
    )
    handler = log_only if os.environ.get("CAGENT_ZULIP_LOG_ONLY") == "1" else make_handler(window)
    zulip = ZulipClient.from_env(env_path)
    log(f"cagent zulip listener starting (window={window.base_url}, handler={handler.__name__})")
    try:
        serve(zulip, handler)
    except KeyboardInterrupt:
        log("stopped")


if __name__ == "__main__":
    main()
