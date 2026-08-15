"""The read-only nctl surface, defined once.

Two consumers call this module and nothing else defines the surface: the
in-process tool the front-door agent gets (`agent_runner.window_tools`), and
the `cagent` CLI handed to the operator subagent (`cli.py`). A subcommand
added here is immediately available — and refusable — in both.

Selection happens in Python rather than as a shell glob list: `("ops",
"list")` matches by tuple, so there is no quoting trick, no `;`, and no
second command to smuggle in. Tokens arrive as ordinary argv entries, and an
unaccounted-for entry is a refusal.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from pathlib import Path

# Each entry is (subcommand words, how many positional arguments follow).
NCTL_SUBCOMMANDS = (
    (("status",), 0),
    (("drift",), 0),
    (("relations",), 0),
    (("actual",), 0),
    (("ops", "list"), 0),
    (("ops", "show"), 1),  # the operation id
)
# Flags that take no value, and flags that take exactly one.
NCTL_SWITCHES = {"--json", "--detail"}
NCTL_OPTIONS = {"--host", "--limit", "--after-seq"}
NCTL_TIMEOUT_SECONDS = 120.0

AVAILABLE = ", ".join(" ".join(words) for words, _ in NCTL_SUBCOMMANDS)


def validate(args: str) -> tuple[list[str] | None, str | None]:
    """`(argv tail, None)` for one read-only call, `(None, refusal)` otherwise.

    `args` is the part after `nctl`. Every token is accounted for — the
    subcommand, its declared number of positional arguments, and flags from
    the two small sets — so a trailing word cannot ride along.
    """
    try:
        parts = shlex.split(args)
    except ValueError as error:
        return None, f"refused: could not parse arguments ({error})"
    match = next(
        ((words, extra) for words, extra in NCTL_SUBCOMMANDS
         if parts[: len(words)] == list(words)),
        None,
    )
    if match is None:
        return None, (
            f"refused: {args!r} is not one of the available subcommands ({AVAILABLE})"
        )
    words, allowed_positionals = match
    rest, positionals = parts[len(words):], 0
    index = 0
    while index < len(rest):
        token = rest[index]
        name, sep, _ = token.partition("=")
        if name in NCTL_SWITCHES and not sep:
            index += 1
        elif name in NCTL_OPTIONS:
            index += 1 if sep else 2  # --flag=value, or --flag value
        elif token.startswith("-"):
            return None, (
                f"refused: {token!r} is not an available option "
                f"({', '.join(sorted(NCTL_SWITCHES | NCTL_OPTIONS))})"
            )
        else:
            positionals += 1
            if positionals > allowed_positionals:
                return None, (
                    f"refused: {token!r} is an extra argument to "
                    f"{' '.join(words)!r}. Available: {AVAILABLE}"
                )
            index += 1
    return parts, None


def run_nctl(base: Path, parts: list[str], *, capture: bool = True) -> subprocess.CompletedProcess:
    """Run one validated `nctl` call from `base` (the superproject root)."""
    argv = ["uv", "run", "--project", "nctl", "nctl", *parts]
    # When this process itself runs under `uv run` (the scripts/cagent shim),
    # the inherited VIRTUAL_ENV points at cagent's venv and the child uv warns
    # about it on every call. The child resolves nctl's own environment.
    env = {k: v for k, v in os.environ.items() if k != "VIRTUAL_ENV"}
    return subprocess.run(
        argv, cwd=base, capture_output=capture, text=capture,
        timeout=NCTL_TIMEOUT_SECONDS, env=env,
    )


def nctl_readonly(base: Path, args: str = "") -> str:
    """The in-process tool: one read-only `nctl` call, result as JSON text."""
    parts, refusal = validate(args)
    if refusal is not None:
        return refusal
    try:
        proc = run_nctl(base, parts)
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

__all__ = [
    "AVAILABLE",
    "NCTL_OPTIONS",
    "NCTL_SPEC",
    "NCTL_SUBCOMMANDS",
    "NCTL_SWITCHES",
    "NCTL_TIMEOUT_SECONDS",
    "nctl_readonly",
    "run_nctl",
    "validate",
]
