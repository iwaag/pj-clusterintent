"""The topic-flow role runner: grants, PATH handover, and record writing.

Nothing here launches a real harness; what is pinned is what `role_run`
decides on its own — which grant each role gets, how the `cagent` CLI
becomes reachable, and that a run leaves an `ag.agent-run.v1` record.
"""

from __future__ import annotations

import json
import os

from agag.harness import HarnessResult

from cagent_api import role_run
from cagent_api.role_run import ROLE_ALLOWED_TOOLS, run_role, tool_environment


def test_both_topic_roles_carry_a_claude_grant():
    """A role missing from the table gets no --allowedTools and claude_code
    waits on an interactive permission prompt until the timeout."""
    assert set(ROLE_ALLOWED_TOOLS) == {"front", "operator"}


def test_the_front_writes_files_and_gets_no_shell():
    grant = ROLE_ALLOWED_TOOLS["front"]
    assert "Write" in grant and "Edit" in grant
    assert "Bash" not in grant


def test_the_operator_gets_only_the_cagent_cli_as_a_shell():
    grant = ROLE_ALLOWED_TOOLS["operator"].split(",")
    assert "Bash(cagent:*)" in grant
    assert not any(g.startswith("Bash") and g != "Bash(cagent:*)" for g in grant)
    assert "Write" not in grant and "Edit" not in grant


def test_neither_role_is_read_only_under_agcode():
    """agcode's read-only preset drops `run`: the front could never write
    `required_info.md`, and the operator could never run the cagent CLI."""
    assert role_run._agcode_args("front") == []
    assert role_run._agcode_args("operator") == []


def test_tool_environment_prepends_the_scripts_dir(tmp_path):
    environment = tool_environment(tmp_path)
    assert environment["PATH"].split(os.pathsep)[0] == str(tmp_path)
    assert tool_environment(tmp_path / "absent") == {}


def test_run_role_uses_the_grant_and_writes_the_record(monkeypatch, tmp_path):
    seen = {}

    def fake_resolve(role, profile_override=None):
        class Agent:
            harness = "fake"
        seen["role"] = role
        return Agent()

    def fake_run(agent, prompt, *, cwd, timeout, allowed_tools, extra_args, transcript_path):
        seen.update(prompt=prompt, cwd=cwd, allowed_tools=allowed_tools)
        return HarnessResult("the answer", 0, {"role": "operator", "outcome": "done"})

    monkeypatch.setattr(role_run, "resolve_cagent_role", fake_resolve)
    monkeypatch.setattr(role_run, "run_harness", fake_run)

    record = tmp_path / "run-0001.json"
    output, run_record, exit_code = run_role(
        "operator", "do it", cwd=tmp_path, timeout=5, record=record,
    )
    assert (output, exit_code) == ("the answer", 0)
    assert run_record["schema"] == "ag.agent-run.v1"
    assert seen["allowed_tools"] == ROLE_ALLOWED_TOOLS["operator"]
    written = json.loads(record.read_text())
    assert written["schema"] == "ag.agent-run.v1"
    assert written["request_id"] == "run-0001"
    assert written["outcome"] == "done"
