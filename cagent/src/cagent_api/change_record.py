"""One requested cluster change, kept in the Zulip conversation it happens in.

Until `refactor` p3 this was `plane.py`: a front that wrote
`requested_change.md` had it registered as an issue in the Plane project
`ClusterAdmin`, keyed on `"<channel>/<topic>"`. The chat carried the
conversation and Plane carried the record, so understanding one request meant
reading two systems and trusting they still agreed — the cost `refactor` p1
removed from agautolab and p2 from agforge.

**A conversation is its own record.** A change request becomes a topic in
cagent's own channel: the statement of the change is an ordinary post a person
can read, the discussion continues in the same topic, and the disposition is
recorded there too. Nothing about a request is anywhere but Zulip.

## Two conversations, and an anchor at each end

    <wherever it was asked>       the origin   → [selfnote][changerec] → the record
    <cagent's channel>/change-…   the record   → [selfnote][change]    → c<id>

Both links are **message ids**, never names. Resolving a topic renames it, a
human may rename it again, a message may be moved to another channel — the id
survives all of it, and `ZulipClient.message` answers with the conversation the
anchor is in *now*, `None` for one that was deleted. So a `change-…` topic
that was retired and replaced by a new topic of the same name is a **different
request**, a renamed origin still receives its link, and a deleted origin is
*absent* rather than whatever took its name.

The record topic is named `change-<stem>-o<origin message id>` for that same
reason: the stem is the requester's word for it and is reusable, the id is
not, so two requests raised under one name never merge into one conversation.

## Prose for people, notes for programs

The statement of the change is an ordinary post — that is what a person reads.
Everything a program must answer without guessing is a selfnote, which is
hidden from every chatlog and **never counts as somebody speaking**, so
writing the record buys nobody a run and replaying a serving cannot start one.

## Recording is not executing

Registering a change says what somebody wants done. It does not reconcile
anything, and nothing here touches the cluster: that distinction is the whole
reason the front writes `requested_change.md` rather than calling `nctl`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from agag.document import DocumentError, compose, split
from agag.selfnote import (
    Conversation,
    is_speech,
    note,
    parse_note,
)
from agag.zulip import (
    RESOLVED_TOPIC_PREFIX,
    ZulipClient,
    ZulipError,
    live_topic_name,
    topic_history_across_resolve,
)

from .instance import CHANGE_TOPIC_PREFIX, TOPIC_PREFIX, own_channel

#: cagent's own selfnote tags, beside the shared `rootchat` and `served`.
CHANGE_TAG = "change"
ORIGIN_TAG = "origin"
DOC_TAG = "doc"
STATE_TAG = "state"
#: Written into the **origin** conversation: where this topic's record is.
RECORD_TAG = "changerec"

#: A request's states. The newest note wins, so a request re-registered after
#: a decision is not read through the old verdict.
CHANGE_REQUESTED = "requested"
CHANGE_DONE = "done"
CHANGE_REJECTED = "rejected"
#: State words somebody **other than cagent** may write. A person deciding
#: what happens to a change request writes with their own credential, and a
#: reader that took states only from its own author would never see them.
EXTERNAL_STATES = ("accepted", "done", "rejected")

#: How much of a conversation one lookup reads. A change topic grows a post
#: per round of discussion and stays far below this.
HISTORY_MESSAGES = 500

#: Zulip accepts an over-long message and **truncates it silently**, appending
#: `[message truncated]` — the post succeeds and the record is quietly wrong.
#: A statement that would be truncated is refused here, where the caller can
#: say so, rather than half-recorded.
POST_LIMIT = 9000

__all__ = [
    "CHANGE_DONE",
    "CHANGE_REJECTED",
    "CHANGE_REQUESTED",
    "CHANGE_TOPIC_PREFIX",
    "EXTERNAL_STATES",
    "HISTORY_MESSAGES",
    "POST_LIMIT",
    "Change",
    "RecordError",
    "bare_topic",
    "change_label",
    "change_note",
    "change_topic_name",
    "compose_document",
    "doc_note",
    "is_change_topic",
    "origin_note",
    "own_change",
    "own_doc",
    "own_origin",
    "own_state",
    "read_change",
    "record_link",
    "record_note",
    "register_change",
    "set_state",
    "split_document",
    "stem_of",
]


class RecordError(RuntimeError):
    """A change record could not be read or written."""


# --- documents --------------------------------------------------------------


def split_document(text: str) -> tuple[str, str]:
    try:
        return split(text)
    except DocumentError as error:
        raise RecordError(str(error)) from error


def compose_document(title: str, body: str | None) -> str:
    return compose(title, body)


# --- names ------------------------------------------------------------------


def change_label(anchor_id: int) -> str:
    """`c5912` — the request's anchor id, worn as a name."""
    return f"c{int(anchor_id)}"


