# Phase 1 Step 8 — Disposable Nautobot preview/apply/repeat proof

Parent: [plan.md](plan.md), Step 8.

Evidence: `.local/interface-contract/p1/disposable/` (directory mode `0700`, files mode `0600`) —
compose file, config, fixture scripts, and every extracted artifact JSON. No credential, token,
Braindump body, or Alignment Review summary appears in any evidence file (the disposable
superuser token/password are throwaway placeholders local to the torn-down container, never
real secrets).

## 1. Isolation

New compose project `nic-p1-disposable`: a new `postgres:15-alpine` container/database/volume, a
new `redis:7-alpine` container/volume, a `networktocode/nautobot:3.1.3-py3.12` container (plus one
`nautobot-worker` for Git-repository Job sync) built from the **exact local `nintent` working
tree** (`pip install --no-deps /opt/nintent`, a bind mount — not the GitHub-installed package the
live dev stack uses) and the **exact local `nauto` working tree**, registered as a Nautobot
`GitRepository` (`remote_url: file:///opt/repo-git/nauto`, `provided_contents: [extras.job]`) so
Job discovery exercises the real production mechanism (`provides: Jobs`, per `nauto/README.md`).
No bind mount, network alias, or port reference to `my_postgres_db`, `service_scripts-redis-1`,
or port 8000; `nautobot-nautobot-1`/`-worker-1`/`-scheduler-1` were never touched, restarted, or
addressed. The superproject's `.local/` (containing `secrets`) was never mounted — only `.git`
and the two submodule working trees.

## 2. Initialize, migrate, verify discovery (items 1-4)

- Nautobot `3.1.3` initialized against the new database; `nautobot_intent_catalog` migrations
  applied automatically through `0016_remove_reconciliation_dashboard_surfaces` — matching the
  live/local state exactly, confirmed via `showmigrations`.
- `makemigrations nautobot_intent_catalog --check --dry-run` → `No changes detected` (checked
  both before and after every bugfix below).
- Discovered nintent Jobs (`GET /api/extras/jobs/`): exactly `Import Intent Sources`, `Analyze
  Intent Sources`, `Reconcile Desired IPAM Intent` — no `Preview Intent Source Analysis`.
- Discovered nauto Jobs (after Git-repository sync, run for real through the worker):  exactly
  `Seed Home Cluster`, `Ingest Nodeutils Inventory`, `AI Resource Review` — no
  `Generate Desired Services`.

## 3. Three real bugs found and fixed by this proof

