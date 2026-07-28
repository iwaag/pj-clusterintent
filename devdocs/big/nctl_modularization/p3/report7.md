# P3 Step 7 — Text rendering

Status: complete.

- Extracted `render_reconcile_text` verbatim to `nctl_core.reconcile_render`.
  It consumes a completed public envelope and makes no planning, round, or
  execution decision.
- Repointed the sole CLI consumer; no compatibility import was retained.
- CLI/reconcile focused coverage passed: **49 passed**.

Implementation commit: nctl `786b61b`.
