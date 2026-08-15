"""How one cagent turn reaches a model.

Replaces the session-API client the cluster-agent used to drive. The shape
of the change:

- **cagent owns the session.** agcode is one-shot and stateless, so the
  conversation is rebuilt from `Store.list_session_requests()` and prepended to
  the task. The store was already the durable record of every message and
  response; it is now also the memory.
- **cagent owns the instructions.** The per-role `AGENTS.md` is read from disk
  on every request and passed as agcode's `system_suffix`. The previous
  harness fixed instructions at process start, so editing the file needed a
  restart — and a stale file once hung a turn forever
  (`devdocs/vision/file_output/report4.md`).
- **cagent owns the permission set, by choosing the tools.** agcode has no
  permission engine: a door that must not do something is simply not offered a
  tool that can. The window gets `nctl` (read-only subcommands selected here,
  in Python), the two incident tools, and `read`/`list` — no shell at all.
- **The turn is synchronous.** `agcode.run()` blocks until the run ends, so
  the worker no longer polls a message count, and there is no
  `finish == "tool-calls"` step logic to get wrong.

`claude_code` profiles still go out as a subprocess through `run_harness()`,
because that is what claude_code is. Its per-door grant is spelled in
`CLAUDE_ALLOWED_TOOLS` rather than as a tool list.
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess
import uuid
from dataclasses import dataclass
from pathlib import Path

from agag import agcode
from agag.agent_config import AgentConfigError, ResolvedAgent, load_config, resolve_role
from agag.harness import run_harness

from . import incident

# Replay caps. A cagent session is a chat, not a codebase: eight turns is more
# context than any observed answer has needed, and the character cap stops one
# enormous `nctl drift --json` response from crowding out everything else.
REPLAY_TURNS = 8
REPLAY_CHARS = 20_000
RUNAWAY_TURN_BUDGET = 40

# Destroy-class commands, denied before exec on the authenticated doors.
#
# This is the one guard carried over from the retired permission file, and it
# is deliberate: the episode drops wrongness-prevention guards and keeps
# irreversible-harm ones. Everything else in that file — the bash allow-list,
# the edit-path rules — is gone. These patterns are matched against the whole
# command line, so a shell composition cannot slip one past by prefixing it.
DESTROY_PATTERNS = (
    "--allow-destroy",
    "nctl prune",
    "playbooks/proxmox/destroy_",
    "destroy_lxc",
    "destroy_qemu",
    "pct destroy",
    "qm destroy",
    "pvesh delete",
    "vgremove",
    "lvremove",
    "zpool destroy",
    "wipefs",
    "sgdisk",
    "mkfs",
)
_DD_TO_DEVICE = re.compile(r"\bdd\b.*\bif=.*\bof=/dev/")

# The read-only nctl surface the window may reach. Selected here, in Python,
# rather than as a shell glob list: `("ops", "list")` matches by tuple, so
# there is no quoting trick, no `;`, and no second command to smuggle in.
# Each entry is (subcommand words, how many positional arguments follow).
WINDOW_NCTL_SUBCOMMANDS = (
    (("status",), 0),
    (("drift",), 0),
    (("relations",), 0),
    (("actual",), 0),
    (("ops", "list"), 0),
    (("ops", "show"), 1),  # the operation id
)
# Flags that take no value, and flags that take exactly one.
WINDOW_NCTL_SWITCHES = {"--json", "--detail"}
WINDOW_NCTL_OPTIONS = {"--host", "--limit", "--after-seq"}
NCTL_TIMEOUT_SECONDS = 120.0

CLAUDE_READONLY_TOOLS = "Read,Glob,Grep"
CLAUDE_WORKING_TOOLS = "Read,Write,Edit,Glob,Grep,TodoWrite,Bash"


@dataclass
class TurnResult:
    """One turn's outcome, in the vocabulary `Store` already stores.

    `cost_usd` is `None` for agcode: the backend reports no cost, and
    inventing a zero is worse than omitting it. claude_code runs keep the
    figure its own result document carries.
    """

    text: str
    state: str  # completed | failed | cancelled
    error: dict | None
    cost_usd: float | None
    backend: dict | None


def compose_task(message: str, history: list[tuple[str, str | None]]) -> str:
    """The task string: prior turns, then this one.

    agcode is stateless, so continuity is a prefix rather than a session. The
    most recent turns are kept — the tail is what a follow-up question refers
    to — capped at REPLAY_TURNS pairs and REPLAY_CHARS characters. When
    anything was dropped the prefix says so, because an agent that silently
    forgets is worse than one that knows it did.
    """
    if not history:
        return message
    kept: list[str] = []
    budget = REPLAY_CHARS
    dropped = 0
    for asked, answered in reversed(history[-REPLAY_TURNS:]):
        block = f"USER:\n{asked}\n\nASSISTANT:\n{answered or '(no answer recorded)'}"
        if len(block) > budget:
            dropped += 1
            continue
        budget -= len(block)
        kept.append(block)
    dropped += max(0, len(history) - REPLAY_TURNS)
    if not kept:
        return message
    note = (
        f"\n\n({dropped} earlier turn(s) of this session are not shown.)" if dropped else ""
    )
    return (
        "=== EARLIER IN THIS SESSION ===\n"
        + "\n\n".join(reversed(kept))
        + note
        + "\n\n=== THE CURRENT MESSAGE ===\n"
        + message
    )


# --- Tools ------------------------------------------------------------------


def _refuse_destroy(command: str) -> str | None:
    """The refusal text for a destroy-class command, or None to allow it."""
    lowered = " ".join(command.lower().split())
    for pattern in DESTROY_PATTERNS:
        if pattern in lowered:
            return (
                f"refused: this command matches the destroy-class pattern {pattern!r}. "
                "Guest destruction and storage erasure are not available to any "
                "cagent door; a human runs those directly."
            )
    if _DD_TO_DEVICE.search(lowered):
        return "refused: writing an image straight to a device is not available here."
    return None


def guarded_run(base: Path, command: str) -> str:
    refusal = _refuse_destroy(command)
    if refusal is not None:
        return refusal
    return agcode.tool_run(base, command)


GUARDED_RUN_SPEC = {
    "name": "run",
    "description": (
        "Run a shell command in the working directory. Returns JSON with "
        "exit_code, stdout, stderr. Destroy-class commands (guest destruction, "
        "storage erasure) are refused with their reason."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"command": {"type": "string", "description": "Shell command line to execute."}},
        "required": ["command"],
    },
}


def nctl_readonly(base: Path, args: str = "") -> str:
    """Run one read-only `nctl` subcommand. The window's whole cluster reach.

    `args` is the part after `nctl`. Every token is accounted for here — the
    subcommand, its declared number of positional arguments, and flags from
    two small sets — so a trailing word cannot ride along. No shell is
    involved at any point, which is why quoting, `;` and `&&` are not the
    concern they were for a bash glob list: they arrive as ordinary argv
    entries, and an unaccounted-for entry is a refusal.
    """
    try:
        parts = shlex.split(args)
    except ValueError as error:
        return f"refused: could not parse arguments ({error})"
    available = ", ".join(" ".join(words) for words, _ in WINDOW_NCTL_SUBCOMMANDS)
    match = next(
        ((words, extra) for words, extra in WINDOW_NCTL_SUBCOMMANDS
         if parts[: len(words)] == list(words)),
        None,
    )
    if match is None:
        return f"refused: {args!r} is not one of the available subcommands ({available})"
    words, allowed_positionals = match
    rest, positionals = parts[len(words):], 0
    index = 0
    while index < len(rest):
        token = rest[index]
        name, sep, _ = token.partition("=")
        if name in WINDOW_NCTL_SWITCHES and not sep:
            index += 1
        elif name in WINDOW_NCTL_OPTIONS:
            index += 1 if sep else 2  # --flag=value, or --flag value
        elif token.startswith("-"):
            return (
                f"refused: {token!r} is not an available option "
                f"({', '.join(sorted(WINDOW_NCTL_SWITCHES | WINDOW_NCTL_OPTIONS))})"
            )
        else:
            positionals += 1
            if positionals > allowed_positionals:
                return (
                    f"refused: {token!r} is an extra argument to "
                    f"{' '.join(words)!r}. Available: {available}"
                )
            index += 1
    argv = ["uv", "run", "--project", "nctl", "nctl", *parts]
    try:
        proc = subprocess.run(
            argv, cwd=base, capture_output=True, text=True, timeout=NCTL_TIMEOUT_SECONDS
        )
    except subprocess.TimeoutExpired:
        return f"nctl {args} timed out after {NCTL_TIMEOUT_SECONDS}s"
    except OSError as error:
        return f"could not run nctl: {error}"
    return json.dumps(
        {"exit_code": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}
    )


NCTL_SPEC = {
    "name": "nctl",
    "description": (
        "Run one read-only nctl command against this cluster. Available: "
        "status, drift, relations, actual, 'ops list', 'ops show <id>'. "
        "Options: --json, --detail, --host NAME, --limit N, --after-seq N. "
        "Nothing that changes the cluster is available here."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "args": {
                "type": "string",
                "description": "The part after 'nctl', e.g. 'drift --json' or 'ops show 01KX...'.",
            }
        },
        "required": ["args"],
    },
}


def record_incident(
    _base: Path, report: str, reporter: str = "unknown", source: str = "unknown", ref: str = ""
) -> str:
    if not report.strip():
        return "refused: the report text is empty; record the reporter's own words"
    path = incident.write_incident(report, reporter=reporter, source=source, ref=ref)
    return f"recorded as {path}"


RECORD_INCIDENT_SPEC = {
    "name": "record_incident",
    "description": (
        "Record one defect report — above all, a report that what this agent "
        "said about the cluster turned out to be wrong. Recording is the whole "
        "job; do not attempt the repair in the same turn."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "report": {"type": "string", "description": "The report verbatim, in the reporter's own words."},
            "reporter": {"type": "string", "description": "Who reported it, e.g. 'zulip:8'."},
            "source": {"type": "string", "description": "Where it arrived, e.g. 'zulip-dm' or 'window'."},
            "ref": {"type": "string", "description": "Anything to trace it back: a message or request id."},
        },
        "required": ["report"],
    },
}


def list_recent_incidents(_base: Path, limit: int = 10) -> str:
    return incident.format_listing(incident.list_incidents(int(limit)))


LIST_INCIDENTS_SPEC = {
    "name": "list_incidents",
    "description": "Show the most recently recorded defect reports, newest first.",
    "input_schema": {
        "type": "object",
        "properties": {"limit": {"type": "integer", "description": "How many to show (default 10)."}},
    },
}

_SPECS = {spec["name"]: spec for spec in agcode.TOOLS_V0}


def authenticated_tools() -> tuple[agcode.Tool, ...]:
    """read / write / list / run, with run refusing destroy-class commands."""
    return (
        agcode.Tool(_SPECS["read"], agcode.tool_read),
        agcode.Tool(_SPECS["write"], agcode.tool_write),
        agcode.Tool(_SPECS["list"], agcode.tool_list),
        agcode.Tool(GUARDED_RUN_SPEC, guarded_run),
    )


def window_tools() -> tuple[agcode.Tool, ...]:
    """read / list / nctl / record_incident / list_incidents. No shell.

    Strictly tighter than the bash allow-list it replaces, and it needs no
    permission engine: the window is never offered a way to change anything,
    so there is no denial to argue with and no glob to escape.
    """
    return (
        agcode.Tool(_SPECS["read"], agcode.tool_read),
        agcode.Tool(_SPECS["list"], agcode.tool_list),
        agcode.Tool(NCTL_SPEC, nctl_readonly),
        agcode.Tool(RECORD_INCIDENT_SPEC, record_incident),
        agcode.Tool(LIST_INCIDENTS_SPEC, list_recent_incidents),
    )


# --- The runner -------------------------------------------------------------


def resolve(role: str, config_path: Path, overlay_path: Path) -> ResolvedAgent:
    config, overlay = load_config(config_path, overlay_path if overlay_path.exists() else None)
    return resolve_role(config, overlay, role)


class AgentRunner:
    """One door's backend: a resolved role, its instructions, and its tools."""

    def __init__(
        self,
        agent: ResolvedAgent,
        *,
        working_dir: Path,
        instructions_path: Path,
        tools,
        claude_allowed_tools: str,
        turn_timeout: float,
    ) -> None:
        self.agent = agent
        self.working_dir = Path(working_dir)
        self.instructions_path = Path(instructions_path)
        self.tools = tools
        self.claude_allowed_tools = claude_allowed_tools
        self.turn_timeout = turn_timeout

    # A session id is cagent's own now; nothing round-trips to a backend to
    # get one, so creating a session cannot fail.
    def new_session_id(self) -> str:
        return f"ses_{uuid.uuid4().hex}"

    def identity(self) -> dict:
        return {
            "harness": self.agent.harness,
            "provider": self.agent.provider,
            "model": self.agent.model,
            "role": self.agent.role,
            "profile": self.agent.profile,
        }

    def instructions(self) -> str:
        """Read per request: editing AGENTS.md changes the next answer."""
        try:
            return self.instructions_path.read_text(encoding="utf-8")
        except OSError:
            # A missing instructions file is a degraded turn, not a hung one —
            # which is exactly what it used to be.
            return ""

    def run(self, task: str, *, stop=None, transcript_path: Path | None = None) -> TurnResult:
        if self.agent.harness == "claude_code":
            return self._run_claude(task, transcript_path)
        return self._run_agcode(task, stop, transcript_path)

    def _run_agcode(self, task: str, stop, transcript_path: Path | None) -> TurnResult:
        result = agcode.run(
            task,
            str(self.working_dir),
            base_url=self.agent.provider_base_url,
            model=self.agent.native_model,
            max_turns=RUNAWAY_TURN_BUDGET,
            deadline_s=self.turn_timeout,
            tools=self.tools,
            system_suffix=self.instructions(),
            stop=stop,
            transcript_path=str(transcript_path) if transcript_path else None,
        )
        outcome = result.meta.get("outcome")
        if result.meta.get("failure_kind") == "cancelled":
            return TurnResult("", "cancelled", None, None, self.identity())
        if outcome != "done":
            return TurnResult(
                "", "failed",
                {"code": "agent_error", "message": result.meta.get("failure", "run failed")},
                None, self.identity(),
            )
        return TurnResult(result.output, "completed", None, None, self.identity())

    def _run_claude(self, task: str, transcript_path: Path | None) -> TurnResult:
        """claude_code stays a subprocess, with its own grant vocabulary.

        No `stop` here: `run_harness` owns the process and offers no
        between-turn hook, so a cancel on this profile takes effect when the
        turn ends rather than immediately. The window's own timeout still
        bounds it.
        """
        result = run_harness(
            self.agent,
            f"{self.instructions()}\n\n=== THE REQUEST ===\n{task}",
            cwd=self.working_dir,
            timeout=self.turn_timeout,
            allowed_tools=self.claude_allowed_tools,
            transcript_path=transcript_path,
        )
        backend = {**self.identity()}
        cost = result.meta.get("cost_usd")
        if isinstance(cost, (int, float)):
            backend["cost_usd"] = cost
        if result.meta.get("outcome") != "done":
            return TurnResult(
                "", "failed",
                {"code": "agent_error", "message": result.meta.get("failure", "run failed")},
                cost if isinstance(cost, (int, float)) else None, self.identity(),
            )
        return TurnResult(
            result.output, "completed", None,
            cost if isinstance(cost, (int, float)) else None, self.identity(),
        )


def build_runner(
    role: str,
    *,
    config_path: Path,
    overlay_path: Path,
    working_dir: Path,
    instructions_path: Path,
    turn_timeout: float,
) -> AgentRunner:
    """Resolve `role` and give it the tool set its door is entitled to."""
    agent = resolve(role, config_path, overlay_path)
    is_window = role == "window"
    return AgentRunner(
        agent,
        working_dir=working_dir,
        instructions_path=instructions_path,
        tools=window_tools() if is_window else authenticated_tools(),
        claude_allowed_tools=CLAUDE_READONLY_TOOLS if is_window else CLAUDE_WORKING_TOOLS,
        turn_timeout=turn_timeout,
    )


__all__ = [
    "AgentConfigError",
    "AgentRunner",
    "TurnResult",
    "authenticated_tools",
    "build_runner",
    "compose_task",
    "window_tools",
]
