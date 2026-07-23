# Automated Verification — Standard Local Commands

Run from the repository root after Steps 1-5 (commit `75f4392`).

```
$ PYTHONPATH=nintent python3 -m unittest discover -s nintent/nautobot_intent_catalog/tests
Ran 111 tests in 0.016s
OK
Exit code: 0
```

(`python3 -m unittest discover -s nintent/nautobot_intent_catalog/tests` alone fails with
`ModuleNotFoundError: No module named 'nautobot_intent_catalog'` because the package root is
`nintent/`, not the repo root — `PYTHONPATH=nintent` is required regardless of this plan's changes;
this is a pre-existing property of the checkout layout, not a regression.)

```
$ uv run --project nctl pytest nctl/tests -q
984 passed, 1 warning in 5.93s
Exit code: 0
```

(The warning is `StarletteDeprecationWarning` from `test_serve_ws.py`, unrelated to this plan.)

```
$ git status --short
(empty)
$ git -C nintent status --short
(empty)
$ git -C nctl status --short
(empty)
```

All three worktrees are clean after the commits for Steps 1-5 — no unintended changes.

## Test counts by step

- Step 1 (nintent `operations/ipam.py`): 31 tests in `test_operations_ipam.py`
  (18 pre-existing + 13 new/replaced), full nintent suite 111/111.
- Step 3 (nctl drift/classify): `test_drift_evaluation.py` +6,
  `test_drift_comparators.py` +1, `test_reconcile_classify.py` allowlist +
  parametrization entries.
- Step 4 (nctl reconcile pinning/coverage): `test_reconcile_planner.py` +2,
  `test_reconcile_ledger.py` +5, `test_reconcile_executor.py` +2 unit tests
  and +1 real multi-round test (`test_real_multi_round_ipam_convergence_for_non_dhcp_endpoint`)
  exercising the real drift engine, `classify()`, planner endpoint-pinning,
  and executor coverage/mutation logic end to end (only the Nautobot snapshot
  fetch and the Job's own execution are mocked).
- Full nctl suite: 984/984 passing throughout, no regressions introduced at
  any step.

## What remains unverified locally (by design)

Per plan.md's Verified Baseline, the following require the deployed Nautobot
environment and are addressed in the next phase, not here:

- Real Django queryset behavior for the widened
  `.exclude(ip_address__isnull=True).exclude(ip_address="")` filter.
- Real `IPAddress.type` model choices (whether a Host-equivalent choice
  actually resolves the way `_resolve_type_choice` expects).
- `nautobot-server makemigrations nautobot_intent_catalog --check --dry-run`
  (expected to report no changes; no model fields changed).
- Job discovery and the updated `Meta.description` inside a running Nautobot.
- Celery-worker execution of the widened queryset against real
  Device/`_custom_field_data` rows.

## Status

Automated verification (local suites + real multi-round test) complete and
green. Ready for the Nautobot-backed and live verification phase, which
requires a user-approved push, container rebuild, and supervised scoped apply
— see plan.md's "Nautobot-backed and Live Verification" section.
