#!/usr/bin/env python3
"""Record one incident report as a local file. Stdlib only, no dependencies.

The cluster-agent's window uses this when a message reports a defect — above
all "what cagent said about the cluster turned out to be wrong". Recording is
the whole job: the repair is a later, separate decision by a human or by the
authenticated entrance.

    uv run cagent/window/incident.py -i "you said agpc was up; it is not"
    uv run cagent/window/incident.py -i "..." --reporter "zulip:8" \
        --source zulip-dm --ref "message 41"
    uv run cagent/window/incident.py --list
    uv run cagent/window/incident.py --list 5 --json

One incident is one file, `<UTC timestamp>-<slug>.md`, under
`.local/cagent/incidents/` (git-ignored) — YAML-ish frontmatter with
id/time/reporter/source/ref, then the report verbatim as the body. Nothing
reads these back except `--list` and a human, so the format stays a text file
rather than a schema.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INCIDENT_DIR = REPO_ROOT / ".local" / "cagent" / "incidents"
SLUG_MAX_CHARS = 48
FRONTMATTER_FENCE = "---"


def incident_dir() -> Path:
    """Where incidents live. `CAGENT_INCIDENT_DIR` overrides, for tests."""
    return Path(os.environ.get("CAGENT_INCIDENT_DIR", str(DEFAULT_INCIDENT_DIR)))


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    if len(slug) > SLUG_MAX_CHARS:
        slug = slug[:SLUG_MAX_CHARS].rsplit("-", 1)[0] or slug[:SLUG_MAX_CHARS]
    return slug or "incident"


def _escape(value: str) -> str:
    """One-line frontmatter value: no newlines, no accidental fence."""
    return " ".join(value.split()) or "-"


def write_incident(
    description: str,
    reporter: str = "unknown",
    source: str = "unknown",
    ref: str = "",
    directory: Path | None = None,
    now: datetime | None = None,
) -> Path:
    directory = directory or incident_dir()
    now = now or datetime.now(timezone.utc)
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    incident_id = f"{stamp}-{slugify(description)}"
    path = directory / f"{incident_id}.md"
    # A second report in the same second is a collision, not an overwrite.
    suffix = 2
    while path.exists():
        path = directory / f"{incident_id}-{suffix}.md"
        suffix += 1
    directory.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"{FRONTMATTER_FENCE}\n"
        f"id: {path.stem}\n"
        f"time: {now.strftime('%Y-%m-%dT%H:%M:%SZ')}\n"
        f"reporter: {_escape(reporter)}\n"
        f"source: {_escape(source)}\n"
        f"ref: {_escape(ref)}\n"
        f"{FRONTMATTER_FENCE}\n\n"
        f"{description.strip()}\n",
        encoding="utf-8",
    )
    return path


def read_incident(path: Path) -> dict:
    """Parse one incident file back into `{id, time, reporter, source, ref, body}`."""
    text = path.read_text(encoding="utf-8")
    record = {"id": path.stem, "time": "", "reporter": "", "source": "", "ref": "", "body": ""}
    lines = text.splitlines()
    if lines and lines[0].strip() == FRONTMATTER_FENCE:
        end = next(
            (i for i, line in enumerate(lines[1:], start=1) if line.strip() == FRONTMATTER_FENCE),
            None,
        )
        if end is not None:
            for line in lines[1:end]:
                key, _, value = line.partition(":")
                if key.strip() in record:
                    record[key.strip()] = value.strip()
            record["body"] = "\n".join(lines[end + 1:]).strip()
            return record
    record["body"] = text.strip()  # hand-written or damaged file: keep it readable
    return record


def list_incidents(limit: int, directory: Path | None = None) -> list[dict]:
    """Most recent first. The filename timestamp is the sort key."""
    directory = directory or incident_dir()
    if not directory.is_dir():
        return []
    paths = sorted(directory.glob("*.md"), key=lambda p: p.name, reverse=True)
    return [read_incident(path) for path in paths[:limit]]


def format_listing(records: list[dict]) -> str:
    if not records:
        return "no incidents recorded"
    lines = []
    for record in records:
        first_line = record["body"].splitlines()[0] if record["body"] else ""
        lines.append(
            f"{record['id']}\n"
            f"  time={record['time']} reporter={record['reporter']} "
            f"source={record['source']} ref={record['ref']}\n"
            f"  {first_line}"
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Record or list cluster-agent incident reports.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='example: incident.py -i "you said agpc was up; it is not" --source zulip-dm',
    )
    parser.add_argument("-i", "--incident", help="the report, verbatim, in the reporter's words")
    parser.add_argument("--reporter", default="unknown", help="who reported it, e.g. 'zulip:8'")
    parser.add_argument("--source", default="unknown", help="where it arrived, e.g. 'zulip-dm'")
    parser.add_argument("--ref", default="", help="anything to trace it back: message/request id")
    parser.add_argument(
        "--list", nargs="?", type=int, const=10, default=None, metavar="N",
        help="show the N most recent incidents (default 10) instead of recording one",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    if args.list is not None:
        records = list_incidents(args.list)
        print(json.dumps(records, indent=2) if args.json else format_listing(records))
        return 0

    if not args.incident or not args.incident.strip():
        parser.error("-i/--incident is required (or use --list)")

    path = write_incident(
        args.incident, reporter=args.reporter, source=args.source, ref=args.ref
    )
    print(json.dumps({"path": str(path), "id": path.stem}) if args.json else path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
