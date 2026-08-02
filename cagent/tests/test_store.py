from __future__ import annotations

import pytest

from cagent_api.store import Identity, NotFoundError, OwnershipError, Store


def test_create_then_continue_appends_to_same_session():
    store = Store()
    identity = Identity("node", "agpc-uuid", "agpc-serial")
    r1 = store.create_session_and_request("ses_1", identity, "first")
    r2 = store.continue_session("ses_1", identity, "second")

    assert r1.session_id == r2.session_id == "ses_1"
    assert r1.request_id != r2.request_id
    requests = store.list_session_requests("ses_1")
    assert [r.request_id for r in requests] == [r1.request_id, r2.request_id]


def test_continue_unknown_session_raises_not_found():
    store = Store()
    identity = Identity("node", "agpc-uuid", "agpc-serial")
    with pytest.raises(NotFoundError):
        store.continue_session("ses_missing", identity, "hi")


def test_continue_with_different_identity_raises_ownership_error():
    store = Store()
    owner = Identity("node", "agpc-uuid", "agpc-serial")
    other = Identity("node", "agstudio-uuid", "agstudio-serial")
    store.create_session_and_request("ses_1", owner, "first")
    with pytest.raises(OwnershipError):
        store.continue_session("ses_1", other, "second")


def test_get_request_not_found():
    store = Store()
    with pytest.raises(NotFoundError):
        store.get_request("req_missing")


def test_list_sessions_reflects_turn_count():
    store = Store()
    identity = Identity("human", "eiji-uuid", "eiji-serial")
    store.create_session_and_request("ses_1", identity, "first")
    store.continue_session("ses_1", identity, "second")
    sessions = store.list_sessions()
    assert len(sessions) == 1
    assert sessions[0].as_dict()["turn_count"] == 2
