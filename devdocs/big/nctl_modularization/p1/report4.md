# P1 Step 4 — Generate the fixture and add the freshness gate

Status: complete.

## Delivered fixture boundary

Generated and committed the sole tracked conformance fixture at
`nctl/tests/fixtures/compute_conformance.json`. It is derived from the nintent owner, not written
by hand; its SHA-256 is retained in the private evidence directory.

Added `devtests/test_strategy/generate_compute_conformance.py`, which imports the sibling nintent
checkout, writes the consumer fixture, and prints the source revision only to stdout. The new
superproject freshness gate regenerates in memory and byte-compares the committed fixture.

The root command matrix and conformance-gate guide now document the command, its sibling-checkout
prerequisite, no-skip expectation, and requirement whenever either side's compute contract changes.

## Verification

`uv run --project nctl pytest -q devtests/test_strategy/test_compute_conformance.py` passed:
**1 passed**. The fixture has 1,234 deterministic JSON lines and digest
`ccff71d9f4c7715a46c026c1529373fc38806208df49f512bc85d6a3e31b81ce`.

## Gate verdict

Complete: the fixture exists once in tracked source, the owner-to-fixture freshness gate passes,
and the command matrix documents the ownership boundary.
