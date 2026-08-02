"""Minimal human inspection surface for cluster-agent evidence.

`uv run --project cagent cagent-evidence list`
`uv run --project cagent cagent-evidence show <request_id>`

Reads evidence directly off disk — does not require the API server to be
running. Per p1/plan.md Step 4: "a tiny CLI subcommand or even documented
ls/cat conventions are enough for now." Documented `ls`/`cat` conventions
also work directly against `<evidence_dir>/<request_id>/{request.json,
events.jsonl}` if this CLI is unavailable.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from .evidence import EvidenceWriter
from .main import DEFAULT_EVIDENCE_DIR


def _evidence_dir() -> Path:
    return Path(os.environ.get("CAGENT_EVIDENCE_DIR", str(DEFAULT_EVIDENCE_DIR)))


def cmd_list(evidence: EvidenceWriter) -> None:
    for request_id in evidence.list_request_ids():
        record = evidence.read_request(request_id)
        latest = evidence.read_latest_event(request_id)
        state = latest["state"] if latest else "unknown"
        identity = record["identity"]
        print(f"{request_id}  {state:<12}  {identity['class']}:{identity['name']}  {record['session_id']}")


def cmd_show(evidence: EvidenceWriter, request_id: str) -> None:
    record = evidence.read_request(request_id)
    print(json.dumps(record, indent=2))
    print("--- events ---")
    events_path = evidence.evidence_dir / request_id / "events.jsonl"
    if events_path.exists():
        print(events_path.read_text(), end="")


def main() -> None:
    parser = argparse.ArgumentParser(prog="cagent-evidence")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list")
    show = sub.add_parser("show")
    show.add_argument("request_id")

    args = parser.parse_args()
    evidence = EvidenceWriter(_evidence_dir())

    if args.command == "list":
        cmd_list(evidence)
    elif args.command == "show":
        try:
            cmd_show(evidence, args.request_id)
        except FileNotFoundError:
            print(f"no evidence for request_id: {args.request_id}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
