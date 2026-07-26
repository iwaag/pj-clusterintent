# Interface Contract Phase 4 Side Fix 1 Plan: Truthful Post-Mutation Failure Evidence

Status: planned. This document authorizes no production-code change, live Nautobot mutation,
Job execution, deployment, service restart, commit, or push by itself.

This plan resolves the still-open Phase 4 Step 1 problem in
[`../problem.md`](../problem.md): a successful `link_actual_node` PATCH followed by failed
GraphQL confirmation is recorded as a failed action, but the action incorrectly reports
`mutated=false`. The shared round accumulator also considers only `success`, so it can fail to
request a fresh final drift snapshot after a real partial mutation.

The later Phase 4 Step 6 Import-preview problem in the same file is not part of this side fix. It
was resolved on 2026-07-26 by preserving the live descriptions in the canonical YAML and is
already closed by [`../report6b.md`](../report6b.md).

Plan-writing baseline:

| Repository | Revision | Worktree |
|---|---|---|
| superproject | `22921a0fd749231f03a2f77c9f8552d33f418c1d` | clean |
| `nctl` | `79b6d6b3e8025722ae1a408daacbf706e845e11d` | clean |
| `nintent` | `e8732f17ae35d8c72d4d593e8d7311bd234fc0bf` | clean |
| `nauto` | `1c78af8bdbfc69cafdc293b4082f866de9f271b0` | clean |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean |

Preserve [`../problem.md`](../problem.md) as the original defect record. When this plan is
implemented and verified, append a dated resolution that links to this side fix's report; do not
rewrite the original diagnosis or its decision list.

## 1. Goal and selected decision

Adopt `problem.md` decision 2, with one compatibility-preserving refinement:

1. A `link_actual_node` failure after an accepted PATCH must produce
   `success=false, mutated=true`.
2. Shared round accounting must treat an action as having side effects when
   `result.success or result.mutated` is true.
3. `progress_made` retains its existing `success or mutated` rule.
4. A later terminal failure in that round must therefore trigger the existing fresh-drift
   refresh. If the refresh fails, the operation must report `final_drift_unknown` and must not
   publish the pre-mutation snapshot as final.

The accumulator must not be changed to `mutated` alone. Successful production-inventory
generation and observation currently count as round side effects through `success` even when
their `ActionResult.mutated` field is not populated. Replacing `success` with `mutated` would
silently regress that established behavior.

No new terminal/manual-review state is needed for this correction. The action remains failed
until fresh GraphQL/drift evidence confirms the result:

```text
GraphQL precondition confirms an unlinked node
  -> REST PATCH receives a success response
  -> post-PATCH GraphQL confirmation fails or disagrees
  -> ActionResult(success=false, mutated=true, exact error code retained)
  -> round evidence is preserved
  -> the next normal round, or the existing terminal-failure refresh, reads fresh drift
  -> only fresh state may support convergence or the final reported drift
```

## 2. Current defect and invariants to preserve

### 2.1 Current defect

The defect spans three existing contracts:

- `nctl/src/nctl_core/reconcile/ledger.py`
  - `execute_link_actual_node()` performs the PATCH and then raises `LedgerActionError` when
    confirmation fails;
  - `LedgerActionError` currently carries `code` and `detail`, but no mutation evidence.
- `nctl/src/nctl_core/reconcile/executor.py`
  - `_execute_action()` converts every caught ledger/Job/Nautobot error into an
    `ActionResult` whose `mutated` field defaults to false;
  - `_execute_round()` accumulates `had_side_effects` from `.success` only in the bootstrap,
    service, and post-actuation-observation paths;
  - `_run_apply()` already computes `progress_made` from `success or mutated` and already knows
    how to refresh final drift after a terminal error when `had_side_effects=true`.
- `nctl/tests/test_reconcile_executor.py`
  - the Phase 4 Step 1 regression test proves that the failed action record survives, but does
    not assert truthful `mutated`, `had_side_effects`, `progress_made`, or final-drift behavior.

### 2.2 Preserve these existing contracts

- A successful PATCH is not a successful action until GraphQL confirms both the exact
  `realized_device` and `realized_device_source="derived"`.
- Precondition, identity, candidate, and rejected-PATCH failures remain
  `success=false, mutated=false`.
- The executor must not infer mutation from an action's planned `mutates=true`; planning intent
  is not execution evidence.
- A failed action remains in `RoundSummary.actions` with its original bounded error code.
- A failed action does not become successful merely because a write occurred.
- `reconcile_ipam` remains failed when any pinned endpoint is unresolved, while exact
  `applied_endpoint_ids` continue to make `mutated=true`.
