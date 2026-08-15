"""cagent's part of serving a `cagent-` topic: the front/operator shape.

The serving *discipline* — ack first, always answer, name the failed step,
the empty-topic guard, workspace numbering, chatlog formatting — lives in
`agag.topics` and is tested there. What is pinned here is only what cagent
decides: which files travel into which generation directory, which branch
the front's *files* select, and the order the answers reach the topic.

Same rule as agforge's suite: nothing asserts what an agent said.
"""

from __future__ import annotations

import pytest
from agag import topics
from agag.topics import GuideError

from cagent_api import topics_serve

BOT_ID = 14
HUMAN_ID = 8
CHANNEL = "general"
TOPIC = "cagent-hello"


def message(sender_id=HUMAN_ID, name="Developer", content="what runs on agpc?", id=1):
    return {
        "id": id,
        "type": "stream",
        "sender_id": sender_id,
        "sender_full_name": name,
        "display_recipient": CHANNEL,
        "subject": TOPIC,
        "content": content,
    }


class Client:
    email = "cagent-bot@example.invalid"

    def __init__(self, calls, history=None):
        self.calls = calls
        self.history = [message()] if history is None else history

    def whoami(self):
        self.calls.append(("whoami",))
        return {"user_id": BOT_ID, "full_name": "Cagent"}

    def topic_history(self, channel, topic, num_before):
        self.calls.append(("history", channel, topic, num_before))
        return self.history


def wire(monkeypatch, tmp_path, calls, *, front="let me check", operator="here it is",
         writes=()):
    monkeypatch.setattr(topics_serve, "TOPICS_ROOT", tmp_path / "topics")
    monkeypatch.setattr(topics_serve, "RECORDS_ROOT", tmp_path / "records")
    # Posting goes through the shared skeleton, so that is where it is caught.
    monkeypatch.setattr(
        topics,
        "topic_write",
        lambda topic, text, **kwargs: calls.append(("write", topic, text)) or "success",
    )

    def front_run(prompt, cwd):
        calls.append(("front", prompt, cwd))
        for name, body in writes:
            (cwd / name).write_text(body)
        return front

    def operator_run(cwd):
        calls.append(("operator", cwd))
        return operator

    monkeypatch.setattr(topics_serve, "run_front", front_run)
    monkeypatch.setattr(topics_serve, "run_operator", operator_run)
    guides = tmp_path / "guides"
    (guides / "front").mkdir(parents=True)
    (guides / "front" / "guide.md").write_text("FRONT GUIDE")
    (guides / "operator_read").mkdir()
    (guides / "operator_read" / "guide.md").write_text("OPERATOR GUIDE")
    monkeypatch.setattr(topics_serve, "GUIDES", guides)
    tools = tmp_path / "agent-tools"
    tools.mkdir()
    (tools / "toolset_nctl.md").write_text("# Description\ncagent --help\n")
    monkeypatch.setattr(topics_serve, "TOOLS", tools)


def gen_dir(tmp_path, number, role):
    return tmp_path / "topics" / CHANNEL / TOPIC / str(number) / role


# --- (a) no handoff files: one answer, nothing else -------------------------


def test_front_only_path_acks_answers_and_stops(monkeypatch, tmp_path):
    calls = []
    wire(monkeypatch, tmp_path, calls)

    topics_serve.handle_topic(Client(calls), CHANNEL, TOPIC)

    assert [call[0] for call in calls] == [
        "whoami", "write", "history", "front", "write", "history",
    ]
    assert calls[1][1:] == (TOPIC, topics_serve.SWEEP_ACK)
    assert calls[4][1:] == (TOPIC, "let me check")
    assert (gen_dir(tmp_path, 1, "front") / "chatlog.md").read_text() == (
        "[Developer] what runs on agpc?\n"
    )
    assert calls[3][2] == gen_dir(tmp_path, 1, "front")
    assert not gen_dir(tmp_path, 1, "operator").exists()


