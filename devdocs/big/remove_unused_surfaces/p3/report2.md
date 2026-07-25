# Phase 3 Step 2 — Remove model fields and generate migration 0016

Parent: [plan.md](plan.md) Step 2.

Executed 2026-07-25. Private evidence directory:
`.local/remove-unused-surfaces/p3/20260725-162655/` (mode `0700`, files `0600`).

nintent commit: `55be38b4eaccb3c68edbe6d7551a2c1b50169e93` (`models.py` +
`migrations/0016_remove_reconciliation_dashboard_surfaces.py` only — the filters/tables/
templates/views/urls/navigation/`__init__.py`/serializer edits needed to make the app importable
again are Step 3's own commit, see `report3.md`).

## Deviation: Steps 2 and 3 required combined implementation before either could be verified

Exactly the same cross-step coupling recorded in `p2/report8.md` §3: Django loads the whole app
(`urls.py` -> `views.py` -> `filters.py`) as one unit, so `nautobot-server makemigrations` failed
immediately with `TypeError: 'Meta.fields' must not contain non-model field names:
reconciliation_status` the moment `models.py`'s fields were removed but `filters.py` still
referenced them. This is a genuine interdependency in the plan's own step boundary, not an
implementation mistake — Step 3's filters/tables/views/urls/navigation/settings/serializer edits
(plan §5.2) had to land before Step 2's migration-generation gate could be exercised at all. Both
steps' file edits are recorded together here; `report3.md` covers Step 3's own verification and
gate separately, matching the file inventory split, not a re-run of Step 2's evidence.

## 1. Model changes

`nintent/nautobot_intent_catalog/models.py`: removed both duplicated
`RECONCILIATION_CONVERGED`/`RECONCILIATION_DRIFTING`/`RECONCILIATION_CONVERGING`/
`RECONCILIATION_UNKNOWN`/`RECONCILIATION_STATUS_CHOICES` blocks and both
`reconciliation_status`/`reconciliation_checked_at` field declarations (one pair on
`DesiredService`, one pair on `DesiredNode`). No other model/field/constraint changed.

## 2. Migration `0016_remove_reconciliation_dashboard_surfaces.py`

Generated via `nautobot-server makemigrations nautobot_intent_catalog
--name remove_reconciliation_dashboard_surfaces` against the running container with local Step
2/3 source `docker cp`'d over the installed package (§6.2 scratch technique — the live `nautobot`
database was never targeted; this command only inspects model state vs. the migration graph, it
does not touch any database).

- Depends directly on `("nautobot_intent_catalog", "0015_compute_platform_instance_and_endpoint_mac")`.
- Exactly four `migrations.RemoveField` operations (`DesiredNode.reconciliation_checked_at`,
  `DesiredNode.reconciliation_status`, `DesiredService.reconciliation_checked_at`,
  `DesiredService.reconciliation_status`) — no `RunPython`, data copy, replacement model, rename,
  default, or compatibility branch.
- Header comment added (hand-review note, matching `0015`'s convention) after generation; no
  operation was edited.

`0009_reconciliation_status.py`, `0010_operational_overrides_and_provenance.py`, and
`0015_compute_platform_instance_and_endpoint_mac.py` are **byte-identical** to the container's
installed copies (`diff` confirmed zero difference for all three) — no historical migration
changed.

## 3. Consistency checks

- `nautobot-server makemigrations --check --dry-run nautobot_intent_catalog`: `No changes detected
  in app 'nautobot_intent_catalog'` (exit 0) — current models plus `0016` are fully reconciled.
- `nautobot-server check`: `System check identified no issues (0 silenced)`.
- Live migration state reconfirmed unchanged: `showmigrations nautobot_intent_catalog` on the
  default (live `nautobot`) database still ends at `0014`; `0015`/`0016` both unapplied there.

## 4. Local Django-free suite

`python3 -m unittest discover -s nautobot_intent_catalog/tests`: **187 passed**, unchanged (no
Django-free fixture/loader test touches these fields).

## Gate

Current models have no cache contract; `0016` is exactly four field removals depending directly on
`0015`; `0009`/`0010`/`0015` are unchanged; `makemigrations --check --dry-run` is clean. Step 2 gate
met (jointly verified with Step 3's edits per the deviation above — see `report3.md` for Step 3's
own file-by-file inventory and test gate).
