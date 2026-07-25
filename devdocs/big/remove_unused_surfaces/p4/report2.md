# Phase 4 Step 2 — Update root and component documentation

Parent: [plan.md](plan.md) Step 2.

Executed 2026-07-25.

## 1. root `README.md`

- Removed `nctl dashboard` (2 command-block lines) and `nctl serve` command-block lines; replaced
  with `nctl ops list`/`nctl ops show OPERATION_ID`.
- Removed the `nctl dashboard` prose paragraph (regenerates static HTML, pushes derived cache) and
  the `**nctl serve**` prose paragraph (HTTP+WebSocket subscriber API); replaced with one paragraph
  stating fresh `nctl drift --json` is the current-status source and `nctl ops list/show` is the
  operation-evidence reader.
- Fixed two pre-existing broken links found during Step 1 link-tracing (`devdocs/vision/core_reconcile/...`
  does not exist; corrected both to `devdocs/big/core_reconcile/...`, which does).
- Verified: no remaining `dashboard`/`serve` token in the file; both corrected links resolve
  (`ls`-confirmed); the `uv run --project nctl nctl ...` command style is unchanged for all retained
  lines.

## 2. `nintent/README.md`

- Removed the sentence naming REST as `nctl dashboard`'s PATCH write path for
  `reconciliation_status`/`reconciliation_checked_at`.
- Replaced the "Reconciliation status fields and the dashboard link" section (cache-field semantics,
  `dashboard_url` setting, nav link, `dashboard_redirect` view) with a "Current status and operation
  evidence" section stating nintent has no reconciliation-status field and no dashboard setting/link,
  and pointing to fresh `nctl drift` and `nctl ops list/show` as the retained inspection paths, with
  a link to the removal roadmap.
- Verified: the file's only remaining `dashboard`/`reconciliation_status` mentions are inside that
  new section, explicitly framed as removed (`grep -n` re-run, 2 lines, both descriptive-of-removal).

## 3. `nintent/README_QUICK.md`

- Replaced the `nctl dashboard` command line with `nctl ops list`/`nctl ops show OPERATION_ID`.
- Replaced the prose describing `nctl dashboard`'s PATCH write-back and `dashboard_url` nav-link
  setup with a sentence naming `nctl ops list/show` as the evidence reader and stating nintent has
  no reconciliation-status field or dashboard setting, linking the removal roadmap.
- Verified: remaining `dashboard`/`reconciliation_status` mentions (2 lines) are both
  descriptive-of-removal.

## 4. Files reviewed, no change needed (§5.2, reconfirmed from Step 1)

`nctl/README.md`, `nctl/docs/output-format.md`, `nctl/docs/compatibility.md`,
`nctl/docs/usage_example.md`, `nctl/docs/event-log.md`, `nctl/example.nctl.toml`,
`nintent/README_DEV.md`, root `README_DEV.md`, `devenv/nautobot/nautobot_config.py` — zero token
matches at Step 1, re-verified unchanged (`git status` shows no modification to any of these files
from this step). Recorded as `verified-current`.

## 5. Working-directory convention and link check

Root examples use `uv run --project nctl nctl ...`; `nintent/README_QUICK.md` uses bare `nctl ...`
(nctl-local convention) — both unchanged and consistent with plan §9 Step 2.8. All Markdown links in
the three edited files resolve (`ls`-confirmed for each target). `git diff --check` clean in both
repositories.

## Gate

Current operational docs contain only retained commands/config/contracts and explain where fresh
status and operation evidence come from. Step 2 gate met.
