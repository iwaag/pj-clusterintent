from __future__ import annotations

from cagent_api.evidence import EvidenceWriter
from cagent_api.evidence_cli import cmd_list, cmd_show


def test_cmd_list_prints_uuid_identity(tmp_path, capsys):
    evidence = EvidenceWriter(tmp_path)
    evidence.record_created("req_1", "ses_1", {"class": "node", "uuid": "agpc-uuid", "cert_serial": "s1"}, "hi", 0.0)

    cmd_list(evidence)

    out = capsys.readouterr().out
    assert "req_1" in out
    assert "node:agpc-uuid" in out
    assert "ses_1" in out


def test_cmd_show_prints_record_and_events(tmp_path, capsys):
    evidence = EvidenceWriter(tmp_path)
    evidence.record_created("req_1", "ses_1", {"class": "node", "uuid": "agpc-uuid", "cert_serial": "s1"}, "hi", 0.0)
    evidence.append_event("req_1", "completed", {"response": "ok"})

    cmd_show(evidence, "req_1")

    out = capsys.readouterr().out
    assert '"uuid": "agpc-uuid"' in out
    assert '"state": "completed"' in out
