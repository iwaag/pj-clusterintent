"""`cagent` — read-only cluster observation for cagent's own subagents.

Everything this command can do is the read-only nctl surface defined in
`readonly_nctl.py`; nothing here can change the cluster. `--help` on any
subcommand *is* the usage information (Tool Giving); no guide text repeats it.
"""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path

from .readonly_nctl import NCTL_TIMEOUT_SECONDS, run_nctl, validate

REPO_ROOT = Path(__file__).resolve().parents[3]

__all__ = ["REPO_ROOT", "build_parser", "compose", "main"]


def _output_flags(parser: argparse.ArgumentParser, *, detail: bool = False) -> None:
    parser.add_argument(
        "--json", action="store_true",
        help="machine-readable envelope instead of the human rendering",
    )
    if detail:
        parser.add_argument(
            "--detail", action="store_true",
            help="include per-resource detail rows",
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cagent",
        description=(
            "Read-only view of this cluster: desired vs actual state, drift, "
            "relations, and past operations. Nothing that changes the cluster "
            "is available through this command."
        ),
    )
    commands = parser.add_subparsers(dest="command", required=True)

    status = commands.add_parser(
        "status", help="health of the control plane itself",
        description=(
            "Check the machinery answers depend on: Nautobot connectivity and "
            "auth, worker health, observation-dump freshness. Run this first "
            "when other commands fail or look stale."
        ),
    )
    _output_flags(status)
    status.set_defaults(words=("status",))

    drift = commands.add_parser(
        "drift", help="where actual state differs from desired state",
        description=(
            "Compare the cluster's desired state against its actual state and "
            "report every difference. No differences means the cluster is "
            "converged. This is the answer to 'is anything wrong or pending?'."
        ),
    )
    drift.add_argument("--host", metavar="NAME", help="limit the report to one node")
    _output_flags(drift)
    drift.set_defaults(words=("drift",))

    relations = commands.add_parser(
        "relations", help="how nodes, guests and services relate",
        description=(
            "Show the desired placement graph: which services and guests live "
            "on which nodes, and each target's current status."
        ),
    )
    relations.add_argument("--host", metavar="NAME", help="limit the report to one node")
    _output_flags(relations)
    relations.set_defaults(words=("relations",))

    actual = commands.add_parser(
        "actual", help="the observed state of the cluster",
        description=(
            "Report what is actually running — nodes, interfaces, guests — as "
            "last observed, independent of what is desired."
        ),
    )
    _output_flags(actual, detail=True)
    actual.set_defaults(words=("actual",))

    ops = commands.add_parser(
        "ops", help="what past operations did",
        description="Read-only history of operations run against the cluster.",
    )
    ops_actions = ops.add_subparsers(dest="action", required=True)

    ops_list = ops_actions.add_parser(
        "list", help="recent operations, newest first",
        description="List recent operations with their IDs; feed an ID to 'ops show'.",
    )
    ops_list.add_argument("--limit", metavar="N", help="how many operations to list")
    _output_flags(ops_list)
    ops_list.set_defaults(words=("ops", "list"))

    ops_show = ops_actions.add_parser(
        "show", help="one operation's event log",
        description="Show what one operation did, event by event, by its ID.",
    )
    ops_show.add_argument("operation_id", help="the operation ID, from 'ops list'")
    ops_show.add_argument(
        "--after-seq", metavar="N", help="only events after this sequence number"
    )
    _output_flags(ops_show)
    ops_show.set_defaults(words=("ops", "show"))

    return parser


def compose(args: argparse.Namespace) -> list[str]:
    """The `nctl` argv tail an argparse result stands for."""
    parts = list(args.words)
    if getattr(args, "operation_id", None):
        parts.append(args.operation_id)
    for switch in ("json", "detail"):
        if getattr(args, switch, False):
            parts.append(f"--{switch}")
    for option in ("host", "limit", "after_seq"):
        value = getattr(args, option, None)
        if value is not None:
            parts += [f"--{option.replace('_', '-')}", str(value)]
    return parts


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    parts, refusal = validate(shlex.join(compose(args)))
    if refusal is not None:
        # The parser and the allow-list are meant to coincide; a refusal here
        # is a defect in this file, said plainly rather than half-run.
        print(refusal, file=sys.stderr)
        return 2
    try:
        proc = run_nctl(REPO_ROOT, parts, capture=False)
    except subprocess.TimeoutExpired:
        print(f"nctl timed out after {NCTL_TIMEOUT_SECONDS:.0f}s", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"could not run nctl: {error}", file=sys.stderr)
        return 1
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
