# Phase 3 Step 7 — Restore the environment, run deletion searches, and measure the final state

Parent: [plan.md](plan.md) Step 7.

Executed 2026-07-25. Private evidence directory:
`.local/remove-unused-surfaces/p3/20260725-162655/` (mode `0700`, files `0600`), containing
`step7-final-deletion-search.txt`, `step7-final-measurements.txt`, `step7-restoration.txt`.

## 1. Missed §5.3 item found and fixed before this step's deletion search

The plan's Step 3 covered §5.2 (nintent runtime/presentation) but this agent's Step 3 execution
skipped §5.3 (`devenv/nautobot/nautobot_config.py`'s deployment `dashboard_url`). Found by this
step's own deletion search (`dashboard_url` still matched
`devenv/nautobot/nautobot_config.py:512`). Fixed immediately: `PLUGINS_CONFIG` changed from
`{"nautobot_intent_catalog": {"dashboard_url": "http://192.168.1.50/nctl-dashboard/"}}` to `{}` —
no other plugin setting existed to preserve, matching plan §5.3's fallback instruction exactly.
`PLUGINS = ["nautobot_intent_catalog"]` (plugin enablement) is untouched. This is a tracked
configuration edit only; no container was rebuilt or restarted, so it is not yet a live mutation
(plan §5.3's own note).

## 2. Container/environment restoration

- Removed the `docker cp`-overridden package from `nautobot-nautobot-1` and restored
  `nautobot_intent_catalog.orig-backup` in its place (the backup created before Step 1's first
  override); no leftover `.orig-backup` directory remains.
- `DROP DATABASE test_nautobot` (the disposable database `nautobot-server test --keepdb` left
  behind across Steps 1/3/6) and reconfirmed neither it nor Step 5's
  `nautobot_p3_step5_scratch` (already dropped in Step 5) remain (`psql -l` clean of both).
- Reconfirmed after restoration: installed `nautobot-intent-catalog` is still `0.9.0` at commit
  `ad9d36397d23c269ad748e13acbccc532fa29f52`; `showmigrations nautobot_intent_catalog` on the live
  (default-alias) database still ends at `0014`; `nautobot-server check` reports 0 issues.
- Re-ran the local nintent suite after restoration: **187/187 passed**, unchanged throughout the
  whole phase.

## 3. Deletion search (final)

Ran the plan §7 eight-token search across `nintent/` and `devenv/`. All 99 matching lines fall into
exactly the plan's named exception buckets, with zero unclassified matches:

- `nintent/nautobot_intent_catalog/migrations/0009_reconciliation_status.py` and
  `0010_operational_overrides_and_provenance.py` (dependency name) — migration history, out of
  scope by plan §3.3/§5.5.
- `nintent/nautobot_intent_catalog/migrations/0016_remove_reconciliation_dashboard_surfaces.py` —
  the four `RemoveField` operations naming the retired fields, the removal itself.
- `nintent/nautobot_intent_catalog/tests/test_remove_unused_surfaces.py` — negative assertions
  (`assertNotIn(...)`, `assertFalse(hasattr(...))`) and their descriptive docstrings/test names
  proving absence, not readers.
- `nintent/README.md` / `nintent/README_QUICK.md` — explicitly Phase-4-owned current documentation
  wording (plan §3.3), intentionally left stale this phase.

`devenv/nautobot/nautobot_config.py` no longer appears in any token's match list after §1's fix.

## 4. Final source/test/migration measurements

| Metric | Step 0 baseline | Final | Delta |
|---|---|---|---|
| Tracked non-test Python (incl. migrations) | 9,665 | 9,560 | −105 |
| Tracked test lines | 3,633 | 4,029 | +396 |
| Tracked template lines | 1,353 | 1,327 | −26 |
| Numbered migrations | 15 | 16 | +1 (`0016`) |
| Local Django-free tests | 187 | 187 | 0 (unchanged — new runtime tests are guarded out locally) |

Diagnostic only, per plan §2.3/§9 — not a completion quota.

## 5. Exact changed-file inventory across the whole phase

`git diff --stat` from the Step 0 baseline revision (`ad0c6424141cea62bf731288ed1f0ca0df4e4711`)
to the current nintent `HEAD`: **12 files** — 10 edits (`__init__.py`, `api/serializers.py`,
`filters.py`, `models.py`, `navigation.py`, `tables.py`, both detail templates, `urls.py`,
`views.py`) + 2 additions (`migrations/0016_...py`, `tests/test_remove_unused_surfaces.py`). Exact
match to plan §5.1/§5.2. `devenv/nautobot/nautobot_config.py` (root repository, §5.3) is the one
additional file outside the nintent submodule.

## Gate

Scratch database/dump and temporary container package override are fully removed/restored; live
nintent is unchanged at its original commit and `0014` migration state; the final deletion search
has zero unexplained active-source/template/config matches after the §5.3 fix. Step 7 gate met.
