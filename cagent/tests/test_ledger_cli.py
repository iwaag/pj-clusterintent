from __future__ import annotations

import pytest

from cagent_api import ledger_cli

UUID = "c82421c3-c42a-4bea-91ce-7468ae8a249c"


def test_register_list_show_revoke_reactivate_cycle(tmp_path, capsys):
    path = str(tmp_path / "ledger.jsonl")

    ledger_cli.main([
        "--path", path, "register", "--uuid", UUID, "--serial", "s1",
        "--fingerprint", "fp1", "--not-after", "2027-01-01T00:00:00+00:00",
    ])
    out = capsys.readouterr().out
    assert "registered serial=s1" in out

    ledger_cli.main(["--path", path, "list"])
    out = capsys.readouterr().out
    assert "serial=s1" in out and "state=active" in out

    ledger_cli.main(["--path", path, "show", "s1"])
    out = capsys.readouterr().out
    assert "uuid=" + UUID in out

    ledger_cli.main(["--path", path, "revoke", "s1"])
    out = capsys.readouterr().out
    assert "revoked serial=s1" in out

    ledger_cli.main(["--path", path, "show", "s1"])
    out = capsys.readouterr().out
    assert "state=revoked" in out

    ledger_cli.main(["--path", path, "reactivate", "s1"])
    out = capsys.readouterr().out
    assert "reactivated serial=s1" in out


def test_show_unknown_serial_exits(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    with pytest.raises(SystemExit):
        ledger_cli.main(["--path", path, "show", "nope"])


def test_revoke_unknown_serial_exits(tmp_path):
    path = str(tmp_path / "ledger.jsonl")
    with pytest.raises(SystemExit):
        ledger_cli.main(["--path", path, "revoke", "nope"])


def test_list_empty_ledger(tmp_path, capsys):
    path = str(tmp_path / "ledger.jsonl")
    ledger_cli.main(["--path", path, "list"])
    out = capsys.readouterr().out
    assert "empty" in out
