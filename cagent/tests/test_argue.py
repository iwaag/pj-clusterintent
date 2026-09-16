"""cagent in an argue (`argue` p1): the mention route answers an argue
invitation through the shared participation, with the read-only cluster
toolset beside the chatlog, and ignores every other mention."""

from pathlib import Path

from cagent_api import argue


class Client:
    def whoami(self):
        return {"user_id": 14, "full_name": "Cagent"}


def test_an_argue_invitation_is_answered_by_the_shared_participation(monkeypatch):
    seen = {}
    monkeypatch.setattr(argue, "participate", lambda client, channel, topic, **kw: seen.update(kw, topic=topic) or [1])
    monkeypatch.setattr(argue, "role_context", lambda: "ROLE")
    argue.handle_mention(Client(), "argue", "argue-fish")
    assert seen["topic"] == "argue-fish" and seen["run"] is argue.run_argue and seen["spec"] is argue.SPEC


def test_a_mention_elsewhere_is_ignored(monkeypatch):
    monkeypatch.setattr(argue, "participate", lambda *a, **kw: (_ for _ in ()).throw(AssertionError("ran")))
    argue.handle_mention(Client(), "general", "hello")


def test_the_argue_run_places_the_cluster_toolset_beside_the_chatlog(monkeypatch, tmp_path):
    seen = {}

    def run_role(role, prompt, *, cwd, timeout, record=None, transcript=None, **kw):
        seen.update(role=role, cwd=cwd, record=record)
        return "cluster says", {}, 0

    monkeypatch.setattr(argue, "run_role", run_role)
    monkeypatch.setattr(argue, "RECORDS_ROOT", tmp_path / "records")
    assert argue.run_argue("PROMPT", tmp_path / "ws", None) == "cluster says"
    assert seen["role"] == "argue" and (tmp_path / "ws" / "tools" / "toolset_nctl.md").is_file()
    assert seen["record"].parent == tmp_path / "records" / "argue"


def test_the_argue_role_has_the_operator_s_read_only_grant():
    from cagent_api.role_run import ROLE_ALLOWED_TOOLS

    assert ROLE_ALLOWED_TOOLS["argue"] == "Read,Glob,Grep,Bash(cagent:*)"