def bare_topic(topic: str) -> str:
    """A topic name without Zulip's `✔ ` resolve prefix."""
    return topic[len(RESOLVED_TOPIC_PREFIX):] if topic.startswith(RESOLVED_TOPIC_PREFIX) else topic


_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def stem_of(topic: str) -> str:
    """The requester's own word for a conversation, taken from its topic name.

    `cagent-agpc-dns` → `agpc-dns`. It is only a name: identity is the anchor
    id, and the stem exists so a human recognises the record in a channel
    listing.
    """
    name = bare_topic(str(topic or "")).strip()
    if name.startswith(TOPIC_PREFIX):
        name = name[len(TOPIC_PREFIX):]
    if name.startswith(CHANGE_TOPIC_PREFIX):
        name = name[len(CHANGE_TOPIC_PREFIX):]
    name = _UNSAFE.sub("-", name).strip("-")
    return name or "change"


def change_topic_name(stem: str, origin_id: int) -> str:
    """`change-<stem>-o<origin message id>`.

    The id is in the name so that two requests raised under one word do not
    merge: Zulip has exactly one topic per name in a channel, and a stem is
    the requester's to reuse.
    """
    return f"{CHANGE_TOPIC_PREFIX}{stem_of(stem)}-o{int(origin_id)}"


def is_change_topic(topic: str) -> bool:
    return bare_topic(topic).startswith(CHANGE_TOPIC_PREFIX)


def record_link(channel: str, topic: str) -> str:
    """Zulip's own link to a conversation — what a reader clicks."""
    return f"#**{channel}>{bare_topic(topic)}**"


# --- the notes --------------------------------------------------------------


def change_note(stem: str) -> str:
    """`[selfnote][change] <stem>` — this conversation is a change request.

    What matters is the note's **own message id**: that is the request.
    """
    return note(CHANGE_TAG, str(stem).strip() or "-")


def parse_change(content) -> str | None:
    return parse_note(content, CHANGE_TAG)


def origin_note(message_id: int) -> str:
    """`[selfnote][origin] <message id>` — the post that asked for this."""
    return note(ORIGIN_TAG, str(int(message_id)))


def parse_origin(content) -> int | None:
    return _as_id(parse_note(content, ORIGIN_TAG))


def record_note(anchor_id: int) -> str:
    """`[selfnote][changerec] <message id>` — where this topic's record is.

    Written into the **origin** conversation, so a later serving of it finds
    the record it already has instead of opening a second one. It is a
    selfnote, so it never makes cagent the last speaker in somebody else's
    conversation and never buys anybody a run.
    """
    return note(RECORD_TAG, str(int(anchor_id)))


def parse_record(content) -> int | None:
    return _as_id(parse_note(content, RECORD_TAG))


def doc_note(message_id: int) -> str:
    """`[selfnote][doc] <message id>` — which post states the change now.

    A statement is re-posted when the request is registered again, and the
    newest post in the topic is usually somebody talking, so "the statement"
    cannot be "the last thing said".
    """
    return note(DOC_TAG, str(int(message_id)))


