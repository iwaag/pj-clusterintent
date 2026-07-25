# Phase 3 Step 5 — Prove the 0015-to-0016 migration on a disposable database

Parent: [plan.md](plan.md) Step 5.

Executed 2026-07-25.

## 1. Scratch database setup (real PostgreSQL, disposable clone — not the shared `nautobot` database)

Same technique as VM Phase 3 Steps 2-4 (`.local/localenv_memo.md`): `pg_dump -Fc nautobot` from
`my_postgres_db` → `pg_restore --no-owner` into a fresh `nautobot_p3_step5_scratch` database
(exact clone of live schema+data, still at migration `0014` at restore time — the live database's
own migration state, unaffected by the pointer bump work already committed in the repo). Every
migration command below was run with `NAUTOBOT_DB_NAME=nautobot_p3_step5_scratch` explicitly set
and the database name positively confirmed before each command; the live `nautobot` database
(default alias) was never targeted by any `migrate` call this step.

## 2. Pre-migration state (representative nonblank data, not an empty database)

Cloned from the live database, so the cache values are the same real ones recorded in Step 0:

| Model | Rows | `reconciliation_status` breakdown |
|---|---|---|
| DesiredNode | 5 | 5 `converged` (nonblank) |
| DesiredService | 6 | 1 `converged` (nonblank), 5 blank |

Both `reconciliation_status`/`reconciliation_checked_at` columns confirmed present via `\d` on
both tables before any migration ran. Recorded id/name/slug/lifecycle for all 5 nodes and
id/name/slug/service_type for all 6 services as the before-comparison baseline.

## 3. Forward migration

- `nautobot-server migrate nautobot_intent_catalog 0015`: applied cleanly (the legacy
  `realized_vm` in-transaction guard in `0015` found zero non-null rows, matching VM Phase 3's own
  finding). `showmigrations` confirmed `0015` applied, `0016` not yet.
- `nautobot-server migrate nautobot_intent_catalog 0016`: applied cleanly. `showmigrations`
  confirmed both `0015` and `0016` now applied.

## 4. Post-migration verification

- **Physical columns**: `\d` on both `nautobot_intent_catalog_desirednode` and
  `..._desiredservice` shows zero `reconciliation_*` columns — all four physically absent.
- **ORM fields**: `DesiredNode`/`DesiredService` — `"reconciliation_status" in [f.name for f in
  ._meta.get_fields()]` is `False` for both, confirmed via `nautobot-server shell` against the
  scratch database.
- **Row counts**: DesiredNode 5, DesiredService 6 — unchanged.
- **Row identity**: id/name/slug/lifecycle for all 5 nodes and id/name/slug/service_type for all 6
  services are byte-identical before vs. after (`diff` against the Section 2 capture).
- **Compute preservation**: `nautobot_intent_catalog_desiredcomputeplatform` and
  `..._desiredcomputeinstance` tables (introduced by `0015`) both present;
  `nautobot_intent_catalog_desiredendpoint.mac_address` column and its
  `nic_unique_desired_mac_address` unique constraint both present.
- **`makemigrations --check --dry-run nautobot_intent_catalog`**: `No changes detected` (exit 0).

The nonblank `converged` cache values (5 node rows + 1 service row) were present immediately before
`0016` ran and are gone (column no longer exists) immediately after — this is a real
data-discarding proof, not a migration run against an empty database. No reverse-schema check was
run this step (plan §6.3 marks it optional); the forward proof above is sufficient and is not
represented as reversible.

## 5. Cleanup

`DROP DATABASE nautobot_p3_step5_scratch` and `rm` of the `pg_dump` file, both confirmed
(`psql -l` no longer lists the scratch database). Live `nautobot-server showmigrations
nautobot_intent_catalog` (default alias, the real live database) reconfirmed unchanged at `0014`
throughout this step — no live migration, schema change, or data mutation occurred.

## Gate

Nonblank cache data was exercised and discarded exactly as designed; all four columns are
physically absent; row counts, identity, and unrelated (compute/endpoint) schema are unchanged;
`makemigrations --check --dry-run` is clean; no live database state changed. Step 5 gate met.
