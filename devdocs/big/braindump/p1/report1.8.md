# Step 1.8 — Deploy once, run live smoke checks, and close the phase

Status: complete. Phase 1 exit criteria all met.

## Revisions and version

- nintent commit committed, pushed (by the user), and installed:
  `aa5a052fdef07e7749b501b6c016eff2fbe10271` (`origin/main` matches local `HEAD` exactly).
- Installed `nautobot-intent-catalog` version: `0.9.0` (confirmed via `pip show` in the rebuilt
  container).
- Root superproject's `nintent` submodule pointer already matches `aa5a052` (each Step 1.1–1.7
  commit updated it incrementally, per the plan's "multiple local commits are acceptable" allowance
  for the nintent side).

## Rollout sequence performed

1. Verified the pushed commit is reachable: `git fetch origin main` on the `nintent` checkout shows
   `origin/main` at `aa5a052`, matching local `HEAD`.
2. **Database backup**: `pg_dump` of the live `nautobot` database, gzipped, to
   `.local/backups/nautobot_pre_braindump_20260721_225612.sql.gz` (502K, 237 `CREATE TABLE`
   statements verified present in the dump). Not committed to git (local-only, `.local/` is outside
   version control per existing convention).
3. **Rebuild with cache-busting**: `docker compose build --no-cache` from `devenv/nautobot`. Build
   log shows `Resolved https://github.com/iwaag/nprojects.git to commit
   aa5a052fdef07e7749b501b6c016eff2fbe10271` and `Successfully installed
   nautobot-intent-catalog-0.9.0` — the exact pushed commit, not a stale cached layer (the known
   [[nintent rebuild cache gotcha]]).
4. **Restart**: `docker compose up -d` recreated `nautobot`, `nautobot-worker`, and
   `nautobot-scheduler`; all reported healthy.
5. **Migration**: the container's entrypoint auto-applied `0014_braindump_exchange_diary` on
   startup (confirmed via `showmigrations` and a direct `to_regclass(...)` check that the
   `nautobot_intent_catalog_braindumpdocument` table exists). Re-ran
   `nautobot-server migrate nautobot_intent_catalog` explicitly (idempotent, no-op) and
   `nautobot-server makemigrations --check --dry-run` → `No changes detected`.
6. **System check**: `nautobot-server check` → `System check identified no issues (0 silenced)`.
7. **Nautobot test module**: `nautobot-server test nautobot_intent_catalog.tests.test_braindump`
   against the rebuilt live image → `Ran 33 tests ... OK` (same environment overrides as Step 1.7:
   `NAUTOBOT_ALLOWED_HOSTS` extended for this invocation only to include
   `nautobot.example.com`/`testserver`, which Nautobot's `TestCase`/`APITestCase` base classes use as
   their default request host; no persistent config file was changed).
8. **Local suite**: `uv run --project nintent python -m unittest discover -s
   nintent/nautobot_intent_catalog/tests` → `Ran 98 tests ... OK`.

## Live UI/REST/GraphQL smoke checks (synthetic content)

All exercised against the running `http://localhost:8000` instance with the existing dev API token
and an admin session login (UI routes require session auth; REST/GraphQL use the token).

- **REST create** (`POST /api/plugins/intent-catalog/braindumps/`): adversarial payload —
  `title = "SMOKE TEST <script>alert(1)</script> 日本語"`, `body` mixing multiline text,
  `<b>html</b>`, `$(rm -rf /)`, and Japanese — returned `201`; response echoed the accepted text
  unchanged (byte-for-byte, no trimming/escaping at the storage layer).
