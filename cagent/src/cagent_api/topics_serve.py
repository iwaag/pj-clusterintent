"""Serve one `cagent-` topic: front agent, then file-driven handoffs.

The discipline — ack, generation workspace, chatlog, always post back, and
re-serve when a human spoke during the run — is `agag.topics.serve_topic`,
shared with agautolab and agforge. What is cagent's own is the two-role
shape over one generation:

    <N>/front/     chatlog.md         → front run → its answer, posted
    <N>/operator/  required_info.md   → operator run → its answer, posted
                   tools/toolset_nctl.md
                   (requested_change.md → a change record in cagent's channel)

What the front *wrote* drives the handoffs, never what it said — its chat
answer is relayed verbatim and never parsed. Generation directories are
never deleted: cutting a new `N` is precisely what stops a previous
generation's `required_info.md` from being re-executed; leftovers are
evidence, not garbage.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from agag.topics import (
    TopicResult,
    chatlog_path,
    chatlog_placement,
    format_chatlog,
    generation_dir as shared_generation_dir,
    guide as shared_guide,
    next_generation,
    next_record_path,
    prompt_with_guide,
    serve_topic,
    topic_workspace as shared_topic_workspace,
)
from agag.zulip import ZulipClient, ZulipError, log

from .change_record import RecordError, register_change as record_change
from .instance import CHANGE_TOPIC_PREFIX, TOPIC_PREFIX
from .role_run import CAGENT_ROOT, REPO_ROOT, run_role

TOPICS_ROOT = REPO_ROOT / ".local" / "topics"
GUIDES = CAGENT_ROOT / "agent" / "guides"
TOOLS = CAGENT_ROOT / "agent" / "tools"
RECORDS_ROOT = REPO_ROOT / ".local" / "agent"

# The common sweep ack (shared wording across agents). Posted synchronously
# on a topic match: it makes this bot the last poster, so the pull loop stops
# re-matching the topic while the run is in flight.
SWEEP_ACK = "Message received. Please wait for the reply."

EMPTY_REPLY = "There is nothing in this topic to answer yet."

# The front only reads and writes text; the operator's nctl calls can each
# take up to two minutes, so it gets the wider budget.
FRONT_TIMEOUT_SECONDS = 360
OPERATOR_TIMEOUT_SECONDS = 900

REQUIRED_INFO = "required_info.md"
REQUESTED_CHANGE = "requested_change.md"
TOOLSET_NCTL = "toolset_nctl.md"
TOOLS_DIR = "tools"

__all__ = [
    "CHANGE_TOPIC_PREFIX",
    "TOPIC_PREFIX",
    "ListenerError",
    "front_prompt",
    "generation_dir",
    "guide",
    "handle_handoffs",
    "handle_topic",
    "run_front",
    "run_operator",
    "serve",
    "topic_workspace",
]


class ListenerError(RuntimeError):
    """One cagent-topic workflow could not complete."""


def topic_workspace(channel: str, topic: str) -> Path:
    return shared_topic_workspace(TOPICS_ROOT, channel, topic)


def generation_dir(channel: str, topic: str, number: int, role: str) -> Path:
    return shared_generation_dir(TOPICS_ROOT, channel, topic, number, role)


def guide(*parts: str) -> str:
    return shared_guide(GUIDES, *parts)


def is_ack(content: str) -> bool:
    """Our own transport noise, which is not conversation."""
    return content == SWEEP_ACK


def front_prompt(bot_name: str) -> str:
    return prompt_with_guide([chatlog_placement(bot_name)], guide("front", "guide.md"))


def _run(role: str, prompt: str, cwd: Path, timeout: float) -> str:
    record = next_record_path(RECORDS_ROOT / role)
    output, _, exit_code = run_role(role, prompt, cwd=cwd, timeout=timeout, record=record)
    if exit_code != 0:
        raise ListenerError(f"{role} run exited {exit_code}: {output.strip()[:500]}")
    return output.strip()


def run_front(prompt: str, cwd: Path) -> str:
    return _run("front", prompt, cwd, FRONT_TIMEOUT_SECONDS)


def run_operator(cwd: Path) -> str:
    return _run("operator", guide("operator_read", "guide.md"), cwd, OPERATOR_TIMEOUT_SECONDS)


def register_change(context, change: Path) -> str:
    """Record one `requested_change.md`, in the conversation it belongs to.

    Wrapped so the whole record route stays behind one name here — the same
    seam `plane.py` used to sit behind, now leading to Zulip.
    """
    return record_change(
        context.client,
        context.channel,
        context.topic,
        change.read_text(encoding="utf-8"),
        self_id=context.self_id,
        history=context.history,
    )


def handle_handoffs(context, front_dir: Path, number: int) -> list[str]:
    """The file-driven branches, after the front's answer is already posted.

    Both files present in one serving are processed, and **independently**:
    a registration that fails is reported as its own section and the
    observation still runs. They were sequential once, and a raised exception
    in the first branch meant the person who asked to be told *and* shown
    got neither.
    """
    channel, topic = context.channel, context.topic
    sections: list[str] = []

    change = front_dir / REQUESTED_CHANGE
    if change.is_file():
        try:
            sections.append(register_change(context, change))
        except (RecordError, ZulipError) as error:
            sections.append(f"the change could not be recorded: {error}")

    required = front_dir / REQUIRED_INFO
    if required.is_file():
        operator_dir = generation_dir(channel, topic, number, "operator")
        shutil.copyfile(required, operator_dir / REQUIRED_INFO)
        tools_dir = operator_dir / TOOLS_DIR
        tools_dir.mkdir(exist_ok=True)
        shutil.copyfile(TOOLS / TOOLSET_NCTL, tools_dir / TOOLSET_NCTL)
        # The operator's answer travels verbatim: answers are chat posts,
        # instructions are files, and nothing parses a role's chat answer.
        sections.append(run_operator(operator_dir))

    return sections


def serve(context) -> TopicResult:
    """cagent's part of one serving: the front run, then the handoffs."""
    number = next_generation(topic_workspace(context.channel, context.topic))
    front_dir = generation_dir(context.channel, context.topic, number, "front")
    chatlog_path(front_dir).write_text(
        format_chatlog(context.history, context.self_id, drop=is_ack), encoding="utf-8"
    )

    context.step = "front"
    answer = run_front(front_prompt(context.bot_name), front_dir)
    # Posted on its own, before any handoff: the front's answer is the
    # conversational reply, and the operator can take minutes.
    context.post(answer)

    context.step = "handoffs"
    return TopicResult(handle_handoffs(context, front_dir, number))


def handle_topic(client: ZulipClient, channel: str, topic: str) -> None:
    log(f"cagent topic {channel!r}/{topic!r}")
    serve_topic(
        client, channel, topic, serve,
        ack_text=SWEEP_ACK,
        empty_reply=EMPTY_REPLY,
    )
