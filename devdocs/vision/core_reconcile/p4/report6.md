# Phase 4 Report — Step 6 (ledger reconcilers and host scoping)

Date: 2026-07-17. Implements [p4/plan.md](plan.md) Step 6. This is the sixth suggested commit
boundary. `nctl` can now actually execute Step 5's `link_actual_node` and `reconcile_ipam` plan
actions against Nautobot/nintent; nintent's `Reconcile Desired IPAM Intent` Job gained host scoping
and a versioned summary artifact.

## What was built

### nintent: host-scoped IPAM Job + versioned summary

`ReconcileDesiredIPAMIntent` (`jobs.py`) gained an optional `desired_node` `StringVar`. When set,
the Job requires exactly one matching `DesiredNode` (raising, which Nautobot surfaces as a failed
JobResult, otherwise) and filters `DesiredEndpoint`s to that node before planning/applying —
`include_inactive` and cluster-wide behavior (empty `desired_node`) are unchanged.

`nautobot_intent_catalog/operations/ipam.py` gained a new pure function,
`build_ipam_reconcile_summary()`, stamping the artifact with `schema_version:
"nctl.ipam.reconcile.summary.v1"` and a `scope` object recording both the requested slug and the
actual `DesiredNode` ids/slugs the processed endpoints belonged to — so a caller can verify the Job
really stayed inside the node it asked for, not just trust the request. `jobs.py`'s `run()` collects
that scope from the (already node-filtered) `endpoints` queryset and passes it through; the actual
plan-building/counts loop is otherwise unchanged. Both changes follow the codebase's existing
pattern of keeping Django-independent logic in `operations/ipam.py` (unit-testable locally) and
`jobs.py` as thin ORM glue (only exercisable against a live Nautobot).

`README.md`'s reconciliation-boundary section documents the new `desired_node` parameter and the
versioned summary's `scope` field.

### nctl: `nctl_core/reconcile/ledger.py` — the only two places `nctl reconcile` mutates

- `execute_link_actual_node(client, action)` — GETs the `DesiredNode` row first and refuses to
  proceed if `realized_device`/`realized_vm` is already set (never clears or replaces an existing
  link, per Decision 5), PATCHes exactly the field implied by the plan action's candidate
  `object_type` (`dcim.device` → `realized_device`, `virtualization.virtualmachine` →
  `realized_vm`) through nintent's existing `/api/plugins/intent-catalog/nodes/{id}/` ViewSet, then
  refetches and asserts the exact link landed. A serialized FK value is normalized whether Nautobot
  returns it as a nested object or a plain id (`_linked_id`), since Step 5's risk list flagged this
  as unconfirmed against a live server.
- `execute_reconcile_ipam(job_runner, action, artifact_relative_path=...)` — reuses Step 1's
  `NautobotJobRunner` to trigger `Reconcile Desired IPAM Intent` with `commit_changes=True,
  include_inactive=False, desired_node=<slug>`, requires the Job to reach a successful terminal
  status, downloads the summary artifact, and rejects it if: the schema version doesn't match
  `nctl.ipam.reconcile.summary.v1`, the summary's selected-node scope contains any slug other than
  the one requested, or any individual plan row names a different node. Conflicts and skips inside
  an otherwise-successful run are returned on the result (`.conflicts`, `.skipped`), not swallowed —
  Step 7's executor is expected to turn those into manual-review findings rather than reporting the
  action as converged, matching "Conflicts/skips remain manual findings rather than being hidden by
  Job success."

Neither function has been exercised against a live Nautobot yet (Step 3's report already recorded a
403 against the local dev instance with the current token/config). Both are implemented against the
documented serializer/Job contracts and covered with `respx`-mocked HTTP.

## Tests

`nintent/nautobot_intent_catalog/tests/test_operations_ipam.py` gained
`BuildIpamReconcileSummaryTests` (schema stamping, cluster vs. host scope shape, sorted
id/slug lists regardless of input order).

`nctl/tests/test_reconcile_ledger.py` (new, 12 tests): link-actual-node happy path, refusal to
replace an existing link (asserted by *not* mocking the PATCH route — an accidental PATCH call
would itself fail the test via respx's unmatched-request error), PATCH failure, refetch mismatch,
unsupported candidate type, wrong-action guard; reconcile-ipam happy path, conflicts/skips surfaced
without raising, schema mismatch, scope mismatch, out-of-scope plan rows, wrong-action guard.

Verification:

- `cd nintent && uv run --with pyyaml python -m unittest discover -s nautobot_intent_catalog/tests -v`
  — **84 passed** (up from 80 before this boundary; `jobs.py` itself remains untestable locally
  without a live Nautobot/Django test DB, matching the pre-existing pattern where only
  `operations/*.py` pure functions run outside Nautobot);
- `cd nintent && python3 -m py_compile nautobot_intent_catalog/jobs.py nautobot_intent_catalog/operations/ipam.py`
  — passed;
- `cd nctl && uv run pytest -q` — **405 passed** (up from 393 before this boundary);
- `cd nctl && python3 -m compileall -q src tests` — passed;
- an AST-based unused-import scan over `ledger.py` found nothing beyond the expected
  `from __future__ import annotations` false positive;
- `git diff --check` (parent, nctl, nintent) — passed.

## Deliberate non-work

- no live deployment: this boundary's nintent changes are not yet committed/pushed, and no
  Nautobot rebuild/restart cycle has run. Per `.local/localenv_memo.md` and Decision from prior
  reports, that push is the user's call, batched with the rest of Step 6/9's nintent work into one
  cycle rather than one per boundary;
- no live verification of the PATCH/refetch or Job-trigger paths against the real dev Nautobot;
  Step 9's live rollout is where that happens, once the local token/config that returned 403 in
  Step 3 is refreshed;
- no `nctl reconcile` CLI or bounded executor calling these two functions yet — Step 7 wires
  planning (Step 5) and execution (this step) into the actual round loop, dashboard reuse, and
  event emission;
- no endpoint-level IPAM eligibility refinement beyond what Step 5 already classified as
  automatic — `execute_reconcile_ipam` trusts the plan action's `desired_node_slug` and verifies
  the Job's own scope, but does not re-derive per-endpoint eligibility itself (the Job is the
  authority on that, as it always has been);
- no nauto or ansible_agdev changes in this boundary.

## Files changed in this boundary

nintent:

- `nautobot_intent_catalog/jobs.py` — `desired_node` Job parameter, scoped endpoint filtering,
  versioned summary via the new builder;
- `nautobot_intent_catalog/operations/ipam.py` — added `build_ipam_reconcile_summary` and
  `IPAM_SUMMARY_SCHEMA_VERSION`;
- `nautobot_intent_catalog/tests/test_operations_ipam.py` — added `BuildIpamReconcileSummaryTests`;
- `README.md` — documented the new parameter and summary `scope` field.

nctl:

- added `src/nctl_core/reconcile/ledger.py`;
- added `tests/test_reconcile_ledger.py`.

Parent repository:

- added this report. No commit was created.
