# Step 1.1 — Freeze the implementation baseline and guardrails

Status: complete.

## 1. Phase 0 approval

User explicitly approved `devdocs/big/braindump/p0/plan.md` as the authoritative minimal contract
via AskUserQuestion on 2026-07-21 ("Approve, proceed to Phase 1"). This was the sole remaining
Phase 0 exit criterion. Phase 1 implementation may begin.

## 2. Baseline evidence

- nintent submodule commit: `60a62a60ef6495d76a6fc261867dea5d765402ea` (heads/main)
- nctl submodule commit: `f211c9ec70c02141b8180f95132c7541a9b00cc1` (heads/main)
- nintent version: `0.8.0` (`nintent/pyproject.toml`, `nintent/nautobot_intent_catalog/__init__.py`)
- Latest migration: `nintent/nautobot_intent_catalog/migrations/0013_analysis_provenance_and_generic_endpoint_policy.py`
- Installed Nautobot version: 3.1.3 (per plan.md; containers `nautobot-nautobot-1`,
  `nautobot-nautobot-worker-1`, `nautobot-nautobot-scheduler-1` all `Up 3 hours (healthy)` at
  baseline time)
- Local Django-free suite:

  ```
  uv run --project nintent python -m unittest discover -s nintent/nautobot_intent_catalog/tests
  Ran 98 tests in 0.017s
  OK
  ```

  98/98 passing, matching plan.md's stated baseline.

## 3. Name-collision search

```
grep -rIn --include="*.py" -iE "BrainDumpDocument|AlignmentReview|braindump|alignment_review" nintent nctl
```

No output — no existing model, prototype, or reference to these names in either submodule. This
confirms the Phase 1 work is purely additive with nothing to migrate away from.

## 4. `nctl drift --json` baseline

Command: `uv run nctl drift --json` (run from `nctl/`, with `NAUTOBOT_TOKEN` set to the token
documented in `.local/localenv_memo.md`).

Result: `ok: true`, schema `nctl.drift.v1`.

- summary: `{"converged": 2, "unknown": 4}`
- severity_summary: `{"error": 6, "warning": 4, "info": 5}`
- targets: 6

Full JSON saved locally at `/tmp/drift_baseline.json` for the Step 1.8 no-side-effect comparison
(not committed; contains no tokens, but is real cluster target/finding data). No Braindump/private
content applies at this baseline since the feature does not exist yet.

## Discrepancies

None. Baseline matches plan.md's "Current state" section exactly. No schema-affecting discrepancy
that would change the plan. Proceeding to Step 1.2.