- **UI detail page** (session-authenticated `GET
  /plugins/intent-catalog/braindumps/<uuid>/`): `200`; both `<script>alert(1)</script>` payloads
  (title, and later the review's `<script>alert(2)</script>`) rendered as
  `&lt;script&gt;alert(...)&lt;/script&gt;` — zero raw occurrences, four escaped occurrences found;
  "User-originated Braindump", "AI Alignment Review", and "Unreviewed" all present before a review
  was attached.
- **Review create** (`POST /api/plugins/intent-catalog/alignment-reviews/`, summary containing
  `<script>alert(2)</script> 混在`): `201`.
- **Duplicate review create**: `400`,
  `{"braindump": ["Alignment review with this Braindump already exists."]}` — the framework's
  ordinary uniqueness-validation response, no history row created.
- **Review replacement** (`PATCH` on the existing review): `200`; `summary` updated in place,
  `created` unchanged, `last_updated` advanced — replacement, not a new row.
- **GraphQL** (pinned query from Step 1.6, `POST /api/graphql/`): `200`; returned the synthetic
  document with `authorship: "USER_DIRECT"` (enum), exact `title`/`body` text, and the nested
  `alignment_review` with the replaced summary and its own timestamps.
- **Review-only deletion** (`DELETE` on the review): `204`; the Braindump remained readable
  (`GET` on it: `200`, same title) — confirming review-only deletion preserves its Braindump.
- **Review recreation**: `POST` a new review for the same Braindump: `201` (the one-review
  constraint is per-current-state, not permanently exhausted after a delete).
- **Final Braindump deletion** (`DELETE` on the Braindump): `204`; a subsequent `GET` on the
  now-orphaned review UUID: `404` — cascade deletion confirmed.
- **Cleanup**: a follow-up `title__ic=SMOKE` list query returned `count: 0` — no synthetic rows
  remain.

## Drift-isolation comparison

`nctl drift --json` (with `NAUTOBOT_TOKEN` set) captured immediately before and after the entire
synthetic CRUD window above:

```
before summary:  {'converged': 2, 'unknown': 4}
after  summary:  {'converged': 2, 'unknown': 4}
before severity: {'error': 6, 'warning': 4, 'info': 5}
after  severity: {'error': 6, 'warning': 4, 'info': 5}
before targets: 6
after  targets: 6
identical target/status/codes: True
```

Per-target `status` and sorted diff `code` lists were compared programmatically and found
byte-identical (ordinary fetch timestamps excluded from the comparison, per the plan). Both
snapshots also match the Step 1.1 pre-implementation baseline exactly (`{'converged': 2, 'unknown':
4}`, 6 targets), confirming `nctl drift` remains schema- and shape-compatible
(`nctl.drift.v1`, `ok: true`) across this rollout. `reconcile --yes` and any Ansible actuation were
not run, per the plan.

## Environment changes made during this rollout (for the record)

- Granted `CREATEDB` to the `nautobot` Postgres role (`ALTER ROLE nautobot CREATEDB;`), with the
  user's explicit approval, so `nautobot-server test` could provision its own disposable test
  database (see [[report1.7]] for the original diagnosis). Left in place since it may be needed
  again; reversible via `ALTER ROLE nautobot NOCREATEDB;` if the user later wants it removed.
- No other persistent environment or config file was changed. The `NAUTOBOT_ALLOWED_HOSTS`
  extension was passed only as a one-off `docker exec -e ...` override for the test-runner
  invocations; the container's actual configured environment (`devenv/nautobot/docker-compose.yml`)
  was not modified.

## Exit criteria (from `p1/plan.md`)

- [x] The Phase 0 contract has explicit user approval and no schema-affecting question remains.
- [x] Migration `0014_*` adds exactly `BrainDumpDocument` and `AlignmentReview`, with the exact
      fields, choices, one-to-one relation, timestamps, and cascade behavior in this plan.
- [x] UI users can list, view, create, edit, and delete arbitrary Unicode Braindumps.
- [x] A Braindump detail page visibly separates user-originated text from the zero-or-one current
      AI review and exposes both update times.
- [x] Review create, replacement, review-only deletion, and Braindump cascade deletion work through
      the supported UI and API paths without history rows.
- [x] REST CRUD is live at the two pinned routes, requires explicit programmatic authorship, and
      preserves accepted text unchanged.
- [x] Canonical generated GraphQL names are introspected, documented, tested, and return both
      models with timestamps and relation identity.
- [x] Whitespace validation, Unicode/multiline round trips, one-to-one enforcement, cascade,
      permissions, escaping, REST failures, GraphQL reads, and multiple documents are covered by
      passing tests.
- [x] Diary CRUD produces no desired-state mutation, drift/reconcile change, Job, nodeutils,
      Ansible, or host side effect.
- [x] nintent `0.9.0` is committed, user-pushed, cache-busted into the local Nautobot image,
      migrated once, and verified with system checks and live smoke tests.
- [x] The database backup is verified, synthetic smoke rows are removed, and `report1.1.md` through
      `report1.8.md` record the implementation and rollout evidence without secrets.

**Phase 1 is complete.** The exchange diary (`BrainDumpDocument`/`AlignmentReview`) is durable,
UI/REST/GraphQL-accessible, and verified live, with zero coupling to desired state, drift,
reconcile, Jobs, nodeutils, or Ansible. Phase 2 (`devdocs/big/braindump/roadmap.md`) can begin
building `nctl` reads/writes against the pinned REST routes and GraphQL query documented in
[[report1.6]].
