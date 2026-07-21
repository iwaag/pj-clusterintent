# Step 3.8 report — Phase 3 closeout and handover

Date: 2026-07-22 (JST)

## Result

Phase 3 is **complete with an accepted safe-stop boundary**.  The direct-source,
review, desired-state, observation, and review-isolation paths were exercised.
The final dnsmasq apply did not fully converge because SSH host-key verification
prevents the production inventory from connecting to `agdnsmasq`.  The user
accepted treating that safety stop as a separately scoped connection-baseline
follow-up rather than weakening SSH verification or changing the Phase 3 design.
The issue is recorded in `memo.py`.

## Evidence collected at closeout

* `nctl braindump list --json` reports four `user_direct` records.  Every
  record has a review, including the explicit "all unmanaged services are
  intentionally unmanaged for now" disposition.
* `nctl drift --json` reports `converged: 4`, `unknown: 2`.
  `agdnsmasq` and the `dnsmasq` service target are converged.  The outstanding
  unknown targets are not hidden: `agstudio` has stale actual data and `aghub`
  has no realized object / interface candidate.
* Full nctl regression suite: `733 passed, 1 warning`.  The warning is the
  existing Starlette/httpx deprecation warning in `test_serve_ws.py`.
* `git diff --check` passed before this report was added.

## What Phase 3 demonstrated

1. The three source files were preserved as distinct direct user inputs and
   received reviewer-readable comparisons against desired and actual state.
2. A concrete observation failure on `agpc` was traced to the temporary
   inventory omitting shared inventory variables.  nctl commit `3f65248`
   preserves those variables; the retry observed `agpc` successfully.
3. The unmanaged `prometheus` observation was explicitly classified as
   intentionally out of scope.  Re-reviewing that unchanged policy was
   verification-only: desired/actual snapshots and drift were unchanged, and
   it created no operation or production artifact update.
4. With approval, `agdnsmasq` was moved from `planned` to `active`; a dry plan
   was reviewed before apply.  The apply observed the node and reconciled IPAM,
   but did not run the dnsmasq configuration task because SSH host-key
   verification failed through the production inventory.

## Remaining work / handover

* Follow `memo.py` to verify the SSH host key and make the production
  connection identity consistent.  Do not weaken SSH verification.
* After explicit approval, run a new plan-only reconcile for `agdnsmasq`,
  inspect it, and only then apply it.  Record the resulting operation in the
  SSH follow-up work; it is not required to reopen this completed phase.
* The direct Nautobot UI-entry case in Step 3.3 was not performed; Phase 3
  therefore does not claim UI-path coverage.  Perform it in a follow-up and
  review the resulting record.
* Refresh or intentionally disposition the stale/unrealized `agstudio` and
  `aghub` actual-state findings in a separate, scoped follow-up.

## Scope boundary

No SSH configuration, known_hosts entry, or host-key policy was changed in
this step.  The handover records the diagnosis and safe decision points only.
No source prose or credentials are copied into this report.

## Accepted closeout scope

This completion does not assert that the direct Nautobot UI-entry interval or
the final SSH-backed configuration action succeeded.  It asserts that their
absence/failure is explicit, safely bounded, and does not require new diary
schema, review automation, or a reconciliation bypass.  The remaining SSH and
UI-path work is a follow-up acceptance test for those respective surfaces.
