# Sequential Desired-State Planning — Report

Date: 2026-07-30

## Result

Implemented the generic batch-planning reference resolver in
`nintent/nautobot_intent_catalog/batch.py`.

- Every desired-state relationship is now resolved independently against the
  current database or an `upsert` identity in the same batch.
- A batch-created reference is accepted only when its kind precedes the
  dependent kind in `KIND_ORDER`, matching ordered atomic application.
- Planning does not create transient rows or duplicate apply-time validation.
- Missing node and platform references remain explicit per-operation
  conflicts.

Added runtime coverage for a new node + endpoint + compute instance whose
platform already exists, including a no-write preview followed by successful
atomic apply. Added separate missing-node and missing-platform conflict cases.

## Verification

Completed successfully:

```text
cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests
Ran 127 tests in 0.004s
OK (skipped=10)

./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb
Ran 187 tests in 5.064s
OK
runtime gate result mode=keepdb label=nautobot_intent_catalog cases=187
```

`git -C nintent diff --check` also passed.

The runtime gate copied the modified local `nintent` checkout into its
test-only Nautobot stage, so it exercised the new planner and atomic apply
path without modifying the persistent scratch desired state.

## agdummy scratch CLI replay

The requested dry-run was executed:

```text
uv run --project nctl nctl desired apply \
  -f .local/workspace/brainforge/2026-07-30_974e/sources/agdummy-desired-state.yaml \
  --json
```

It returned two creates and one conflict:

```text
desired_compute_instance: unresolved desired_node reference: 'agdummy'
totals: create=2, conflict=1
transaction: dry_run, committed=false
```

This is the expected result from the currently deployed, pre-change plugin.
Per `.local/localenv_memo.md`, the persistent scratch Nautobot image installs
`nintent` from GitHub and does not mount this local checkout. Therefore the
requested post-deployment replay cannot be completed until this change is
committed, pushed by the user, and the Nautobot image is rebuilt/restarted.
No desired-state write, reconcile, Ansible, SSH, or Proxmox operation was run.

After that deployment, rerun the same command. Expected result: exactly three
`create` actions, zero conflicts, and `transaction.status=dry_run` with
`committed=false`.