def parse_doc(content) -> int | None:
    return _as_id(parse_note(content, DOC_TAG))


def state_note(state: str) -> str:
    """`[selfnote][state] <word>` — where this request has got to."""
    return note(STATE_TAG, str(state).strip())


def parse_state(content) -> str | None:
    return parse_note(content, STATE_TAG)


# --- reading a history ------------------------------------------------------


def _as_id(value) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def _earliest(messages, self_id: int, parse):
    """The first note of a kind this bot wrote, with its own message id.

    Earliest, because an identity is written once: a re-registration adds no
    second anchor, and a topic records the request it was opened for.
    """
    for message in messages:
        if message.get("sender_id") != self_id:
            continue
        found = parse(message.get("content"))
        if found is not None:
            return int(message.get("id", 0)), found
    return None


def _newest(messages, self_id: int, parse):
    """The last note of a kind this bot wrote. The newest one wins."""
    for message in reversed(list(messages)):
        if message.get("sender_id") != self_id:
            continue
        found = parse(message.get("content"))
        if found is not None:
            return found
    return None


def own_change(messages, self_id: int) -> tuple[int, str] | None:
    """`(anchor id, stem)` of the request this conversation is."""
    return _earliest(messages, self_id, parse_change)


def own_origin(messages, self_id: int) -> int | None:
    found = _earliest(messages, self_id, parse_origin)
    return None if found is None else found[1]


def own_record(messages, self_id: int) -> int | None:
    """The record anchor this conversation was already given, newest wins.

    Newest, because a record that was deleted is replaced by a fresh one and
    the second note is the true answer from then on.
    """
    return _newest(messages, self_id, parse_record)


def own_doc(messages, self_id: int) -> int | None:
    return _newest(messages, self_id, parse_doc)


def own_state(messages, self_id: int) -> str | None:
    """The newest state note, from cagent or — for `EXTERNAL_STATES` — anybody."""
    for message in reversed(list(messages)):
        found = parse_state(message.get("content"))
        if found is None:
            continue
        if message.get("sender_id") == self_id or found.strip().lower() in EXTERNAL_STATES:
            return found
    return None


# --- one request ------------------------------------------------------------


@dataclass(frozen=True)
class Change:
    """One change request, as its conversation currently reads."""

    anchor_id: int
    stem: str
    conversation: Conversation
    origin_id: int | None = None
    doc_id: int | None = None
    state: str | None = None

    @property
    def label(self) -> str:
        return change_label(self.anchor_id)

    @property
    def link(self) -> str:
        return record_link(self.conversation.channel, self.conversation.topic)


def conversation_of(client: ZulipClient, anchor_id: int) -> Conversation | None:
    """Where an anchor is **now**, or None when the message is gone.

    A deleted anchor is *absent*. That is a different answer from "a topic
    with that name exists", and every caller here relies on the difference.
    """
    message = client.message(int(anchor_id))
    if not message:
        return None
    channel = str(message.get("display_recipient") or "")
    topic = str(message.get("subject") or "")
    if not channel or not topic:
        return None
    return Conversation(channel, topic)


def read_change(client: ZulipClient, anchor_id: int, self_id: int) -> Change | None:
    """The request an anchor id names, read out of the conversation it is in."""
    where = conversation_of(client, anchor_id)
    if where is None:
        return None
    history = topic_history_across_resolve(
        client, where.channel, where.topic, HISTORY_MESSAGES
    )
    found = own_change(history, self_id)
    if found is None or found[0] != int(anchor_id):
        return None
    return Change(
        anchor_id=int(anchor_id),
        stem=found[1],
        conversation=where,
        origin_id=own_origin(history, self_id),
        doc_id=own_doc(history, self_id),
        state=own_state(history, self_id),
    )


