# Test Strategy Phase 3 — Step 5 Report: DesiredNode Real-HTTP Transition (in progress)

Parent: [plan.md](plan.md), Step 5.

Status: **`partially complete`**.

## Implemented maintained runtime proof

Added `nintent/nautobot_intent_catalog/tests/test_p3_node_link_http.py`. It runs only in the
exact-local-source Nautobot runtime, using Django's loopback live server, a test-only token, and
rows owned by `test_nautobot`. The test imports the checked-out `nctl` source and invokes its real
desired/actual GraphQL readers, drift engine, classifier/planner, and ledger writer.

The positive case proves the real HTTP sequence exactly:

```text
POST /api/graphql/ 200
PATCH /api/plugins/intent-catalog/nodes/<synthetic-id>/ 200
POST /api/graphql/ 200
```

It asserts initial `actual_node_not_linked`, one exact `link_actual_node` action, the expected
synthetic candidate ID, and fresh drift/planning with no repeated link action after confirmation.

Test-owned callbacks run only after the real PATCH returns successfully and before its GraphQL
confirmation. They prove fail-closed, `mutated=true` results for a reset link, a changed source,
a different candidate, and a deleted DesiredNode. Pre-existing links/source-only state and absent
or unauthenticated pre-write requests fail with `mutated=false` and leave the synthetic row
unchanged. The callbacks are test fixtures, not application endpoints or production seams.

## Verification

The exact-local-source runtime command passed:

```text
nautobot-server test nautobot_intent_catalog.tests.test_p3_node_link_http --keepdb -v 1  6 passed
```

The container runtime resolved `nautobot_intent_catalog` from `/tmp/p3-nintent` and `nctl_core`
from `/tmp/p3-nctl/src`. `httpx` and its pure-Python transitive runtime dependencies were copied
only to `/tmp/p3-nctl-deps`, because the Nautobot image does not ship nctl's HTTP client
dependency. No public network, secret file, root `nctl.toml`, persistent database, real inventory,
or external host was used.

## Remaining Step 5 work

This report is deliberately not complete. The maintained test still needs the Step 5 operation
executor/evidence assertions for a successful PATCH followed by a terminal failure, including
retained action/round evidence, `had_side_effects=true`, and a final drift or typed unknown state.
It also needs the remaining representative malformed GraphQL pre-read/confirmation transport case
through the loopback boundary. The existing focused executor and ledger tests remain the current
owner for those domain assertions until that real-HTTP bridge is added.

All test-owned runtime rows are rolled back by the Nautobot test runner. The temporary source and
dependency copies under `/tmp/p3-*` were removed after the passing checkpoint; the phase cleanup
audit will recheck that boundary.
