"""cagent's change record: one request, one conversation, found by id.

What is pinned here is only what the record *decides* — where a statement is
written, when a second registration reuses a conversation instead of forking
it, and what happens when a name is reused or an anchor is deleted. The Zulip
mechanics are `agag.zulip`'s and are tested there.
"""

from __future__ import annotations

import pytest
from agag.selfnote import is_selfnote

from cagent_api import change_record
from cagent_api.change_record import RecordError

BOT_ID = 14
HUMAN_ID = 8
OWN_CHANNEL = "cagent-test1"
ORIGIN_CHANNEL = "general"
ORIGIN_TOPIC = "cagent-agpc-dns"

CHANGE = "# Point agpc at the new resolver\n\nIt still uses the old one.\n"
OTHER = "# Give agpc a second disk\n\nIt is out of room.\n"


class FakeZulip:
    """Just enough Zulip to be a conversation store: topics, ids, deletes."""

    def __init__(self):
        self.next_id = 100
        self.topics: dict[tuple[str, str], list[dict]] = {}
        self.by_id: dict[int, dict] = {}

    # --- the surface change_record uses ---
    def send_to_channel(self, channel, topic, content):
        self.next_id += 1
        message = {
            "id": self.next_id, "sender_id": BOT_ID, "sender_full_name": "Cagent",
            "display_recipient": channel, "subject": topic, "content": content,
        }
        self.topics.setdefault((channel, topic), []).append(message)
        self.by_id[message["id"]] = message
        return message["id"]

    def topic_history(self, channel, topic, num_before=50):
        return list(self.topics.get((channel, topic), []))[-num_before:]

    def message(self, message_id):
        return self.by_id.get(int(message_id))

    def stream_id(self, name):
        return abs(hash(name)) % 1000

    def channel_topics(self, stream_id):
        return [t for (c, t) in self.topics if self.stream_id(c) == stream_id]

    # --- what a person or the realm does to it ---
    def say(self, channel, topic, content, sender_id=HUMAN_ID):
        self.next_id += 1
        message = {
            "id": self.next_id, "sender_id": sender_id, "sender_full_name": "Developer",
            "display_recipient": channel, "subject": topic, "content": content,
        }
        self.topics.setdefault((channel, topic), []).append(message)
        self.by_id[message["id"]] = message
        return message["id"]

    def rename(self, channel, topic, new_topic):
        messages = self.topics.pop((channel, topic), [])
        for message in messages:
            message["subject"] = new_topic
        self.topics.setdefault((channel, new_topic), []).extend(messages)

    def delete_topic(self, channel, topic):
        for message in self.topics.pop((channel, topic), []):
            self.by_id.pop(message["id"], None)

    # --- reading a test's way around ---
    def visible(self, channel, topic):
        return [m for m in self.topic_history(channel, topic, 500)
                if not is_selfnote(m["content"])]

    def statements(self, channel, topic):
        """The posts cagent made that a person reads — the record itself."""
        return [m["content"] for m in self.visible(channel, topic)
                if m["sender_id"] == BOT_ID]

    def only_change_topic(self):
        names = sorted(t for (c, t) in self.topics if c == OWN_CHANNEL)
        assert len(names) == 1, names
        return names[0]


@pytest.fixture
def zulip(monkeypatch):
    monkeypatch.setattr(change_record, "own_channel", lambda *a, **k: OWN_CHANNEL)
    return FakeZulip()


def register(zulip, channel=ORIGIN_CHANNEL, topic=ORIGIN_TOPIC, text=CHANGE):
    return change_record.register_change(
        zulip, channel, topic, text, self_id=BOT_ID
    )


# --- a first registration ----------------------------------------------------


def test_a_change_becomes_a_topic_in_cagents_own_channel(zulip):
    asked = zulip.say(ORIGIN_CHANNEL, ORIGIN_TOPIC, "the resolver moved")

    line = register(zulip)

    name = zulip.only_change_topic()
    assert name == f"change-agpc-dns-o{asked}"
    assert f"#**{OWN_CHANNEL}>{name}**" in line
    # The statement is an ordinary post, readable by a person.
    visible = zulip.visible(OWN_CHANNEL, name)
    assert len(visible) == 1
    assert visible[0]["content"].startswith("# Point agpc at the new resolver")


def test_the_record_knows_what_it_is_and_where_it_came_from(zulip):
    asked = zulip.say(ORIGIN_CHANNEL, ORIGIN_TOPIC, "the resolver moved")
    register(zulip)
    name = zulip.only_change_topic()
    history = zulip.topic_history(OWN_CHANNEL, name, 500)

    anchor, stem = change_record.own_change(history, BOT_ID)
    assert stem == "agpc-dns"
    assert change_record.own_origin(history, BOT_ID) == asked
    assert change_record.own_state(history, BOT_ID) == change_record.CHANGE_REQUESTED
    assert change_record.own_doc(history, BOT_ID) == zulip.visible(OWN_CHANNEL, name)[0]["id"]

    change = change_record.read_change(zulip, anchor, BOT_ID)
    assert change.label == f"c{anchor}"
    assert change.conversation.as_pair() == (OWN_CHANNEL, name)


