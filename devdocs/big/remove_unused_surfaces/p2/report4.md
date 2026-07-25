# Phase 2 Step 4 — Remove active wording and update current nctl docs

Parent: [plan.md](plan.md) Step 4.

Executed 2026-07-25. Private evidence directory:
`.local/remove-unused-surfaces/p2/20260725-155334/`, additionally containing
`step4-full-tests.txt`.

## 1. Active source/test wording updated (no behavior change)

- `nctl/src/nctl_core/drift_render.py`: `render_drift_data()`'s docstring dropped "...rather than
  reimplementing this shape" `nctl dashboard` reference, now names only `nctl drift`.
- `nctl/src/nctl_core/sources/desired.py:40`: dropped "dashboard," from "no compute drift,
  planner, dashboard, or reconcile action is added in this step."
- `nctl/tests/test_vm_p3_compute_stays_inert.py:2`: module docstring dropped "dashboard/" from
  "compute drift/planner/dashboard/reconcile dispatch."

All three are comment/docstring-only edits; `grep -n "dashboard"` against each file now returns
zero matches, and the full suite (below) confirms no behavior changed.

## 2. Current nctl documentation updated

- **`nctl/README.md`**: removed the four `nctl dashboard...` usage-example lines; replaced the
  `dashboard` command's whole prose block (routine-command description, status-push behavior) with
  a short paragraph naming `nctl drift` as the supported fresh-status read; renamed "Status
  legend"'s "Dashboard tiles and nintent's reconciliation-status badges" framing to "`nctl drift`
  targets," dropped the `color` column (tied to the removed HTML rendering), and added guidance to
  cross-check `nctl ops show`/`result.json` history against a fresh `nctl drift`; deleted the
  entire "Status write-back" subsection (PATCH behavior no longer exists); removed the "Dashboard
  reuse" bullet from the `reconcile` section; removed "`dashboard` result" from the
  `nctl.reconcile.v2` field list; removed "dashboard" from the Braindump import-boundary sentence;
  deleted the entire "## Dashboard configuration" section (`[dashboard]` TOML example and
  `dashboard_url`/nintent-plugin-setting cross-reference).
- **`nctl/docs/compatibility.md`**: removed the `nctl.dashboard.v1` row from the frozen schema
  table.
- **`nctl/docs/output-format.md`**: removed "(the dashboard's only input, and...)" parenthetical
  from `nctl.drift.v1`'s description; deleted the entire `## nctl.dashboard.v1` section (example
  payload + prose); removed "dashboard health" from the Braindump isolation sentence.
- **`nctl/docs/usage_example.md`**: removed the "Regenerate the dashboard" → `nctl dashboard` row.
- **`nctl/docs/event-log.md`**: re-searched per plan §5.4 — no dashboard coupling found, no edit
  needed (matches the plan's own prediction).

No replacement GUI, dashboard alias, or new "current status" surface was introduced anywhere in
these edits — every replacement points at `nctl drift`, reconcile artifacts/`result.json`, or
`nctl ops list/show`, matching plan §5.4's required framing exactly.

## 3. Post-edit verification

- `grep -rni "dashboard" nctl/README.md nctl/docs/*.md` → zero matches across all four edited
  files plus `event-log.md`.
- Full nctl suite: **953 passed** (unchanged from Step 3 — confirms these were pure documentation/
  comment edits with no source behavior touched).

## 4. Root/cross-initiative matches confirmed as known Phase 4 territory

`grep -rli dashboard README.md README_DEV.md devdocs/big/*/roadmap.md devdocs/big/vm/p3/plan.md`
returns: root `README.md`; `devdocs/big/braindump/roadmap.md`; `devdocs/big/better_usability/
roadmap.md`; `devdocs/big/core_reconcile/roadmap.md`; `devdocs/big/remove_unused_surfaces/
roadmap.md` (this initiative's own roadmap); `devdocs/big/vm/roadmap.md`; `devdocs/big/vm/p3/
plan.md`. Every one of these is explicitly out of scope for Phase 2 per plan §3.3/§5.4 (root
README and cross-initiative current roadmaps are Phase 4 work) — no newly introduced instruction
was found among them, only the already-known set the plan predicted.

## Gate

Current nctl package docs direct users to drift/reconcile/ops only (no `nctl dashboard` command,
config, schema, or status-push mention remains in any of the four edited files), and no active
source/test comment implies a dashboard consumer or dispatch path (`sources/desired.py`,
`drift_render.py`, `test_vm_p3_compute_stays_inert.py` all confirmed clean). Step 4 gate met.
