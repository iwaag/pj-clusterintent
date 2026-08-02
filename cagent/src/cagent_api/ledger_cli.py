"""`cagent-ledger` console script: human-usable CLI over the auth ledger
(p2/plan.md Step 3 — a human-usable CLI is required, don't repeat the
DesiredWorkspace no-GUI mistake, README_DEV.md)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .ledger import Ledger, LedgerError

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_LEDGER_PATH = Path.home() / ".local" / "state" / "cagent" / "ledger" / "ledger.jsonl"


def _print_entry(entry) -> None:
    print(f"serial={entry.serial}")
    print(f"  uuid={entry.uuid}")
    print(f"  state={entry.state}")
    print(f"  fingerprint={entry.fingerprint}")
    print(f"  not_after={entry.not_after}")
    if entry.revoked_at:
        print(f"  revoked_at={entry.revoked_at}")


def cmd_list(args: argparse.Namespace) -> None:
    ledger = Ledger(Path(args.path))
    entries = ledger.list()
    if not entries:
        print("(ledger is empty)")
        return
    for entry in entries:
        _print_entry(entry)


def cmd_show(args: argparse.Namespace) -> None:
    ledger = Ledger(Path(args.path))
    entry = ledger.get(args.serial)
    if entry is None:
        raise SystemExit(f"no ledger entry for serial {args.serial}")
    _print_entry(entry)


def cmd_register(args: argparse.Namespace) -> None:
    ledger = Ledger(Path(args.path))
    entry = ledger.register(args.uuid, args.serial, args.fingerprint, args.not_after)
    print(f"registered serial={entry.serial} uuid={entry.uuid} state={entry.state}")


def cmd_revoke(args: argparse.Namespace) -> None:
    ledger = Ledger(Path(args.path))
    try:
        entry = ledger.revoke(args.serial)
    except LedgerError as exc:
        raise SystemExit(str(exc))
    print(f"revoked serial={entry.serial} uuid={entry.uuid} state={entry.state}")


def cmd_reactivate(args: argparse.Namespace) -> None:
    ledger = Ledger(Path(args.path))
    try:
        entry = ledger.reactivate(args.serial)
    except LedgerError as exc:
        raise SystemExit(str(exc))
    print(f"reactivated serial={entry.serial} uuid={entry.uuid} state={entry.state}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cagent-ledger", description=__doc__)
    parser.add_argument("--path", default=str(DEFAULT_LEDGER_PATH), help="ledger JSONL path")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="list all ledger entries")
    p_list.set_defaults(func=cmd_list)

    p_show = sub.add_parser("show", help="show one entry by certificate serial")
    p_show.add_argument("serial")
    p_show.set_defaults(func=cmd_show)

    p_register = sub.add_parser("register", help="register a newly signed node certificate")
    p_register.add_argument("--uuid", required=True)
    p_register.add_argument("--serial", required=True)
    p_register.add_argument("--fingerprint", required=True)
    p_register.add_argument("--not-after", required=True, dest="not_after")
    p_register.set_defaults(func=cmd_register)

    p_revoke = sub.add_parser("revoke", help="revoke a certificate serial")
    p_revoke.add_argument("serial")
    p_revoke.set_defaults(func=cmd_revoke)

    p_reactivate = sub.add_parser("reactivate", help="reactivate a previously revoked serial")
    p_reactivate.add_argument("serial")
    p_reactivate.set_defaults(func=cmd_reactivate)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    args.func(args)


if __name__ == "__main__":
    main()