def test_the_front_prompt_is_the_placement_line_plus_its_own_guide(monkeypatch, tmp_path):
    calls = []
    wire(monkeypatch, tmp_path, calls)
    topics_serve.handle_topic(Client(calls), CHANNEL, TOPIC)
    prompt = next(call[1] for call in calls if call[0] == "front")
    assert prompt == (
        "The chatlog is placed in the working directory. "
        "You are 'Cagent' in the chatlog.\n\nFRONT GUIDE"
    )


# --- (c) an exception mid-way: `failed during …` is posted ------------------


def test_a_front_failure_names_its_step(monkeypatch, tmp_path):
    calls = []
    wire(monkeypatch, tmp_path, calls)

    def explode(prompt, cwd):
        raise topics_serve.ListenerError("agcode timed out")

    monkeypatch.setattr(topics_serve, "run_front", explode)
    topics_serve.handle_topic(Client(calls), CHANNEL, TOPIC)
    assert calls[-1][2] == "failed during front: agcode timed out"


# --- generations ------------------------------------------------------------


def test_generation_increments_once_per_serve_and_keeps_the_old_ones(monkeypatch, tmp_path):
    calls = []
    wire(monkeypatch, tmp_path, calls, writes=(("required_info.md", "which node?"),))
    topics_serve.handle_topic(Client(calls), CHANNEL, TOPIC)
    topics_serve.handle_topic(Client(calls), CHANNEL, TOPIC)

    assert gen_dir(tmp_path, 1, "front").is_dir()
    assert gen_dir(tmp_path, 2, "front").is_dir()
    # A previous generation's required_info.md stays where it is; cutting a
    # new N is what stops it from being re-executed.
    assert (gen_dir(tmp_path, 1, "operator") / "required_info.md").is_file()
    assert [call[1] for call in calls if call[0] == "operator"] == [
        gen_dir(tmp_path, 1, "operator"),
        gen_dir(tmp_path, 2, "operator"),
    ]


def test_an_empty_topic_costs_no_agent_run(monkeypatch, tmp_path):
    calls = []
    wire(monkeypatch, tmp_path, calls)
    topics_serve.handle_topic(Client(calls, history=[]), CHANNEL, TOPIC)
    assert not any(call[0] in {"front", "operator"} for call in calls)
    assert calls[-1][2] == topics_serve.EMPTY_REPLY


# --- cagent's own chatlog rule ----------------------------------------------


def test_our_acks_are_dropped_from_the_chatlog(monkeypatch, tmp_path):
    calls = []
    wire(monkeypatch, tmp_path, calls)
    history = [
        message(),
        message(sender_id=BOT_ID, name="Cagent", content=topics_serve.SWEEP_ACK),
        message(sender_id=BOT_ID, name="Cagent", content="agpc runs ollama"),
    ]
    topics_serve.handle_topic(Client(calls, history=history), CHANNEL, TOPIC)
    assert (gen_dir(tmp_path, 1, "front") / "chatlog.md").read_text() == (
        "[Developer] what runs on agpc?\n[Cagent (you)] agpc runs ollama\n"
    )


def test_a_human_quoting_an_ack_stays_in_the_chatlog(monkeypatch, tmp_path):
    calls = []
    wire(monkeypatch, tmp_path, calls)
    history = [message(content=topics_serve.SWEEP_ACK)]
    topics_serve.handle_topic(Client(calls, history=history), CHANNEL, TOPIC)
    assert topics_serve.SWEEP_ACK in (
        gen_dir(tmp_path, 1, "front") / "chatlog.md"
    ).read_text()


def test_guide_refuses_to_start_without_the_file(monkeypatch, tmp_path):
    monkeypatch.setattr(topics_serve, "GUIDES", tmp_path)
    with pytest.raises(GuideError):
        topics_serve.guide("front", "guide.md")
