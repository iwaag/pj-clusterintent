# fix1 Implementation Plan: `observe_node` must not batch service-kind targets

Goal: fix a reproducible bug where `nctl reconcile --yes` aborts the automatic-observation
step whenever a service has an evidence-gap diff (e.g. `service_observation_missing`),
because that diff's `service`-kind target gets batched into the same `observe_node` action
as ordinary `node`-kind targets, and `run_observation` only accepts node slugs. This blocks
`.local/scenario3.txt`'s "collect → ingest → compare → report" flow for any placement whose
service hasn't been observed yet (e.g. a freshly declared `dnsmasq` placement).

## Current state (as of 2026-07-20)

Reproduced live against the dev Nautobot instance: `uv run nctl reconcile agdnsmasq --yes`
plans one `observe_node` action with `target_slugs: ["agdnsmasq", "dnsmasq"]` and it fails
immediately with `hosts are not bootstrap-eligible: dnsmasq`. The other actions in the same
round (`reconcile_ipam`, `regenerate_production_inventory`) succeed; only observation is
broken. This reproduced identically across two independent test runs (see
`devdocs/small/basic_service/report6.md`'s follow-up conversation), so it isn't a transient
environment issue (a separate, unrelated Celery-worker outage during testing was ruled out by
restarting the worker and re-running).

Root cause, traced end to end:

- `nctl/src/nctl_core/reconcile/classify.py`'s `_OBSERVATION_CODES` includes both node-evidence
  codes (`missing_actual_node`, `missing_actual_data`, …) and service-evidence codes
  (`service_observation_missing`, `service_observation_stale`, `service_observed_facts_unknown`).
  Both map to the same `reconciler_id="observe_node"`.
- `nctl/src/nctl_core/reconcile/planner.py:125-155`: every diff classified `OBSERVATION` is
  added to one shared `observe_targets` dict keyed by `_target_key(diff.target)` — the diff's
  own target, unmodified. For `service_observation_missing` this target has
  `kind="service", slug="dnsmasq"` (the service's own slug, not the node it runs on). All
  targets are then handed to `plan_observe_node()` (`reconcilers.py:72-81`) as one batch and
  become one `ReconcileAction`'s `targets` list, mixing kinds.
- `nctl/src/nctl_core/reconcile/executor.py:355`: `target_slugs = [t.slug for t in
  action.targets if t.slug]` — derives the slugs to observe straight from `action.targets`,
  blind to `kind`. For the mixed batch this yields `["agdnsmasq", "dnsmasq"]`.
- `nctl/src/nctl_core/observation.py:96-103` (`run_observation`): builds `eligible` from
  `export_hosts_intent(...)` (node slugs only) and raises `ValueError` for any target slug not
  in that set — `"dnsmasq"` never is, so the whole batched action fails, including the
  legitimate node-slug targets that were bundled alongside it.
- The node this service actually needs observed *is* recoverable: `evaluate_all_services`
  (`nctl/src/nctl_core/drift/evaluation_snapshot.py:74-99`) already puts `node_slug` /
  `node_id` into the diff's `desired.expected` payload for `service_observation_missing` (and
  the other service-evidence codes share the same evaluator), e.g.
  `desired.expected.node_slug == "agdnsmasq"` for the `dnsmasq` service target observed live.
  The information needed to fix this is already on the diff; nothing new needs to be computed.

No existing test covers this interaction: `test_reconcile_planner.py::
test_observe_node_aggregates_targets_and_codes` only exercises node-kind diffs
(`missing_actual_data`, `ingest_lag` on plain nodes), so the service-kind path was never
exercised at the planner level.

## Design decision

- **Resolve service-kind observation targets to their owning node at plan time, in
  `planner.py`.** When an `OBSERVATION`-classified diff's target has `kind == "service"`,
  substitute a `kind="node"` target built from `diff.desired["expected"]["node_slug"]` /
  `["node_id"]` before adding it to `observe_targets`, instead of the diff's own service
  target. This is the single point where the diff (with its `desired.expected` payload) and
  the eventual action's target list are both in scope, so it fixes the batching at its source
  rather than downstream:
  - Rejected: filtering/translating in `executor.py`'s `target_slugs` derivation (line 355) —
    would need to re-look-up the owning node from the snapshot for each service target,
    duplicating logic `planner.py` already has cheap access to via the diff payload, and would
    leave `action.targets` (the planned/persisted representation) still showing the wrong
    kind for anyone reading a plan file directly.
  - Rejected: giving `run_observation`/`export_hosts_intent` a service-aware fallback (treat an
    unknown slug as "look up its node") — would silently paper over any future genuinely-wrong
    slug reaching this function instead of failing closed, weakening the existing
    fail-closed contract at `observation.py:101-103`.
  - A service and its node may both already have pending node-level observation diffs in the
    same round; substitution must dedupe by the resulting node key (already the case, since
    `observe_targets` is a dict keyed by `_target_key`).
  - If a service's diff lacks a resolvable node reference (`node_slug` missing/empty in
    `desired.expected`) treat it as a planner defect the same way an unclassified code is
    treated: this shouldn't happen given `evaluate_all_services` always populates it for these
    codes, so raise rather than silently dropping the diff into `manual_review`/`unsupported`.

## Step 1 — planner resolves service-observation targets to their node

- `nctl/src/nctl_core/reconcile/planner.py`, in the `OBSERVATION` branch (~line 133-136): when
  `diff.target.kind == "service"`, read `node_slug`/`node_id` from `diff.desired["expected"]`
  and build the `observe_targets` key/value from a `Target(kind="node", slug=node_slug,
  id=node_id)` instead of `diff.target`. Node-kind observation diffs are unaffected (no branch
  change for them).
- Keep `observe_codes` accumulation as-is (it's code-level, not target-level, so no change
  needed there).
- Tests: extend `test_reconcile_planner.py` with a case mirroring
  `test_observe_node_aggregates_targets_and_codes` but using a `service_observation_missing`
  diff on a service target whose `desired.expected.node_slug` points at an existing node —
  assert the resulting `observe_node` action's targets are the node (`kind="node"`), not the
  service, and that a concurrent node-kind evidence-gap diff for the *same* node collapses into
  one target (dedup). Add a second case for a service diff mixed with an unrelated node's
  evidence-gap diff — assert two distinct node targets, matching today's multi-node aggregation
  behavior.

## Step 2 — regression test at the executor/observation boundary

- Add a test exercising the `executor.py:355` → `run_observation` path directly (or via the
  existing executor-level test harness, whichever `test_reconcile_executor.py` already uses for
  `observe_node`) with a service-kind evidence-gap diff in the plan, asserting `target_slugs`
  passed to `run_observation` contains only the node slug and the action does not fail with
  `hosts are not bootstrap-eligible`.

## Verification

- `uv run pytest -q` (nctl) — full suite green, including the two new/extended planner tests.
- Live replay of the case that surfaced this bug: `uv run nctl reconcile agdnsmasq --yes
  --json` (dev Nautobot instance, `dnsmasq` service placement in `service_observation_missing`
  state) — `observe_node` action should now succeed (or fail for a real observation reason,
  never `hosts are not bootstrap-eligible: dnsmasq`), unblocking `.local/scenario3.txt`'s
  collect → ingest → compare flow for services.

## Exit criteria

- `nctl reconcile --yes` no longer fails `observe_node` for any target whose evidence-gap diff
  is service-kind; the underlying node is observed instead, with node-kind and service-kind
  evidence gaps on the same node deduped into one target.
- No change to `classify.py`'s classification table or to which diff codes are automatable —
  this is purely a target-resolution fix inside the existing `observe_node` reconciler.