def test_the_origin_is_told_where_its_record_is_without_speaking_in_it(zulip):
    zulip.say(ORIGIN_CHANNEL, ORIGIN_TOPIC, "the resolver moved")
    register(zulip)
    name = zulip.only_change_topic()
    anchor, _ = change_record.own_change(
        zulip.topic_history(OWN_CHANNEL, name, 500), BOT_ID
    )

    origin = zulip.topic_history(ORIGIN_CHANNEL, ORIGIN_TOPIC, 500)
    assert change_record.own_record(origin, BOT_ID) == anchor
    # A selfnote is not speech: recording a change never buys anybody a run.
    assert zulip.visible(ORIGIN_CHANNEL, ORIGIN_TOPIC) == origin[:1]


def test_the_anchor_is_a_message_not_a_name(zulip):
    """The statement is anchored to what somebody said, not to cagent's ack."""
    asked = zulip.say(ORIGIN_CHANNEL, ORIGIN_TOPIC, "the resolver moved")
    zulip.send_to_channel(ORIGIN_CHANNEL, ORIGIN_TOPIC, "Message received.")
    register(zulip)
    name = zulip.only_change_topic()
    assert name.endswith(f"-o{asked}")


# --- registering again -------------------------------------------------------


def test_registering_the_same_topic_again_reuses_its_record(zulip):
    zulip.say(ORIGIN_CHANNEL, ORIGIN_TOPIC, "the resolver moved")
    register(zulip)
    name = zulip.only_change_topic()

    zulip.say(ORIGIN_CHANNEL, ORIGIN_TOPIC, "and it needs a second disk")
    line = register(zulip, text=OTHER)

    assert zulip.only_change_topic() == name  # no second conversation
    assert "restated" in line
    statements = zulip.statements(OWN_CHANNEL, name)
    assert len(statements) == 2
    assert statements[1].startswith("# Give agpc a second disk")


def test_registering_inside_the_record_restates_it_there(zulip):
    """Replaying a serving in the record itself must not fork the request."""
    zulip.say(ORIGIN_CHANNEL, ORIGIN_TOPIC, "the resolver moved")
    register(zulip)
    name = zulip.only_change_topic()

    zulip.say(OWN_CHANNEL, name, "make it the other resolver")
    line = register(zulip, channel=OWN_CHANNEL, topic=name, text=OTHER)

    assert zulip.only_change_topic() == name
    assert "here" in line
    assert len(zulip.statements(OWN_CHANNEL, name)) == 2


def test_a_reused_origin_name_is_a_different_request(zulip):
    """A topic name is the requester's to reuse; identity is the anchor id."""
    zulip.say(ORIGIN_CHANNEL, ORIGIN_TOPIC, "the resolver moved")
    register(zulip)
    first = zulip.only_change_topic()

    zulip.rename(ORIGIN_CHANNEL, ORIGIN_TOPIC, f"✔ {ORIGIN_TOPIC}")
    zulip.say(ORIGIN_CHANNEL, ORIGIN_TOPIC, "different thing, same name")
    register(zulip, text=OTHER)

    names = sorted(t for (c, t) in zulip.topics if c == OWN_CHANNEL)
    assert len(names) == 2 and first in names


# --- renames and deletions ---------------------------------------------------


def test_a_resolved_record_still_receives_the_restatement(zulip):
    zulip.say(ORIGIN_CHANNEL, ORIGIN_TOPIC, "the resolver moved")
    register(zulip)
    name = zulip.only_change_topic()
    zulip.rename(OWN_CHANNEL, name, f"✔ {name}")

    zulip.say(ORIGIN_CHANNEL, ORIGIN_TOPIC, "one more thing")
    line = register(zulip, text=OTHER)

    assert zulip.only_change_topic() == f"✔ {name}"
    assert f"#**{OWN_CHANNEL}>{name}**" in line
    assert len(zulip.statements(OWN_CHANNEL, f"✔ {name}")) == 2


def test_a_deleted_record_is_absent_not_whatever_took_its_name(zulip):
    zulip.say(ORIGIN_CHANNEL, ORIGIN_TOPIC, "the resolver moved")
    register(zulip)
    name = zulip.only_change_topic()
    zulip.delete_topic(OWN_CHANNEL, name)

    zulip.say(ORIGIN_CHANNEL, ORIGIN_TOPIC, "ask again")
    line = register(zulip, text=OTHER)

    assert "recorded" in line  # a fresh record, not a resurrection
    assert zulip.only_change_topic() != name


def test_a_change_nobody_asked_for_has_nothing_to_anchor_to(zulip):
    with pytest.raises(RecordError):
        register(zulip)


def test_a_statement_zulip_would_truncate_is_refused(zulip):
    zulip.say(ORIGIN_CHANNEL, ORIGIN_TOPIC, "the resolver moved")
    with pytest.raises(RecordError):
        register(zulip, text="# Big\n\n" + "x" * change_record.POST_LIMIT)
