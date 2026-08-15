"""Resolve a cagent topic-flow role and launch its configured harness.

The same shape as agforge's `role_run`: one function that goes from a role
name to a finished run plus its `ag.agent-run.v1` record, and one table of
per-role tool grants beside it. Everything a role may touch is decided here,
not at the call site.

This is the out-of-process runner for the `cagent-` topic flow. The
in-process runner (`agent_runner.py`) keeps serving the `/window` + DM path
unchanged; a role served there gets its curated tool objects, a role served
here gets a harness subprocess in its own workspace, with `scripts/` on PATH.
"""

from __future__ import annotations

import os
from dataclasses import replace
from pathlib import Path

from agag.agent_config import ResolvedAgent, load_config, resolve_role
from agag.harness import run_harness, write_run_record

REPO_ROOT = Path(__file__).resolve().parents[3]
CAGENT_ROOT = REPO_ROOT / "cagent"
AGENTS_CONFIG = CAGENT_ROOT / "agents.toml"
AGENTS_LOCAL_CONFIG = CAGENT_ROOT / ".local" / "agents.local.toml"
SCRIPTS_DIR = CAGENT_ROOT / "scripts"

# A role missing from this table gets no `--allowedTools` at all from
# `build_argv`, and claude_code then sits waiting for an interactive
# permission answer until the timeout. Every new role belongs here, even
# while its profile is `local`.
ROLE_ALLOWED_TOOLS = {
    # The front converses and writes handoff files in its workspace. No Bash:
    # nctl is not its to touch — that is the whole point of the split.
    "front": "Read,Write,Edit,Glob,Grep",
    # The operator reads its workspace and runs the read-only `cagent` CLI,
    # reached bare through PATH. Nothing it is offered mutates the cluster.
    "operator": "Read,Glob,Grep,Bash(cagent:*)",
}

# The roles that only read, under the agcode harness: agcode has no
# permission engine, so a read-only role is handed the `read-only` tool
# preset (read/list — no run, no write). Deliberately empty this phase:
# the front must write handoff files, and the operator's whole job is
# running the `cagent` CLI, which needs agcode's `run` tool. Under
# claude_code the per-role grants above carry the same intent instead.
READONLY_ROLES: frozenset[str] = frozenset()


def _agcode_args(role: str) -> list[str]:
    return ["--tools", "read-only"] if role in READONLY_ROLES else []


def tool_environment(scripts_dir: Path | None = None) -> dict[str, str]:
    """The host-local tool handover: PATH, and nothing else.

    `run_harness` launches with `{**os.environ, **agent.environment}`, so this
    is where the `cagent` CLI becomes reachable by its bare name from a role's
    workspace — which is what `toolset_nctl.md` and the operator guide assume.
    """
    directory = scripts_dir if scripts_dir is not None else SCRIPTS_DIR
    if not directory.is_dir():
        return {}
    return {"PATH": os.pathsep.join([str(directory), os.environ.get("PATH", "")])}


def resolve_cagent_role(
    role: str,
    *,
    profile_override: str | None = None,
    check_available: bool = True,
    config_path: Path | None = None,
    overlay_path: Path | None = None,
) -> ResolvedAgent:
    """Resolve one role against cagent's config pair, with its tool handover.

    The config pair is an argument, not a fixed fact: a caller that owns its
    own pair (a test pointed at the `stub` profile) passes it, and nothing
    here can silently fall back to the committed config and launch a real,
    paid harness.
    """
    config, overlay = load_config(
        config_path or AGENTS_CONFIG,
        AGENTS_LOCAL_CONFIG if overlay_path is None else overlay_path,
    )
    agent = resolve_role(
        config, overlay, role,
        profile_override=profile_override,
        check_available=check_available,
    )
    return replace(agent, environment={**agent.environment, **tool_environment()})


def run_role(
    role: str,
    prompt: str,
    *,
    cwd: Path,
    timeout: float,
    profile: str | None = None,
    transcript: Path | None = None,
    record: Path | None = None,
) -> tuple[str, dict, int]:
    """Resolve `role`, run it once, and return output, record, and exit code."""
    agent = resolve_cagent_role(role, profile_override=profile)
    result = run_harness(
        agent,
        prompt,
        cwd=cwd,
        timeout=timeout,
        allowed_tools=ROLE_ALLOWED_TOOLS.get(role),
        extra_args=_agcode_args(role) if agent.harness == "agcode" else None,
        transcript_path=transcript,
    )
    run_record = {"schema": "ag.agent-run.v1", **result.meta}
    if record:
        write_run_record(record, request_id=record.stem, meta=result.meta)
    return result.output, run_record, result.exit_code
