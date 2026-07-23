# Step 3 — Make nctl Eligibility and Drift Evidence Explicit

## Changes

`nctl/src/nctl_core/drift/evaluation.py`, `evaluate_endpoint_intent()`:

- Added `_endpoint_ipam_self_observation(node_realized_device, node_realized_vm)`:
  reads `ActualDevice.actual_facts().local_ip` (the `primary_ip_address`
  custom field nauto's ingest Job writes — the same value nctl already
  exposes as `ActualFacts.local_ip`), never the controller-local nodeutils
  cache. `ActualVirtualMachine` (Step 1 schema) carries no custom fields, so a
  linked VM contributes no candidate rather than a guessed one — a structural
  fact of the current actual-source schema, not special-cased logic.
- Added `_resolve_ipam_eligibility(ip_policy, desired_host, observed_hosts)`:
  `dhcp_reserved` is always `"eligible"` (unchanged reservation-intent
  behavior — no matching-observation requirement was added to it);
  `static`/`external` are `"eligible"` only with exactly one distinct observed
  host equal to the normalized desired host, else `"missing"` / `"mismatch"`
  / `"ambiguous"`.
- In the endpoint-IPAM branch (the `realized_ip is None` case), this
  eligibility is now resolved before either automatic code can be emitted.
  When not eligible, the endpoint gets one of the three new gap codes instead
  of `missing_actual_ip_address`:
  - `ipam_reconcile_observation_missing`
  - `ipam_reconcile_observation_mismatch`
  - `ipam_reconcile_observation_ambiguous`
  Only an eligible gap still emits `missing_actual_ip_address` /
  `actual_ip_address_not_linked` — matching the plan's "only an eligible
  create or link gap emits the existing automatic codes."
- All four of these gaps (the three new ones plus the two preserved automatic
  ones) now carry `expected = {endpoint_id, endpoint_name, ip_policy,
  ip_address}` and an `actual` payload with self-observation evidence
  (`candidates`/`observed_hosts`, each candidate's `basis` and `last_seen`)
  plus, for the two automatic codes, `ipam_state: "missing"/"unlinked"` and
  the matching candidate's actual-ref when linked. This satisfies "preserve
  endpoint identity and decision evidence when converting an endpoint gap
  into a node target" — `endpoint_intent_matching` in `comparators.py`
  already collapses every endpoint gap onto its owning node `Target`
  (unchanged), so the endpoint id/name now travel in the diff's
  `desired`/`actual` payload instead of being lost at that collapse.
- IP-range classification, DHCP MAC/interface readiness, and the
  `dhcp_reserved`-only DHCP-pool checks are untouched — IPAM ledger
  eligibility remains independent of DHCP readiness, MAC selection, and range
  evaluation, and `static`/`external` endpoints are not made dnsmasq
  DHCP-reservation targets by this change.

`nctl/src/nctl_core/reconcile/classify.py`:

- Registered the three new codes under `_MANUAL_REVIEW_CODES` so they behave
  like every other ambiguity/conflict code (no reconciler id, never
  auto-triggers the `reconcile_ipam` Job, and Decision 2's fail-closed
  `UnclassifiedDiffCodeError` guard still holds for any future new code).

## Test changes

- `tests/test_reconcile_classify.py`: added the three new codes to
  `_DYNAMIC_CODES` (they are built via an f-string, like the existing
  `*_mismatch` codes, so the source-scanning guard rail needs the same
  manual allowlisting) and to the `test_manual_review_table_from_plan_md_step5`
  parametrization.
- `tests/test_drift_evaluation.py`: added
  `test_dhcp_reserved_endpoint_missing_ip_needs_no_observation`,
  `test_static_endpoint_without_observation_is_manual_review_gap`,
  `test_static_endpoint_with_matching_observation_is_automatic_gap`
  (also asserts the `expected` evidence dict's `endpoint_id`/`ip_policy`),
  `test_external_endpoint_with_mismatched_observation_is_manual_review_gap`,
  `test_static_endpoint_observation_matches_by_host_portion`, and
  `test_static_endpoint_without_realized_device_is_observation_missing`.
- `tests/test_drift_comparators.py`: added
  `test_endpoint_intent_matching_carries_endpoint_identity_for_observation_gap`,
  confirming the node-targeted diff for a manual-review IPAM code still
  carries the owning endpoint's id/name/policy after the node-target
  collapse.

## Verification

```
$ uv run pytest tests/test_drift_evaluation.py tests/test_reconcile_classify.py -q
67 passed

$ uv run pytest tests/test_drift_comparators.py -q
28 passed

$ uv run pytest tests/ -q
974 passed
```

No pre-existing test needed behavioral changes: every existing endpoint
fixture in `test_drift_evaluation.py`/`test_drift_comparators.py` defaults to
`ip_policy="dhcp_reserved"`, which this step deliberately leaves unaffected.

## Status

Step 3 complete at the code level. `reconcilers.py`/`planner.py`/`ledger.py`/
`executor.py` endpoint-coverage pinning (Step 4) and documentation (Step 5)
remain. Not yet deployed or Nautobot-verified.
