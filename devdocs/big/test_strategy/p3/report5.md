# Test Strategy Phase 3 — Step 5 Report: DesiredNode Real-HTTP Transition

Parent: [plan.md](plan.md), Step 5.

Status: **`complete`**.

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

The runtime gate also starts a second test-owned loopback HTTP server for a malformed GraphQL
pre-read reply. `NautobotClient` crosses that actual socket, receives malformed GraphQL data, and
fails as `node_fetch_failed` with `mutated=false`; its traffic record proves there was one GraphQL
POST and no PATCH.

For a real PATCH followed by a test-owned reset, the gate also invokes nctl's real executor action
boundary. It verifies the returned action result is `success=false`, `mutated=true`, names
`node_link_not_confirmed`, and that the durable JSONL `action_completed` record retains the same
success/mutation facts.

The final case runs the public `run_reconcile` loop against the same live server and test-only
token.  The real PATCH succeeds, the callback resets only its synthetic row, and the next fresh
GraphQL/drift/plan cycle reaches the truthful `no_progress` terminal result.  It retains the failed
`link_actual_node` action in the round (`success=false`, `mutated=true`), sets
`progress_made=true`, preserves the action-completed JSONL record, and writes a fresh final-drift
artifact.  The test has no deployment profiles, so its post-ledger production-render action is an
explicit no-profile no-op; no inventory or external action is involved.

## Verification

The exact-local-source runtime command passed:

```text
nautobot-server test nautobot_intent_catalog.tests.test_p3_node_link_http --keepdb -v 0  9 passed
```

The container runtime resolved `nautobot_intent_catalog` from `/tmp/p3-nintent`, `jobs` from
`/tmp/p3-nauto`, and `nctl_core` from `/tmp/p3-nctl/src`. `httpx` and its pure-Python transitive
runtime dependencies were copied only to `/tmp/p3-nctl-deps`, because the Nautobot image does not
ship nctl's HTTP client dependency. No public network, secret file, root `nctl.toml`, persistent
database, real inventory, or external host was used.

All test-owned runtime rows are rolled back by the Nautobot test runner. The temporary source and
dependency copies under `/tmp/p3-*` were removed after the passing checkpoint; the phase cleanup
audit will recheck that boundary.
