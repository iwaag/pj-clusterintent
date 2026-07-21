# Phase 4 Step 4.8 — Coordinated rollout and live-safe verification

Parent: [plan.md](plan.md), Step 4.8. Phase 4's final step — closes the roadmap.

## Revisions deployed

| Submodule | Revision | Pushed |
|---|---|---|
| nintent | `3e38769` | yes (Steps 4.2/4.3/4.5 batched) |
| nctl | `f211c9e` | yes (Steps 4.4/4.5/4.7 batched) |
| nauto | `f1f9aea` | yes (Step 4.6) |
| ansible_agdev | `3020b93` | unchanged this phase |
| nodeutils | `95a2dfc` | unchanged this phase |

## 1–3. Backup, preflight, rebuild, migration

- **DB backup**: `pg_dump -F c` from `my_postgres_db`, 1.5 MB, 2389 TOC entries, verified with
  `pg_restore --list` inside the container. Stored in the session scratchpad, not the repo (per
  this step's own instruction not to commit a DB backup).
- **Live preflight**: `nctl status` confirmed clean submodules and Nautobot connectivity before
  touching anything.
- **Rebuild**: `docker compose build` initially **cached** the `pip install
  git+https://github.com/iwaag/nprojects.git` layer and silently kept the pre-Phase-4 nintent —
  the Dockerfile has no cache-busting mechanism for a moving Git ref. Caught before applying the
  migration: `docker compose build --no-cache` re-resolved and confirmed commit `3e38769` in the
  build log. Recorded here as a real operational gotcha for any future nintent-only rebuild, not
  just a Phase 4 particular.
- **Migration**: applied automatically on `nautobot-nautobot-1` container startup —
  `Applying nautobot_intent_catalog.0013_analysis_provenance_a... OK 0.37s`. The guard against a
  non-empty `placement_policy` did not fire (would have aborted the migration with a
  `RuntimeError`), confirming Step 4.1's live preflight finding held at migration time.
  `showmigrations`: all 13 migrations through `0013_*` applied. `nautobot-server check`: "System
  check identified no issues (0 silenced)." `makemigrations --check --dry-run`: "No changes
  detected."

## 4–5. nctl cutover and REST/GraphQL verification

nctl was already at the matching revision throughout (local development, not a separate deploy
step). Verified live against the rebuilt Nautobot:

- `GET /api/plugins/intent-catalog/services/` — previously 500ed
  (`p4/fixtures/service_rest_list_pre.json`, Step 4.1); now returns 200 with `intent_source` as a
  plain UUID, `analysis_provenance: {}`, and **no** `placement_policy` key.
- `PATCH` a status-only field (`reconciliation_status`/`reconciliation_checked_at`) — succeeds.
- `PATCH analysis_provenance` — silently ignored (DRF read-only field behavior), value stays `{}`,
  confirming the read-only contract holds live, not just in unit tests.
- Quick Add page (`/plugins/intent-catalog/nodes/quick-add/`) renders with `node_type` `device`
  selected by default and the derived-accepted-types preview markup present — Step 4.2's UI
  change is live.
- GraphQL introspection on `DesiredServiceType`: `placement_policy` absent, confirming the schema
  itself changed, not just nctl's query.

`IntentSource` detail/edit pages require session login (302 redirect) — this dev instance's
anonymous-read policy does not cover that view, unlike Quick Add's `FormView`. Not a Phase 4
regression (unrelated to any change this phase made); not further pursued since the Quick Add
verification above already confirms the relevant UI change.

## 6. Pre/post data comparison

Read-only GraphQL snapshot (all node lifecycle/type/accepted-types, endpoint policy/publishing/DNS
values, service requirements, and placement config) captured before the rebuild
(`p4/fixtures/pre_migration_snapshot.json`) and after (`post_migration_snapshot.json`):

```
diff pre_migration_snapshot.json post_migration_snapshot.json
(exit code 0 — zero differences)
```

Every value the migration was never supposed to touch is confirmed byte-identical.

## 7. Status/drift/render/dashboard/reconcile, read-only and dry

- `nctl status`: `ok: true`, now shows the new `target state: use \`nctl drift --host SLUG\`` hint
  live.
- `nctl drift --host agpc`: renders the new compact `intent`/`effective`/`application` three-line
  format live, correctly showing `accepted_actual_types=(none) (override)` for agpc's empty
  stored list (differs from the canonical `["device"]` derivation, correctly classified
  `override` per Decision 4) and the known stale-observation finding.
- `nctl drift --json` (full cluster): `ok: true`, 6 targets, exactly one `intent_effect_summary`
  per desired node (5/5), no `UnclassifiedDiffCodeError`.
- `nctl render production --json`: `ok: true`, report `schema_version: "3.0"` with a closed
  `nodes` array of exactly 5 (every desired node), inventory `schema_version` unchanged at
  `"2.0"`.
- `nctl dashboard --no-push`: generates cleanly; the embedded drift JSON carries
  `intent_effect_summary` for all 5 nodes (the three-section/badge rendering itself is client-side
  JS this environment cannot execute to screenshot — verified by code review in
  `report4.5.md` and by confirming the complete, correctly-shaped data reaches the page; a full
  browser render was not captured).
- `nctl reconcile --json` (dry, cluster scope): `ok: true`, `state: planned`, 3 manual-review
  records, 0 automatic actions — no crash, no unclassified code.

## 8. Live write: dashboard status push (with approval)

With explicit operator approval, ran `nctl dashboard` (push enabled):
`status_push: {pushed: true, attempted: 6, updated: 6, skipped_no_row: 0, failed: 0, errors: []}`.
Confirmed via a follow-up REST `GET` that the `dnsmasq` service's `reconciliation_status`/
`reconciliation_checked_at` updated to match the run — the last deferred proof point from
`report4.5.md` item 7 ("prove dashboard service status write-back succeeds on the new nintent
serializer") is now closed with a real live write, not just isolation logic.

**Not run, by explicit operator decision**: creating/deleting a disposable node/service to
literally walk the new recipes end-to-end. Verification against existing live targets (extensive
read-only checks above, plus the real status-push write) was judged sufficient; `nctl reconcile
--yes` / SSH actuation against real machines remains out of scope for this tooling phase, matching
the already-known stale-nodeutils infrastructure finding from Phase 3
([[project-better-usability-p3]]), which Phase 4 does not attempt to fix.

## Known infrastructure limitation (unchanged by this phase)

`agpc`/`agstudio` nodeutils collection remains stale (`stale_actual_data`), and `aghub` has no
realized object at all — the same finding recorded at the end of Phase 3. Left visible, not
mutated to force a green result, per this step's own explicit instruction.

## Test totals (unchanged from Step 4.7, no code changed this step)

nintent **98** passed · nctl **617** passed · nauto **14** passed.

## Result

Phase 4 is complete. Every desired node has exactly one `intent_effect_summary`; drift text, JSON,
dashboard, and production report all consume the same report-3.0 node record; production inventory
is schema `2.0` and confirmed byte-stable; the companion report is schema `3.0` and closed;
`deployment_profiles_unavailable` is a classified global blocker; Quick Host Add defaults to
`device` with a visible accepted-type derivation/override; `IntentSource` caches and
`analysis_provenance` are read-only and confirmed live; operator `requirements` are proven
protected from analysis overwrite; `placement_policy` and all its readers/writers are deleted; the
nauto seed is proven valid under its real owner; and both recipes reflect the current UI + drift +
reconcile flow. All of this is now running against the live Nautobot instance, not just committed
code.
