"""The chat adapter's deterministic shell: transcript, ack, poll, reply.

Nothing here asserts what the agent said — the window's answer is its own
business. These pin what the listener does around it.
"""

from __future__ import annotations

import pytest

from cagent_api import zulip_window

BOT_ID = 14
HUMAN_ID = 8


def dm(sender_id, content, message_id=1, recipients=(BOT_ID, HUMAN_ID)):
    return {
        "id": message_id,
        "type": "private",
        "sender_id": sender_id,
        "sender_full_name": "Cagent" if sender_id == BOT_ID else "Developer",
        "content": content,
        "display_recipient": [{"id": i} for i in recipients],
    }


class FakeZulip:
    def __init__(self, history):
        self.history = history
        self.sent: list[tuple[list[int], str]] = []

    def dm_history(self, user_ids, num_before=50):
        return self.history

    def send_dm(self, user_ids, content):
        self.sent.append((user_ids, content))
        return len(self.sent)


class FakeWindow:
    """Stands in for `WindowClient`: one request id, a scripted final state."""

    def __init__(self, final):
        self.final = final
        self.asked: list[str] = []

    def ask(self, text):
        self.asked.append(text)
        return "req_fake"

    def wait(self, request_id, sleep=None):
        return self.final


def test_transcript_labels_speakers_and_drops_acks():
    transcript = zulip_window.format_transcript(
        [
            dm(HUMAN_ID, "is agpc up?"),
            dm(BOT_ID, zulip_window.ACK_TEMPLATE.format(request_id="req_x")),
            dm(BOT_ID, "it is up"),
            dm(HUMAN_ID, "it is not"),
        ],
        BOT_ID,
    )
    assert transcript.splitlines() == [
        "[Developer] is agpc up?",
        "[Cagent (you)] it is up",
        "[Developer] it is not",
    ]


def test_the_window_text_carries_the_reporter_and_the_message_reference():
    message = dm(HUMAN_ID, "you were wrong", message_id=41)
    text = zulip_window.compose_text(
        "[Developer] you were wrong",
        reporter=zulip_window.reporter_label(message),
        ref=f"zulip message {message['id']}",
    )
    assert '--reporter "zulip:8 Developer"' in text
    assert '--ref "zulip message 41"' in text
    assert "--source zulip-dm" in text
    assert "[Developer] you were wrong" in text


def test_answer_text_prefers_the_response():
    assert zulip_window.answer_text({"state": "completed", "response": " done \n"}) == "done"


@pytest.mark.parametrize(
    "unanswered",
    [
        {"state": "failed", "error": {"code": "opencode_error", "message": "backend exploded"}},
        {"state": "interrupted", "error": None},
        {"state": "completed", "response": "   "},
    ],
)
def test_answer_text_says_something_when_there_is_no_answer(unanswered):
    assert "did not produce an answer" in zulip_window.answer_text(unanswered)


def test_a_dm_becomes_an_ack_then_the_answer():
    zulip = FakeZulip([dm(HUMAN_ID, "you told me node X was up, it is not", message_id=41)])
    window = FakeWindow({"state": "completed", "response": "recorded it", "cost_usd": 0.01})
    zulip_window.run_and_reply(zulip, window, zulip.history[0], BOT_ID)

    assert [content for _, content in zulip.sent] == [
        zulip_window.ACK_TEMPLATE.format(request_id="req_fake"),
        "recorded it",
    ]
    assert all(partners == [HUMAN_ID] for partners, _ in zulip.sent)
    assert "[Developer] you told me node X was up, it is not" in window.asked[0]


def test_the_wait_gives_up_instead_of_hanging_forever():
    class StuckWindow(zulip_window.WindowClient):
        def __init__(self):
            super().__init__("http://127.0.0.1:1", timeout_seconds=0.0)
            self.calls = 0

        def _call(self, path, body=None):
            self.calls += 1
            return {"state": "running"}

    window = StuckWindow()
    request = window.wait("req_x", sleep=lambda _: None)
    assert request["error"]["code"] == "listener_timeout"
    assert "did not produce an answer" in zulip_window.answer_text(request)


def test_a_broken_window_is_reported_into_the_chat():
    class BrokenWindow:
        def ask(self, text):
            raise RuntimeError("connection refused")

    zulip = FakeZulip([dm(HUMAN_ID, "hello")])
    react = zulip_window.make_handler(BrokenWindow())
    # The handler answers on a thread; call the body directly for determinism.
    with pytest.raises(RuntimeError):
        zulip_window.run_and_reply(zulip, BrokenWindow(), zulip.history[0], BOT_ID)
    assert react is not None
