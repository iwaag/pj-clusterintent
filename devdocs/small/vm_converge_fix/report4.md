# Step 4 Report — Forced observation truthfulness

Status: complete.

The reconcile loop already limited `--refresh-observation` to the first round. This step completed
the failure boundary:

- the forced action carries `forced_refresh` in its plan parameters/evidence;
- a failed first-round forced observation terminates the round before production regeneration,
  ingest, or ledger-link work can claim progress; and
- the operation reports `observation_failed` rather than a stale-snapshot `converged` result.

Normal drift-driven observation behavior remains unchanged. Successful forced observation continues
to allow a second round to use fresh evidence without a second forced collection.

Verification, from `nctl`:

```text
uv run pytest -q tests/test_reconcile_planner.py tests/test_reconcile_executor.py tests/test_reconcile_ledger.py --durations=20
-> 104 passed

uv run pytest -q --durations=20
-> 1007 passed
```

The new executor regression covers: forced collection failure -> failed operation -> one failed
`observe_node` action and no downstream ingest/link claim. Existing refresh success coverage proves
one collection followed by convergence.