- Existing successful action, production-inventory, observation, interruption, SSH preflight,
  and `final_drift_unknown` behavior must remain intact.
- `nctl.reconcile.v2` does not need a schema bump: this side fix corrects the value of the
  existing `mutated` field rather than adding or removing a public field.
- No raw REST body, token, private prose, or other secret is added to action details or events.

## 3. Mutation-evidence contract

### 3.1 Truth table

| Execution point | `success` | `mutated` | Counts toward `had_side_effects` | Counts toward `progress_made` |
|---|---:|---:|---:|---:|
| validation or precondition fails before PATCH | false | false | no | no |
| PATCH returns a non-success response | false | false | no | no |
| PATCH succeeds; post-PATCH GraphQL fetch fails | false | true | yes | yes |
| PATCH succeeds; refetched node identity is wrong | false | true | yes | yes |
| PATCH succeeds; device link is not confirmed | false | true | yes | yes |
| PATCH succeeds; link source is not confirmed | false | true | yes | yes |
| PATCH and both confirmation fields succeed | true | true | yes | yes |
| IPAM applies at least one pinned endpoint but another remains unresolved | false | true | yes | yes |
| IPAM resolves no pinned endpoint and reports only conflicts/skips | false | false | no | no |
| another action succeeds under its current contract | true | existing value | yes | yes |

The important boundary is the successful PATCH response, not a list of two error-code strings in
the executor. Once that boundary has been crossed, every subsequent confirmation failure belongs
to the post-write path and must carry `mutated=true`. This includes transport/schema/fetch,
missing-node, slug-mismatch, link-mismatch, and source-mismatch failures.

### 3.2 The mutation owner supplies the evidence

Extend `LedgerActionError` with a keyword-only `mutated: bool = False` attribute, or introduce an
equally narrow typed ledger execution error with that property. The preferred implementation is
the former because it preserves all current callers and error codes.

`execute_link_actual_node()` must set the flag at the layer that knows whether PATCH succeeded:

1. All errors before a successful PATCH retain the default `mutated=false`.
2. After a successful PATCH response, wrap or annotate every error from the confirmation block
   with `mutated=true`.
3. The two explicit confirmation mismatch errors are created with `mutated=true`.
4. Preserve the original error code, message, safe detail, and exception cause when wrapping a
   post-PATCH GraphQL error.

Do not hard-code `node_link_not_confirmed` and `node_link_source_not_confirmed` in
`_execute_action()`. That would miss post-PATCH `node_fetch_failed` and `node_fetch_mismatch`, and
would make a generic executor guess where the ledger writer crossed its mutation boundary.

### 3.3 Executor propagation and aggregation

In `_execute_action()`:

- copy `getattr(exc, "mutated", False)` into the failed `ActionResult`;
- retain the exact bounded error code;
- add only safe structured detail needed to identify the failure phase, if detail is exposed at
  all; and
- include the boolean mutation result in the sanitized `action_completed` event so the JSONL and
  final envelope agree.

Introduce one private predicate, for example:

```python
def _action_had_side_effects(result: ActionResult) -> bool:
    return result.success or result.mutated
```

Use that predicate at every `_execute_round()` accumulation site:

- bootstrap/ledger actions;
- production inventory regeneration;
- service actions; and
- post-actuation observation.

This eliminates divergent formulas while preserving all current successful-action behavior.
Update `RoundOutcome` and `_execute_round()` comments so they no longer claim
`had_side_effects` means only “at least one appended action succeeded.”

### 3.4 Final drift and terminal behavior

Do not add a second refresh mechanism. Reuse `_run_apply()`'s existing contract:

- a terminal error with `outcome.had_side_effects=false` may retain the current fresh snapshot;
- a terminal error with `outcome.had_side_effects=true` performs exactly one fresh
  `fetch_and_compute_drift()` call;
- a successful refresh replaces the pre-mutation `final_snapshot`, `final_drift_result`, and
  timestamp;
- a failed refresh clears final drift, appends `final_drift_unknown`, and retains all completed
  action/round evidence.

The error text and comments should say that a mutation “succeeded or was positively recorded
before full action confirmation failed,” rather than incorrectly equating `success=true` with
every mutation.

This side fix does not redesign `max_rounds`, `no_progress`, or the operation state machine. Add a
focused audit assertion for the round-limit path while implementing; if a separate stale-final
snapshot can be reproduced when a mutating final round exhausts `max_rounds` without a terminal
error, record it as a new bounded problem instead of silently expanding this fix.

## 4. Required reconciler audit

Before changing shared aggregation, classify every current `ActionResult` producer:

| Producer | Current positive mutation evidence | Required side-fix action |
|---|---|---|
| `link_actual_node` | successful return only; post-PATCH errors lose it | implement the ledger error flag and executor propagation |
| `reconcile_ipam` | exact non-empty `applied_endpoint_ids` already set `mutated=true` | retain producer logic; prove shared `had_side_effects` now observes it |
| `service_profile` / `dnsmasq_config` | successful `_actuation_result()` sets `mutated=true` | preserve; run regression tests |
| `observe_node` | success currently contributes through `.success`; failures have no exact committed-row evidence | preserve current behavior; do not invent mutation from a failed observation |
| production inventory regeneration | success currently contributes through `.success`; it is a local artifact write | preserve by using `success or mutated`, not `mutated` alone |

Also inspect errors after a committed IPAM Job but before its artifact is fully validated.
This side fix may set `mutated=true` only where exact positive evidence exists, such as non-empty
validated `applied_endpoint_ids`. A Job timeout, failed poll, missing artifact, invalid artifact,
or failed playbook can mean “mutation unknown”; the existing boolean must not be changed to true
without evidence. If the audit shows that the current two-state field cannot truthfully represent
an operationally important unknown-write boundary, record a separate problem proposing a
tri-state mutation status. Do not smuggle that schema/state-machine redesign into this repair.

## 5. Implementation sequence

### Step 0 — Freeze the baseline and add failing assertions

1. Re-read this plan, `../problem.md`, `README_DEV.md`, and the relevant current nctl source.
2. Record exact revisions and dirty state; do not overwrite unrelated user changes.
3. Run the existing focused ledger/executor tests.
4. Strengthen the existing Phase 4 Step 1 test so it first fails on:
   - `link_result.mutated is True`; and
   - `outcome.had_side_effects is True`.
5. Add a failed-before-PATCH control that continues to assert both values are false.

The failed-then-passing result belongs in `sidefix1/report.md`.

### Step 1 — Carry mutation evidence across the ledger error boundary

1. Add the default-false mutation flag to `LedgerActionError`.
2. Split or wrap the post-PATCH confirmation block so every failure after the successful REST
   response carries `mutated=true`.
3. Preserve the original code and detail for post-fetch failures.
4. Update focused ledger tests for:
   - refetch transport/GraphQL failure after PATCH;
   - node absent after PATCH;
   - slug mismatch after PATCH;
   - link mismatch;
   - source mismatch;
   - PATCH rejection; and
   - precondition/read failures.
5. Prove that only the post-successful-PATCH cases set the flag.

### Step 2 — Propagate and aggregate evidence in the executor

1. Copy the ledger error's mutation flag into the failed `ActionResult`.
2. Emit the same safe boolean in `action_completed`.
3. Add the one shared `success or mutated` predicate.
4. Replace all four round accumulation formulas with the predicate.
5. Correct the `RoundOutcome`, `_execute_round()`, `_run_apply()`, and `progress_made` comments to
   describe the actual contract.
6. Do not change action ordering, dependency handling, retry count, terminal-error selection, or
   convergence classification.

### Step 3 — Prove partial IPAM and final-drift behavior

1. Extend the existing partial-IPAM executor test to assert
   `outcome.had_side_effects is True`.
2. Add an IPAM no-apply conflict/skip control that remains
   `mutated=false, had_side_effects=false` unless another successful action contributes.
3. Add an executor/run-level case in which:
   - a link PATCH is recorded as mutated;
   - its confirmation fails;
   - a later expected terminal error stops the same round; and
   - exactly one fresh final drift fetch occurs.
4. Add the refresh-failure variant and require:
   - the failed-mutated action remains in the round;
   - `progress_made=true`;
   - both the original terminal error and `final_drift_unknown` are reported; and
   - `final_drift_path` is empty rather than pointing at the stale pre-mutation snapshot.
5. Re-run existing successful production-regeneration, successful observation, interruption,
   store-failure, and post-actuation evidence-retention tests to prove the aggregation change did
   not narrow existing side-effect accounting.

### Step 4 — Close documentation and report truthfully

1. Create `sidefix1/report.md` with:
   - exact before/after revisions;
   - the selected contract;
   - files changed;
   - failed-then-passing tests;
   - the reconciler audit and every residual unknown-mutation case;
   - verification command totals; and
   - confirmation that no live operation or deployment occurred, unless separately authorized.
2. Append a dated resolution to the first open problem in `../problem.md`, linking to the report.
3. Leave the closed Step 6 resolution and historical Phase 4 reports unchanged.
4. Update current nctl documentation only if it currently defines `progress_made`,
   `mutated`, or final-drift semantics inconsistently. Do not rewrite historical reports.

## 6. Automated verification

### 6.1 Focused ledger tests