Local Django-free unit tests cannot exercise the ORM-backed `_plan_import`/`_apply_import`/
`_plan_analysis`/`_apply_analysis` paths (Nautobot isn't installed locally). Running them for
real against a live database surfaced three genuine defects, none reachable by the existing test
suite:

1. **`jobs.py` `_plan_import`: `ip_range_rows` dict comprehension read `row["slug"]` but the
   `.values()` call omitted `"slug"`.** Silent on the very first Import (no existing IP ranges to
   iterate, so the comprehension ran zero times); crashed with `KeyError: 'slug'` on the second
   Import once ranges existed. Fixed by adding `"slug"` to the `.values()` field list.
2. **Missing intra-batch duplicate-identity detection for `intent_sources`, `desired_nodes`,
   `desired_endpoints`, and `desired_ip_ranges`** (the other five roots already had this check).
   A YAML document with two entries sharing one identity passed the loader, both planned as
   `create` in preview (since planning reads existing DB state once, before any write), then
   silently coalesced into **one** row at apply time (last entry's fields win) — a genuine
   preview/apply parity break, caught live by intentionally injecting a duplicate `agrollbacktest`
   node. Fixed by adding `_duplicate_intent_source_errors`, `_duplicate_desired_node_errors`,
   `_duplicate_endpoint_identity_errors`, and `_duplicate_ip_range_errors` to `loaders.py`,
   matching the existing pattern; each is now a loader error, blocking planning entirely.
3. **`analysis.py` `_source_name()`/`_github_owner_repo()`/`_gitlab_project_path()` crashed on a
   URL-less (manual) `IntentSource`.** `urlparse(None)` silently returns a bytes-mode
   `ParseResultBytes` instead of raising, and the subsequent `.strip("/")` /
   `"gitlab" not in parsed.netloc.lower()` then raised `TypeError: a bytes-like object is
   required, not 'str'`. This is **live-reachable today**: the confirmed "Manual" `IntentSource`
   (Phase 0) has `url=None` and `enabled=True`, so *every* Analyze run against real current data
   would have crashed on this source before even reaching the fixture source. Fixed by an early
   `if not url: return ...`/`return None` guard in all three functions.

Each fix has a new regression test (`test_duplicate_desired_node_slug_is_rejected`,
`test_duplicate_intent_source_slug_is_rejected`, `test_duplicate_git_intent_source_url_is_rejected`,
`test_duplicate_endpoint_identity_without_mac_is_rejected`, `test_duplicate_ip_range_slug_is_rejected`
in `test_loaders.py`; `test_manual_url_less_intent_source_does_not_crash_analysis` in
`test_analysis.py`). Full local suite after all three fixes: 222 nintent tests, `OK`; 110 nauto
tests, `OK`, unaffected.

## 4. Import preview/apply/repeat/rollback/conflict proof (items 5-11, 17)

Fixture (`step8_fixture.py`): one native prerequisite `Device`, an existing `agpc` `DesiredNode`
with `lifecycle=approved` and `realized_device`/`realized_device_source=override` set, and its
`agpc` primary `DesiredEndpoint` with `realized_ip_address_source=override` — the exact kind of
operational/realized state Import must never touch.

- **Preview** (`apply=false`, default): `intent-import-result.json` reported `create: 20,
  update: 1, unchanged: 1, conflict: 0`; the one `update` (`agpc`'s `name`) listed `lifecycle` in
  `preserved_fields`, not `changed_fields`. `writes={attempted: false, committed: false,
  requested: false}`, `transaction.status=not_requested`. Before/after row counts and
  `ObjectChange` count were byte-for-byte identical (0 writes) — re-verified via direct ORM
  query, not just the artifact's own claim.
- **Apply** (`apply=true`): committed one transaction; final counts matched plan Section 4.2
  exactly (2/5/5/3/6/1/0). `agpc.name` became `"agpc"`; `agpc.lifecycle` stayed `"approved"`;
  `agpc.realized_device_id` and the endpoint's `realized_ip_address_source` were untouched.
  `writes={attempted: true, committed: true}`, `transaction.status=committed`,
  `confirmation.status=confirmed`, zero mismatches.
- **Repeat apply**: `create: 0, update: 0, unchanged: 22, conflict: 0` — fully idempotent.
- **Rollback** (`step8_rollback_proof.py`): with the loader-level duplicate fix from Section 3,
  an ordinary document can no longer reach `_apply_import()` with an already-invalid
  precondition (every intra-batch duplicate is now caught before planning — itself a positive
  result). To still exercise `transaction.atomic()`'s rollback guarantee for a genuine
  persistence-layer failure, the second of two clean, plan-approved `DesiredNode` creates was
  forced to fail `full_clean()`. Result: `committed=false`, and **neither** row survived
  (`after_rows: []`) — the whole transaction rolled back, not just the failing row.
- **Ownership conflict** (`step8_conflict_proof.py`): pre-created the `prometheus` `DesiredService`
  under `infrastructure` with an operator-renamed `name`/`slug`. Plan correctly reported one
  `conflict` (`"name is not YAML-updatable on an existing row"`); the real `apply=true` Job run
  reported `writes={attempted: false, committed: false}`, `transaction.status=blocked`; the
  conflicting row's `name` was confirmed unchanged in the database afterward.
- **Artifact inspection**: one filename (`intent-import-result.json`), one schema
  (`nintent.intent-import.v1`) across every mode observed (preview/apply/blocked); deterministic
  object ordering; stable natural-key identities (no temporary UUIDs); no credential/secret in
  any changed field.

## 5. Analyze preview/apply/repeat/malformed proof (items 12-17)

A local deterministic HTTP fixture (`python3 -m http.server 8090`, inside the disposable
container only) served a static Backstage `catalog-info.yaml` via a `raw_url_template`-based
`IntentSource` (`ref=fixed`) — real network calls, but to a pinned local fixture, not a live
external repository, matching "a local deterministic HTTP fixture" (plan Section 6.3).

- **Preview** (`apply=false`, default): `intent-analysis-result.json` reported `DesiredService
  create=1`, `DesiredDependency create=1`, `IntentSource update=3` (status/timestamp refresh for
  all 3 enabled sources — expected every run, not a repeat-idempotence violation, since freshness
  tracking is that field's purpose). Zero writes confirmed directly via ORM query
  (`DesiredService.objects.count()` unchanged). `writes={attempted: false, committed: false}`,
  `transaction.status=not_requested`.
- **Apply**: committed; new `DesiredService`/`DesiredDependency` rows created with the exact
  analyzed fields (`lifecycle=proposed`, `catalog_kind=Component`, `catalog_lifecycle=production`,
  etc.).
- **Operator-field survival**: manually set `lifecycle=active`, `notes="operator note: keep
  this"`, `requirements={"cpu": "2"}` on the service and `resolution_status=resolved`,
  `notes="operator resolved this manually"` on the dependency. Re-ran Analyze `apply=true`
  against **identical** fetched bytes: `DesiredService unchanged=1`, `DesiredDependency
  unchanged=1` — no repeated content change — and every operator-set field above was confirmed
  unchanged afterward by direct ORM read.
- **Malformed dependency** (item 16): a second fixture catalog entity declared the same
  `dependsOn` ref twice. `plan_dependency_sync()` raised on the duplicate normalized key; the Job
  logged the exact warning (`"malformed dependencies for desired service {...}: Duplicate
  dependency key..."`) and the malformed service was never created (`DesiredService.objects.
  filter(catalog_metadata_name="malformed-service").exists()` → `False`) while the rest of that
  same run's plan/apply (the already-analyzed `fixture-service` and the 3 `IntentSource` status
  updates) proceeded normally — one bad service does not block the rest of the batch.

## 6. Isolation and cleanup (item 18)

`docker compose down -v` removed all four disposable containers, both named volumes, and the
disposable network; `docker ps -a`/`docker volume ls`/`docker network ls` filtered on
`nic-p1-disposable` confirm nothing remains. The one build artifact the disposable container's
`pip install` left in the host `nintent/` working tree (`build/`, `.pytest_cache/`, both already
gitignored) was removed. No live container, database, or media volume was touched at any point.

## Gate

Satisfied: real Jobs (not a rollback-only unit test, not the live dev database) proved preview/
apply/repeat and failure atomicity on an isolated real ORM/database for both Import and Analyze.
Three real defects surfaced by this live proof (none reachable by local unit tests) were fixed
and regression-tested; the full local suite (222 + 110) remains green. Proceeding to Step 9.
