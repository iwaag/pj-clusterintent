#!/usr/bin/env python3
"""Generate nctl's committed compute-contract fixture from the sibling owner."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
NINTENT = ROOT / "nintent"
FIXTURE = ROOT / "nctl/tests/fixtures/compute_conformance.json"

sys.path.insert(0, str(NINTENT))
from nautobot_intent_catalog.compute_conformance import dumps_fixture  # noqa: E402


def main() -> None:
    FIXTURE.parent.mkdir(parents=True, exist_ok=True)
    FIXTURE.write_text(dumps_fixture(), encoding="utf-8")
    revision = subprocess.check_output(["git", "-C", str(NINTENT), "rev-parse", "HEAD"], text=True).strip()
    print(f"generated from nintent {revision}")


if __name__ == "__main__":
    main()
