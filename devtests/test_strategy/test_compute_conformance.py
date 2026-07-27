from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "nintent"))

from nautobot_intent_catalog.compute_conformance import dumps_fixture  # noqa: E402


def test_committed_fixture_matches_checked_out_owner() -> None:
    fixture = ROOT / "nctl/tests/fixtures/compute_conformance.json"
    assert fixture.read_text(encoding="utf-8") == dumps_fixture()
