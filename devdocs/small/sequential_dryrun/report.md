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

Before deployment, it returned the expected old-plugin failure of two creates
and one conflict:

```text
desired_compute_instance: unresolved desired_node reference: 'agdummy'
totals: create=2, conflict=1
transaction: dry_run, committed=false
```

After the user pushed commit `8ea7d4842c5fa778249ffb304668838fee9550f1`, the
scratch Nautobot Dockerfile's pinned `NINTENT_COMMIT` was updated to that SHA
and `docker compose --env-file ../.env up -d --build` was run from
`devenv/nautobot/`. The rebuilt service reported that same SHA in
`/opt/nautobot/build_info.json` and all three Nautobot services were healthy.

The replay then returned the target result:

```text
desired_node: create
desired_endpoint: create
desired_compute_instance: create
totals: create=3, conflict=0
transaction: dry_run, committed=false
```

No desired-state write, reconcile, Ansible, SSH, or Proxmox operation was run.
