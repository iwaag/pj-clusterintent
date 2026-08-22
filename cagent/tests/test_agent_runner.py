"""The agent backend: session replay, per-request instructions, tool sets.

Nothing here talks to a model. The three things worth pinning are decisions
this module makes on its own — what history a turn carries, what a door is
offered, and what it refuses before running.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agag import agcode
from agag.agent_config import AgentConfigError

from cagent_api import agent_runner
from cagent_api.agent_runner import AgentRunner, build_runner, compose_task

CONFIG = Path(__file__).resolve().parents[1] / "agents.toml"


# --- session replay ---------------------------------------------------------


def test_a_first_turn_carries_no_prefix():
    assert compose_task("what is up?", []) == "what is up?"


def test_replay_puts_older_turns_first_and_the_message_last():
    task = compose_task(
        "and the second one?",
        [("first question", "first answer"), ("second question", "second answer")],
    )
    assert task.index("first question") < task.index("second question")
    assert task.endswith("=== THE CURRENT MESSAGE ===\nand the second one?")
    assert "first answer" in task and "second answer" in task


def test_replay_is_capped_by_turn_count_and_says_so():
    history = [(f"question-{i:02d}", f"answer-{i:02d}") for i in range(agent_runner.REPLAY_TURNS + 3)]
    task = compose_task("now", history)
    for dropped in range(3):
        assert f"question-{dropped:02d}" not in task
    for kept in range(3, agent_runner.REPLAY_TURNS + 3):
        assert f"question-{kept:02d}" in task
    assert "3 earlier turn(s) of this session are not shown" in task


def test_replay_is_capped_by_characters_and_says_so():
    """One enormous `nctl drift --json` answer must not crowd out the rest —
    and the agent is told it happened rather than silently forgetting."""
    history = [("small question", "x" * (agent_runner.REPLAY_CHARS + 10)), ("recent", "answer")]
    task = compose_task("now", history)
    assert "recent" in task and "small question" not in task
    assert "1 earlier turn(s) of this session are not shown" in task


def test_a_history_that_does_not_fit_at_all_degrades_to_the_message():
    history = [("q", "x" * (agent_runner.REPLAY_CHARS + 10))]
    assert compose_task("now", history) == "now"


# --- tool sets --------------------------------------------------------------


def test_the_window_is_offered_no_way_to_change_anything():
    names = [tool.name for tool in agent_runner.window_tools()]
    assert names == ["read", "list", "nctl", "record_incident", "list_incidents"]
    assert "run" not in names and "write" not in names


def test_the_authenticated_doors_keep_the_four_builtins():
    names = [tool.name for tool in agent_runner.authenticated_tools()]
    assert names == ["read", "write", "list", "run"]


def test_every_tool_table_is_well_formed():
    """agcode rejects duplicate names; building the table is the check."""
    for tools in (agent_runner.window_tools(), agent_runner.authenticated_tools()):
        table = agcode.tool_table(tools)
        for name, tool in table.items():
            assert tool.spec["name"] == name
            assert set(tool.spec) >= {"name", "description", "input_schema"}


# --- the destroy-class guard ------------------------------------------------


@pytest.mark.parametrize(
    "command",
    [
        "uv run --project nctl nctl reconcile RETIRED --allow-destroy --yes",
        "uv run --project nctl nctl prune",
        "pct destroy 109",
        "qm destroy 110",
        "pvesh delete /nodes/aghub/lxc/109",
        "mkfs.ext4 /dev/sda1",
        "wipefs -a /dev/sda",
        "zpool destroy tank",
        "echo hi && lvremove -f /dev/vg0/lv0",
        "ansible-playbook playbooks/proxmox/destroy_lxc.yml",
        "dd if=/dev/zero of=/dev/sda",
    ],
)
def test_destroy_class_commands_are_refused_before_running(tmp_path, command):
    """The one guard kept from the previous harness's permission file. It matches the
    whole command line, so a shell composition cannot smuggle one through."""
    result = agent_runner.guarded_run(tmp_path, command)
    assert result.startswith("refused:")


def test_ordinary_commands_still_run(tmp_path):
    (tmp_path / "marker.txt").write_text("here")
    result = json.loads(agent_runner.guarded_run(tmp_path, "ls"))
    assert result["exit_code"] == 0
    assert "marker.txt" in result["stdout"]


# The window's nctl tool moved to `readonly_nctl.py`, shared with the
# `cagent` CLI; its refusal tests moved with it (test_readonly_nctl.py).


# --- instructions and identity ----------------------------------------------


def test_instructions_are_read_per_request(tmp_path):
    instructions = tmp_path / "AGENTS.md"
    instructions.write_text("first version")
    runner = AgentRunner(
        agent=None, working_dir=tmp_path, instructions_path=instructions,
        tools=(), claude_allowed_tools="", turn_timeout=1,
    )
    assert runner.instructions() == "first version"
    instructions.write_text("second version")
    # No restart: the previous harness fixed these at process start, and a
    # stale file once hung a turn forever.
    assert runner.instructions() == "second version"


def test_a_missing_instructions_file_degrades_rather_than_raising(tmp_path):
    runner = AgentRunner(
        agent=None, working_dir=tmp_path, instructions_path=tmp_path / "absent.md",
        tools=(), claude_allowed_tools="", turn_timeout=1,
    )
    assert runner.instructions() == ""


def test_session_ids_are_cagents_own_and_unique(tmp_path):
    runner = AgentRunner(
        agent=None, working_dir=tmp_path, instructions_path=tmp_path / "a.md",
        tools=(), claude_allowed_tools="", turn_timeout=1,
    )
    ids = {runner.new_session_id() for _ in range(100)}
    assert len(ids) == 100
    assert all(i.startswith("ses_") for i in ids)


# --- the committed configuration --------------------------------------------


def _machine_overlay(tmp_path):
    """The machine facts every door needs, whatever backend it is pointed at.

    Which harness and model the committed config chooses is not pinned here:
    Agent != Model, so a backend swap is a configuration change and must not
    read as a test failure. What is pinned is that every door still resolves
    and still answers as itself.
    """
    claude = tmp_path / "claude"
    claude.write_text("#!/bin/sh\nexit 0\n")
    claude.chmod(0o755)
    overlay = tmp_path / "agents.local.toml"
    overlay.write_text(
        'schema = "ag.agent-config.v1"\n\n[local.provider.ollama]\n'
        'base_url = "http://ollama.example:11434"\n\n'
        f'[local.harness.claude_code]\ncommand = "{claude}"\n'
    )
    return overlay


def test_the_committed_config_resolves_all_three_doors(tmp_path):
    overlay = _machine_overlay(tmp_path)
    for role in ("node", "human", "front"):
        runner = build_runner(
            role, config_path=CONFIG, overlay_path=overlay, working_dir=tmp_path,
            instructions_path=tmp_path / "a.md", turn_timeout=1,
        )
        identity = runner.identity()
        assert identity["role"] == role
        assert identity["profile"]
        assert identity["harness"] and identity["model"]


def test_only_the_front_role_gets_the_window_tools(tmp_path):
    """`front` is the renamed window role; the `/window` route keeps serving
    the strictly-smaller tool set through it."""
    overlay = _machine_overlay(tmp_path)
    kwargs = dict(config_path=CONFIG, overlay_path=overlay, working_dir=tmp_path,
                  instructions_path=tmp_path / "a.md", turn_timeout=1)
    window = build_runner("front", **kwargs)
    human = build_runner("human", **kwargs)
    assert "run" not in [t.name for t in window.tools]
    assert "run" in [t.name for t in human.tools]


def test_an_unknown_role_fails_loudly(tmp_path):
    with pytest.raises(AgentConfigError):
        build_runner(
            "nobody", config_path=CONFIG, overlay_path=tmp_path / "absent.toml",
            working_dir=tmp_path, instructions_path=tmp_path / "a.md", turn_timeout=1,
        )
