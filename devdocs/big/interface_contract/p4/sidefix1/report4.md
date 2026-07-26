# Side Fix 1 Step 4 Report — Documentation, Audit, and Completion

Plan: [plan.md](plan.md), Step 4. Status: complete.

## Result

The Phase 4 Step 1 mutation-evidence problem is resolved in the local nctl worktree. The
implementation is limited to:

- `nctl/src/nctl_core/reconcile/ledger.py`;
- `nctl/src/nctl_core/reconcile/executor.py`;
- focused ledger/executor tests; and
- this side-fix evidence and the dated resolution appended to [`../problem.md`](../problem.md).

No nintent, nauto, schema, YAML, live Nautobot, Job, service, deployment, commit, or push change
was made.

## Final contract

- A rejected/precondition PATCH path remains `success=false, mutated=false`.
- Once `link_actual_node` receives a successful PATCH response, every later GraphQL
  confirmation/fetch/identity error remains failed but is recorded as `mutated=true`.
- The executor copies mutation evidence from the source-owned ledger error; it does not maintain
  an error-code list.
- Every round accumulator uses `success or mutated`, preserving existing successful render and
  observation accounting while including failed node-link and partial-IPAM mutations.
- A terminal error after those side effects obtains one fresh drift snapshot. A refresh failure
  retains the action evidence and reports `final_drift_unknown` without a stale final-drift path.

## Reconciler audit

| Producer | Disposition |
|---|---|
| `link_actual_node` | fixed: all post-successful-PATCH confirmation failures now carry exact mutation evidence |
| `reconcile_ipam` | retained: existing non-empty validated `applied_endpoint_ids` is the positive mutation evidence; shared accumulation now observes it |
| `service_profile` / `dnsmasq_config` | unchanged: successful `_actuation_result()` already records mutation; failed playbook outcomes do not claim unproven mutation |
| `observe_node` | unchanged: successful observation still contributes through `success`; a failed observation has no exact committed-row evidence to relabel |
| production inventory regeneration | unchanged: successful local artifact generation continues to contribute through `success` |

Job timeout/poll/artifact failures remain deliberately unclassified as `mutated=true`: they do not
provide exact committed-row evidence. Should a caller need to distinguish a material
unknown-write state in future, that requires a separate tri-state contract decision rather than
overstating the existing boolean.

## Verification

```text
uv run --project nctl pytest nctl/tests/test_reconcile_ledger.py nctl/tests/test_reconcile_executor.py
72 passed in 0.93s

cd nctl && uv run pytest
967 passed in 5.54s

git -C nctl diff --check
git diff --check
both passed
```

The attempted root-directory `uv run --project nctl pytest` invocation collected the whole
superproject (including nintent/nodeutils tests) and stopped during unrelated dependency setup.
The documented nctl-only command is therefore the `nctl/` working-directory invocation above;
its 967-test suite passed.

## Completion statement

The side fix satisfies its plan's definition of done: it distinguishes failed-before-write from
failed-after-recorded-write, preserves full-confirmation failure semantics, refreshes final drift
after terminal side effects, covers the IPAM partial-apply path, and leaves no live side effect.
The changes are intentionally left uncommitted for the user-controlled review/commit/push flow.
