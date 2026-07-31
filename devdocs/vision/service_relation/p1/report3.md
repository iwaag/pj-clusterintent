# Step 3 Report — Graph Invariants + §8 Protection

Status: complete.

## Changes

- `batch.py`:
  - `_DELETE_BLOCKERS`: `desired_service` gains an `inbound_bindings ->
    desired_service_binding` blocker (provider side); `desired_service_placement`
    gains a `service_bindings -> desired_service_binding` blocker (consumer
    side). Both give an early `conflict` in `plan_batch`/dry-run output before
    a delete ever reaches the transaction.
  - `_validate_service_binding_graph(models)`: a final-state validator called
    once, unconditionally, at the end of `apply_batch`'s
    `transaction.atomic()` block (after every write), so it always sees the
    state that survives the whole batch — this is what makes "unless the
    same atomic batch removes or retargets them" (idea-A §8) fall out for
    free rather than needing special-casing. For every surviving
    `DesiredServiceBinding` it checks, in order: consumer placement active
    (§4.1), consumer/provider service active (§4.2), provider service has
    exactly one active placement (§4.3, both zero and >1 rejected as
    "unresolved provider binding"), that placement's endpoint is usable —
    protocol in `{http, https}`, integer port 1–65535, at least one of
    `ip_address`/`dns_name`/`mdns_name` (§4.4), no self-reference (§4.5), and
    acyclic (§4.6, DFS with a 3-color visited set over
    `consumer_placement.pk -> resolved_provider_placement.pk` edges — this
    graph already includes "that placement's own bindings" for free, since a
    resolved provider placement that is itself a consumer elsewhere appears
    as its own node with its own outgoing edges).
  - Provider-side failures (unresolved/ambiguous/inactive/unusable-endpoint)
    for the same provider service are grouped into one error naming the
    exact inbound set, in idea-A §8's literal shape:
    `provider: <slug> / <instance_name-or-ambiguous-list>` then one `consumer_node
    / consumer_service / binding_name` line per surviving binding. Retiring
    or deleting a provider, or deactivating its sole active placement, or
    nulling its endpoint, is exactly the case that empties/breaks this
    resolution, so it is caught by the same code path rather than a separate
    §8-specific check.
  - Self-reference and cycle failures get their own concise, non-grouped
    messages (not the inbound-set format — the plan only requires that shape
    for §8, and neither is a "which consumers get cut off" situation).

## Tests

`ServiceBindingGraphInvariantTests` (ORM, in `tests/test_batch.py`), driven
through `apply_batch` (a real transaction, not just `.clean()`):

- fully resolvable binding commits;
- ambiguous provider (two active placements for one service) is rejected,
  naming both instance names;
- unusable endpoint (no `desired_endpoint` at all) is rejected;
- self-reference (binding's own placement is the resolved provider) is
  rejected;
- cycle (two node_agent placements each providing the other's dependency) is
  rejected;
- retiring a provider service with a live inbound binding is rejected and
  rolled back, with the error containing `provider: <slug>` and the exact
  `node / service / binding_name` consumer line — and the service's lifecycle
  is confirmed unchanged after rollback;
- deactivating the sole active provider placement (leaving the service
  itself active) is rejected the same way;
- deleting a provider service with an inbound binding is caught early as a
  `dry_run` plan `conflict` naming the exact `desired_service_binding:<pk>`
  blocker, before ever reaching the transaction.

The Step 2 `test_apply_batch_creates_a_binding_via_the_batch_endpoint` test
needed a fix: it previously bound to a service with zero placements, which
Step 3's validator now correctly rejects as unresolved; it now builds a
proper resolvable provider first via the new shared `_make_resolvable_provider`
test helper.

## Verification

- `python3 -m unittest discover -s nautobot_intent_catalog/tests` from
  `nintent/`: `Ran 129 tests ... OK (skipped=10)` (unchanged — all new
  coverage here is ORM-backed and Django-free-skipped).
- `./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb
  nautobot_intent_catalog.tests.test_batch`: `cases=33`, all green (25 from
  before Step 3 + 8 new graph-invariant cases).

## Next

Step 4: the full-package runtime gate (`--keepdb` once more to catch
cross-file interactions, then `--clean` once since this phase added a new
migration).