Use `respx` at the real HTTP-client boundary and the real `execute_link_actual_node()` function.
Required cases:

- precondition GraphQL failure: no PATCH, `mutated=false`;
- existing/partial existing link: no PATCH, `mutated=false`;
- PATCH non-success: `mutated=false`;
- PATCH success plus post-fetch transport failure: original fetch code, `mutated=true`;
- PATCH success plus absent/mismatched node: original identity code, `mutated=true`;
- PATCH success plus wrong device: `node_link_not_confirmed`, `mutated=true`;
- PATCH success plus wrong source: `node_link_source_not_confirmed`, `mutated=true`;
- fully confirmed PATCH: successful result and executor `mutated=true`.

### 6.2 Executor and operation tests

Required assertions:

- the existing post-PATCH confirmation-failure test now asserts failed + mutated + retained;
- the round accumulator recognizes a failed-mutated link;
- the round accumulator recognizes partial IPAM;
- a failed-non-mutating action does not create progress;
- existing successful production inventory still contributes despite its default
  `mutated=false`;
- `progress_made` is true for failed-but-mutated link/IPAM actions;
- a later terminal failure triggers one fresh final-drift read;
- refresh failure produces `final_drift_unknown` without stale final evidence; and
- event JSON and final `ActionResult` agree on `success=false, mutated=true`.

### 6.3 Full local suite

From the repository root:

```text
uv run --project nctl pytest nctl/tests/test_reconcile_ledger.py \
  nctl/tests/test_reconcile_executor.py
uv run --project nctl pytest
git -C nctl diff --check
git diff --check
```

If repository-standard invocation requires running inside `nctl/`, record that exact working
directory and use `uv run pytest`. Do not substitute a narrower passing test for a failed full
suite.

## 7. Environment-backed verification

No live mutation is required or authorized for this accounting repair. The highest practical
proof is:

1. real `NautobotClient` request construction under `respx`;
2. the real ledger writer and executor code;
3. a run-level final-drift refresh test with only external Nautobot responses stubbed; and
4. the full nctl suite.

A disposable Nautobot HTTP test may be added if an existing harness can safely force the
post-PATCH GraphQL confirmation failure while rolling back all rows. It must:

- use a clearly synthetic DesiredNode and Device;
- record before/after row fingerprints;
- restore or delete the fixture;
- prove both the PATCH and failed confirmation actually occurred; and
- never weaken authentication, GraphQL confirmation, or writer restrictions.

Do not induce this failure on the live five-node cluster. Absence of a live anomaly is not proof
that the boundary ran.

## 8. Safety, failure handling, and rollback

- Implementation is nctl-only unless the audit proves otherwise.
- Do not modify nintent REST behavior or weaken post-PATCH GraphQL confirmation.
- Do not retry the PATCH automatically after failed confirmation; a retry could collide with the
  link that the first PATCH already wrote.
- Do not clear or replace an existing realized link during recovery.
- Do not classify an action as successful merely because `mutated=true`.
- Do not infer mutation from planned intent, an attempted request, or an unvalidated Job result.
- Keep error details bounded and secret-free.
- No database migration is expected.
- Before any future deployment, require the normal user-owned commit/push/deploy workflow; this
  plan does not authorize it.

If focused or full tests fail outside the intended assertions, stop and report the exact failure.
If the shared accumulator changes an established successful-action result, revert the code change
or fix the predicate before proceeding. Source rollback is the single reviewed nctl commit; no
database rollback should be necessary because verification is local/disposable.

## 9. Definition of done

This side fix is complete only when:

- every failure before an accepted link PATCH reports `mutated=false`;
- every confirmation failure after an accepted link PATCH reports
  `success=false, mutated=true`;
- post-PATCH fetch and identity errors are covered, not only the two explicit confirmation codes;
- the executor propagates mutation evidence without an error-code allowlist;
- every round accumulator uses the same `success or mutated` predicate;
- partial IPAM apply contributes to `had_side_effects` without becoming successful;
- failed-but-mutated actions contribute to `progress_made`;
- a later terminal failure obtains fresh final drift, or reports `final_drift_unknown` without a
  stale final path;
- existing successful production-inventory, observation, service, and interruption behavior
  remains covered and passing;
- focused and full nctl suites pass from their documented working directory;
- the report records any unresolved unknown-mutation boundary without overstating completion;
- `problem.md` links to the verified resolution while preserving its original history; and
- no live state, secret, private prose, or unrelated worktree content was changed.

Passing tests alone are not completion. The required outcome is truthful, retained evidence that
distinguishes “the action fully succeeded,” “a write happened before confirmation failed,” and
“no write occurred,” followed by a fresh final-state read whenever later failure would otherwise
publish stale drift.
