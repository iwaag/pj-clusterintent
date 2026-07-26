# Test Strategy Phase 1 — Step 1 Report: Phase 0 Classifications Revalidated

Parent: [plan.md](plan.md), Step 1.

Status: **`complete`**.

## Revalidation result

- The Phase 0 ownership inventory still identifies exactly **29** `replace` entries, all from
  `nintent/nautobot_intent_catalog/tests/test_remove_unused_surfaces.py`.
- The current nctl compatibility-consumer matrix still names the active consumers for
  `EventRecord`, `nctl.drift.v1`, the two inventory renders, dnsmasq render, and operations
  index/list/show. It also records `legacy_dashboard_urls` and
  `reconciliation_status_fields` as removed in a matched rollout.
- The five historical nctl modules collected **12** tests and passed (`12 passed`). The focused
  compatibility plus historical-module baseline passed (`17 passed`).
- `test_vm_p3_compute_stays_inert.py::test_valid_compute_collections_produce_no_drift_and_no_plan_actions`
  passed, preserving the real comparator/planner no-compute-dispatch proof.

## Search classification

- No old phase-prefixed target filename appears in active tracked source outside the five files
  scheduled for rename.
- The only active `reconciliation_status` occurrences outside the removal test are migration
  history (`0009`, `0010`, `0016`) and the nctl operations-index historical-artifact reader.
  Both are retained owners, not deletion candidates.
- `nintent/DEVLOG_PICKUP.md` mentions an old Job class in a dated historical note; it is not an
  implementation, registration, or current consumer.
- Matches for `serve` were manually classified as ordinary words such as “server”,
  “observed”, or documentation prose; none establishes an `nctl serve` consumer.
- No tracked fixture, helper, dependency, generated snapshot, or current document has yet been
  proven to have lost its final active consumer. Step 5 therefore has no pre-authorized deletion.

## Disposable-test cleanup finding

The initial focused Nautobot baseline found a stale disposable `test_nautobot` database left by
an earlier `--keepdb` execution. It had a duplicate-table migration failure. I verified that the
live database was separately named `nautobot`, terminated only connections to `test_nautobot`,
and removed that exact disposable database. A later direct runner invocation again left a
`test_nautobot` database without reaching a final result through this terminal session, so it was
removed as well. No live database, service, or source file was changed.

The required local-source disposable command will be established in Step 6 using the plan's
one-shot runner method; the installed-package baseline is not used as evidence for edited tests.

## Deletion ledger authority

The 29 entries remain authorized only for consolidation into the named model/migration, API, or
UI owners in Step 2. The next step will record each old test's exact final owner and positive
evidence before deleting the historical removal module.
