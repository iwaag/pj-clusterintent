# P3 Step 2 — Reconcile result contract

Status: complete.

- Moved `RECONCILE_SCHEMA`, `ActionResult`, `RoundSummary`, and `ReconcileData`
  textually to `nctl_core.reconcile.results`.
- Repointed the executor and current-consumer contract test; no compatibility
  re-export was introduced.
- The `nctl.reconcile.v2` string, model field names, defaults, and consumer
  contract test remain unchanged.
- `uv run pytest -q --durations=20` passed: **970 passed**.

Implementation commit: nctl `6d9ef99`.

