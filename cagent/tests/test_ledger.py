from __future__ import annotations

import pytest

from cagent_api.ledger import ACTIVE, REVOKED, Ledger, NotRegisteredError

UUID = "c82421c3-c42a-4bea-91ce-7468ae8a249c"


def test_register_creates_active_entry(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    entry = ledger.register(UUID, "serial1", "fp1", "2027-01-01T00:00:00+00:00")
    assert entry.state == ACTIVE
    assert entry.uuid == UUID
    assert ledger.is_active("serial1")


def test_revoke_then_reactivate_round_trips(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    ledger.register(UUID, "serial1", "fp1", "2027-01-01T00:00:00+00:00")

    revoked = ledger.revoke("serial1")
    assert revoked.state == REVOKED
    assert revoked.revoked_at is not None
    assert not ledger.is_active("serial1")

    reactivated = ledger.reactivate("serial1")
    assert reactivated.state == ACTIVE
    assert reactivated.revoked_at is None
    assert ledger.is_active("serial1")


def test_unregistered_serial_is_not_active(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    assert ledger.get("nope") is None
    assert not ledger.is_active("nope")


def test_revoke_unregistered_serial_raises(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    with pytest.raises(NotRegisteredError):
        ledger.revoke("nope")


def test_reactivate_unregistered_serial_raises(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    with pytest.raises(NotRegisteredError):
        ledger.reactivate("nope")


def test_list_returns_all_entries_sorted_by_issued_at(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    ledger.register(UUID, "serial1", "fp1", "2027-01-01T00:00:00+00:00")
    ledger.register(UUID, "serial2", "fp2", "2027-01-01T00:00:00+00:00")
    entries = ledger.list()
    assert [e.serial for e in entries] == ["serial1", "serial2"]


def test_is_expired_uses_not_after(tmp_path):
    import datetime

    ledger = Ledger(tmp_path / "ledger.jsonl")
    ledger.register(UUID, "serial1", "fp1", "2020-01-01T00:00:00+00:00")
    assert ledger.is_expired("serial1", now=datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc))
    assert not ledger.is_expired("serial1", now=datetime.datetime(2019, 1, 1, tzinfo=datetime.timezone.utc))


def test_ledger_persists_across_instances_reading_same_file(tmp_path):
    path = tmp_path / "ledger.jsonl"
    Ledger(path).register(UUID, "serial1", "fp1", "2027-01-01T00:00:00+00:00")
    # A fresh Ledger instance (simulating a separate process, e.g. the CLI
    # writing while the API server reads) must see the same state.
    reloaded = Ledger(path)
    assert reloaded.is_active("serial1")
    reloaded.revoke("serial1")

    third = Ledger(path)
    assert not third.is_active("serial1")