def _post(client: ZulipClient, where: Conversation, text: str) -> int:
    if len(text) > POST_LIMIT:
        raise RecordError(
            f"the change statement is {len(text)} characters; Zulip truncates "
            f"over {POST_LIMIT} silently, so it is not recorded"
        )
    try:
        return int(client.send_to_channel(where.channel, where.topic, text))
    except ZulipError as error:
        raise RecordError(f"could not write the record in {where}: {error}") from error


def set_state(client: ZulipClient, change: Change, state: str) -> None:
    """Record where a request has got to, in its own conversation."""
    _post(client, change.conversation, state_note(state))


def _live(client: ZulipClient, where: Conversation) -> Conversation:
    """`where`, under the name it wears now — a resolve renames a topic."""
    return Conversation(where.channel, live_topic_name(client, where.channel, where.topic))


def _write_statement(
    client: ZulipClient, where: Conversation, title: str, body: str
) -> int:
    doc_id = _post(client, where, compose_document(title, body))
    _post(client, where, doc_note(doc_id))
    return doc_id


def register_change(
    client: ZulipClient,
    channel: str,
    topic: str,
    change_text: str,
    *,
    self_id: int,
    origin_id: int | None = None,
    history: list[dict] | None = None,
) -> str:
    """Record one front `requested_change.md` and say where it went.

    Three cases, and the difference between them is the whole of the "no
    duplicates" rule:

    - the topic being served **is** a change record → the statement is
      re-posted there, and the same conversation carries on;
    - the topic already **has** a record (an anchor cagent wrote into it, and
      the anchor still exists) → the statement is re-posted into that record;
    - otherwise a record is opened in cagent's own channel and the origin is
      given its anchor.

    The return value is the report line for the serving, carrying a link to
    the record.
    """
    title, body = split_document(change_text)
    here = Conversation(channel, topic)
    history = list(
        history
        if history is not None
        else topic_history_across_resolve(client, channel, topic, HISTORY_MESSAGES)
    )

    mine = own_change(history, self_id)
    if mine is not None:
        # This conversation is the record. Nothing new is opened for it —
        # replaying a serving here restates the change, it does not fork it.
        _write_statement(client, here, title, body)
        return f'restated {change_label(mine[0])} "{title}" here'

    existing = own_record(history, self_id)
    if existing is not None:
        change = read_change(client, existing, self_id)
        if change is not None:
            where = _live(client, change.conversation)
            _write_statement(client, where, title, body)
            return (
                f'restated {change.label} "{title}" in '
                f"{record_link(where.channel, where.topic)}"
            )
        # The anchor is gone: the record was deleted, so this is a fresh one
        # rather than whatever now wears its name.

    if origin_id is None:
        origin_id = _asking_message_id(history, self_id)
    if origin_id is None:
        raise RecordError(
            "there is no message in this topic to anchor the request to"
        )

    home = Conversation(own_channel(), change_topic_name(stem_of(topic), origin_id))
    anchor_id = _post(client, home, change_note(stem_of(topic)))
    _post(client, home, origin_note(origin_id))
    _write_statement(client, home, title, body)
    _post(client, home, state_note(CHANGE_REQUESTED))
    _post(client, here, record_note(anchor_id))
    return (
        f'recorded {change_label(anchor_id)} "{title}" in '
        f"{record_link(home.channel, home.topic)}"
    )


def _asking_message_id(history: list[dict], self_id: int) -> int | None:
    """The post this registration answers: the newest thing somebody said.

    Not simply the newest message — cagent's own ack and its own notes are
    transport, and anchoring to one of them would make the return destination
    a message cagent wrote to itself. Somebody else's last piece of speech is
    the request, and if that message is later deleted the origin is *absent*,
    which is the answer the plan asks for.
    """
    for message in reversed(list(history)):
        if message.get("sender_id") == self_id or not is_speech(message):
            continue
        return _as_id(message.get("id"))
    return None
