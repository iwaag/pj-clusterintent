# Phase 0 Step 5 — Apply the minimum classification rules

Parent: [plan.md](plan.md), Step 5.

Step 4's grep-based manifest is a string-token pass. This step traces imports/callers to catch
coupling that string matching misses, per plan §4's "do not classify only by filename... trace
imports/callers" instruction.

## `delete` group — one addition found by import trace

`git grep` on the plan's token list did not match `nctl/src/nctl_core/serve/artifacts.py` (no
occurrence of `dashboard`/`serve`/`FastAPI`/etc. token strings in that file — it imports only
`OperationRecord` from the shared `operations_index` module). Tracing `serve/app.py`'s imports
found `from nctl_core.serve.artifacts import list_public_artifacts, resolve_public_artifact`.
Reading the file confirms it is "the public, allowlisted view of operation artifacts" described by
plan §4.5 as a server adapter to delete ("delete only the server adapters for public artifact
allowlisting..."), distinct from the shared `nctl_core/artifacts.py`/`operations_index.py` it
wraps. Its only importer is `serve/app.py`. **Added to `manifest.tsv` as `delete`/Phase 1.**

This raises the `delete` total from 23 to **24 files**, still exactly the plan §5 minimum set
(directory membership `nctl_core/serve/` implies every file under it, and `serve/artifacts.py` is
under that directory) plus `test_events_bus.py`.

No other delete-classified file has a retained (non-`serve`/non-`dashboard`) importer:

```text
nctl_core.dashboard_render / nctl_core.serve.runtime importers -> cli/main.py, reconcile/executor.py
```

Both importers are themselves classified `edit` (they keep most of their behavior and only lose
the dashboard/serve call sites), not `delete` — consistent with plan §5's `edit` list.

## `keep-shared` minimum — explicitly confirmed present and genuinely shared

The five modules plan §5 names as the minimum `keep-shared` set had **zero** token matches in
Step 4 (expected — they should not mention dashboard/serve vocabulary at all) and so do not appear
as manifest rows from the grep pass. Import-tracing confirms each has a real retained-CLI importer
independent of `serve/`/`dashboard/`:

| Module | Retained (non-serve/dashboard) importers |
|---|---|
| `nctl_core/artifacts.py` | `ansible.py`, `dnsmasq_apply.py`, `jobs.py`, `observation.py`, `reconcile/executor.py`, `ssh_enroll.py` |
| `nctl_core/operations_index.py` | `ops_render.py` |
| `nctl_core/ops_render.py` | `cli/main.py` |
| `nctl_core/output.py` | 14 non-serve/dashboard modules incl. `cli/main.py`, `status.py`, `drift_render.py`, `production_render.py` |
| `nctl_core/reconcile/lock.py` | `config.py`, `reconcile/executor.py`, `ssh_enroll.py` |

Each is genuinely a shared kernel dependency, not a serve-only helper that happens to be named
generically. None is added as a manifest row (they are outside the removal scope entirely, with no
edit required), but this table is the required explicit protection evidence.

## `edit` group — nintent field/link spot-check

Representative `nintent` matches were read directly (not inferred from filename) in report4.md's
evidence gathering: `tables.py`'s `reconciliation_status` column renderer, `filters.py`'s filter
field list, `navigation.py`/`views.py`/`urls.py`'s `dashboard_url`/`dashboard_redirect` chain, and
`api/serializers.py`'s docstring justification ("`reconciliation_status`... stay writable because
nctl dashboard is [the writer]"). All twelve `nintent` `edit` rows are confirmed real dashboard/
cache-field couplings, not incidental string matches (e.g. a template comment).

## `historical` group — no active instruction disguised as history

Spot-checked `devdocs/big/vm/p3/report3.5.md` (kept historical — it truthfully records what Step 5
of that phase implemented, including the still-current `dashboard`/`ReconcileData` field, and does
not instruct future work) against `devdocs/big/vm/p3/plan.md` (an active document, correctly
classified as needing edits and handled by this phase's own Step 7, not listed as a manifest
`historical`/`edit` row here since it is out-of-manifest-scope by the plan's own Step 7 procedure).
`devdocs/big/braindump/roadmap.md` and `devdocs/big/core_reconcile/roadmap.md` remain `edit`
(Phase 4) rather than `historical` because both are active roadmap documents that still narrate the
dashboard/realtime-API goal as current, which `devdocs/vision/refactor/vision.md` (§"Documents
every roadmap must read") explicitly says is superseded.

## Gate

`test_events_bus.py` is confirmed present in the `delete` set (from Step 4). No shared
operation/evidence helper was absorbed into `delete` — the import trace above is the positive
proof, not just an absence of a grep hit. No `historical` row instructs active work; the two
active-but-outdated roadmaps are `edit`, not `historical`.
