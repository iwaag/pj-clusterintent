# Test Strategy Phase 2 — Step 2 Report: nctl Transport Fixture Disposition

Parent: [plan.md](plan.md), Step 2.

Status: **`complete`**.

## Contract inventory

Mapped the transport tests in `nctl/tests/test_nautobot.py` by exact method and endpoint:
status plus GraphQL type discovery, generic GraphQL, REST POST, REST PATCH, and REST DELETE.
Each existing inline response is already a small canonical fixture for that wire contract and
contains only fields consumed by its parser.

The map retains the distinct safe translations for absent plugin/types, GraphQL errors,
authentication statuses, connection failures, and DELETE's non-auth 404 behavior. Those outcomes
are not collapsed into a shared success matrix.

## Disposition

No shared response factory was added. A generic builder here would have to re-express method,
endpoint, status, and failure semantics across five different contracts, becoming the second
schema implementation prohibited by the plan. The exact, contract-local fixtures are clearer and
are retained as their canonical fixtures.

Focused verification passed: `cd nctl && uv run pytest -q tests/test_nautobot.py` — **22
passed**. No runtime behavior or external service was changed.

The detailed wire-contract map and this disposition are recorded privately in
`.local/test-strategy/p2/20260726T144434Z/transport-fixture-map.tsv`.
