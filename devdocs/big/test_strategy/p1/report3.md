# Test Strategy Phase 1 — Step 3 Report: Current-Consumer Compatibility Contracts

Parent: [plan.md](plan.md), Step 3.

Status: **`complete`**.

## Result

- nctl commit `58871055c9c2bfae57a2646c9a7455251d6a2f17` replaces the historical
  `test_compatibility_snapshots.py` with `test_current_consumer_contracts.py`.
- `nctl/docs/compatibility.md`, `event-log.md`, and `output-format.md` now follow the root
  coordinated matched-version rollout rule. They name current writers/readers and the minimal
  durable historical-reader obligation for operation evidence.
- The replacement uses exact current field sets rather than additive-only floors. It detected and
  then recorded two existing `nctl.apply.dnsmasq.v2` fields (`ssh_preflight`, `setup`) and three
  existing `nctl.render.dnsmasq.v3` fail-closed fields (`partial_conf_preview`, `blocked`,
  `blocking_findings`) which the old floor snapshots had not named.
- The source-text event-name grep was removed. Real JSONL/index write-read, corruption, restart,
  and historical-dashboard-field behavior remain owned by the operations-index tests.

## Verification

`cd nctl && uv run pytest -q tests/test_current_consumer_contracts.py tests/test_operations_index.py tests/test_cli_ops.py tests/test_output.py --durations=20`

Result: **31 passed** in 0.16 s. The direct obsolete-policy scan found no additive-floor,
deprecation-window, or parallel-runtime-writer claim in the revised docs or test.

No compatibility-only producer, alias, or retained dashboard presentation field was introduced;
historical operation evidence remains covered by its existing reader tests.
