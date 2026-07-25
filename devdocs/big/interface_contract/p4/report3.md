# Phase 4 Step 3 Report — Freeze commits and build a reproducible candidate

Plan: [plan.md](plan.md), Step 3.

Status: **implemented, not fully closed**. Items 1-3 and 5-12 are complete and disposable-proven.
Item 4 (push) surfaced a genuine defect mid-step that produced one more required commit
(`e8732f1`); that commit is not yet pushed, so the *fully final* pinned candidate has not been
rebuilt against it. No live mutation, no live service stop/restart/rebuild, no live database/media
action. Everything below is disposable-only, as authorized without a live-maintenance approval by
Section 3.4.

## 1. Remote-SHA check at step start (plan items 4-5)

Before doing any work, `git fetch origin` in `nintent` and `nctl` showed `HEAD == origin/main` for
both:

- nintent `179a12ac48b00f33512acc739c9a9ec01a3c6854` (Step 1 + Step 2's repair commits)
- nctl `79b6d6b3e8025722ae1a408daacbf706e845e11d` (Step 1's boundary-test commit)

The superproject's submodule pointers (set by the Step 1/Step 2 commits) already matched these
SHAs. So the plan's "ask the user to push" gate for the *pre-existing* Step 1/2 commits was already
satisfied — the user had pushed them between sessions. This step's own new commit (Section 3 below)
is a separate, later gate.

## 2. Pin the Dockerfile to the exact frozen tuple (plan items 6-8)

[`devenv/nautobot/Dockerfile`](../../../../devenv/nautobot/Dockerfile) changed from installing
mutable `git+https://github.com/iwaag/nprojects.git` (no ref) to:

- `ARG NINTENT_COMMIT=179a12ac48b00f33512acc739c9a9ec01a3c6854` / `ARG
  NAUTO_COMMIT=2635e648469d6e6bad87af113f7427b878b0a387` (the plan's Section 5.1 frozen tuple);
- `pip install ... "git+https://github.com/iwaag/nintent.git@${NINTENT_COMMIT}"` — an exact commit,
  not a branch;
- a build-time check that `importlib.metadata`'s `direct_url.json` `vcs_info.commit_id` equals
  `NINTENT_COMMIT` exactly, failing the build otherwise (pip resolving a moved/retagged ref to a
  different commit would be caught, not silently accepted);
- `COPY nauto/seed/intent_sources.yaml /opt/nautobot/intent_sources.yaml` — the exact nauto
  commit's canonical YAML baked in read-only at one explicit path, plus a build-time
  `sha256sum` recorded at `/opt/nautobot/intent_sources.yaml.sha256`; and
- `LABEL`s and `/opt/nautobot/build_info.json` exposing both embedded commit SHAs.

Because the YAML now needs to reach the nauto submodule checkout, [`docker-compose.yml`](../../../../devenv/nautobot/docker-compose.yml)'s three services changed `build.context` from `.` to `../..`
(the superproject root) with `dockerfile: devenv/nautobot/Dockerfile`. Added a root
[`.dockerignore`](../../../../.dockerignore) excluding `.git`, `.local` (secrets), `devdocs`, and
caches from the now-larger build context.

[`nautobot_config.py`](../../../../devenv/nautobot/nautobot_config.py) sets
`PLUGINS_CONFIG = {"nautobot_intent_catalog": {"intent_sources_file":
"/opt/nautobot/intent_sources.yaml"}}` (previously empty) — the same file is bind-mounted
identically into web, worker, and scheduler, so all three resolve the same explicit path per plan
Section 3.3. No runtime existence check was added beyond the build-time `COPY`/checksum step: the
YAML is baked into the immutable image rather than a volume, so it cannot go missing at container
start without the image itself being different — a build-time guarantee, not a runtime one, but
sufficient given the read-only/immutable delivery mechanism.

## 3. A real test-portability defect found and fixed while building the candidate (not in plan Section 2's audit)

`nautobot-server test nautobot_intent_catalog` inside the first disposable candidate (pinned to
`179a12a`, built from `git+https://github.com/iwaag/nintent.git@179a12a...`, the actual production
install method) failed one test that had passed in every previous run:

```
FAIL: test_canonical_checked_in_file_matches_exact_confirmed_counts
  Lists differ: ['Intent source file not found: /opt/nautobot/.local/lib/python3.12/nauto/seed/intent_sources.yaml'] != []
```

`CanonicalFileIdentityCountTests._CANONICAL_PATH` (added in Phase 1 Step 8) computed the checked-in
YAML's path as `Path(__file__).resolve().parents[3] / "nauto" / "seed" / "intent_sources.yaml"` —
correct only when `__file__` is the source tree's `nintent/nautobot_intent_catalog/tests/` (four
parents up lands on the superproject root, which has a `nauto/` sibling). A real `pip install
git+https://...` places the installed file under
`.../site-packages/nautobot_intent_catalog/tests/`, where four parents up is nowhere near a `nauto/`
checkout. Every prior disposable run (Step 2's `nic-p4-disposable`, and the Step 0 planning-time
audit) bind-mounted and locally `pip install`ed the nintent *directory* rather than installing from
a real Git URL, which is why this path-depth mismatch was never exercised until this step's
Dockerfile started doing the real thing.

Fixed in `nintent/nautobot_intent_catalog/tests/test_loaders.py`
(`_first_existing_canonical_intent_sources_path()`): resolve the canonical path in priority order —
`NAUTOBOT_INTENT_SOURCES_FILE` env var, then Django's
`settings.PLUGINS_CONFIG["nautobot_intent_catalog"]["intent_sources_file"]` (wrapped so the
Django-free local suite, which never calls `django.setup()`, falls through instead of raising
`ImproperlyConfigured`), then the original parents-based local-checkout fallback; skip the test only
if none of the three exist. This is a test-only change; no production code path changed. Committed
as nintent `e8732f1` ("interface_contract p4 step3: fix canonical-YAML test path assumption for
real pip installs").

Verified both ways:
- **Local Django-free suite** (`python3 -m unittest discover -s nautobot_intent_catalog/tests` from
  the checked-out `nintent/`): 226 passed, 13 skipped — unchanged from every prior step.
- **Disposable candidate, hot-patched**: `docker cp`'d the fixed file over the already-running
  `179a12a`-pinned candidate's installed copy and reran; the single test now resolves via the
  `PLUGINS_CONFIG` branch (proving the new `/opt/nautobot/intent_sources.yaml` path from Section 2
  is exactly what makes this portable) and the full `nautobot-server test nautobot_intent_catalog`
  suite passed **304/304**, 0 failures, 0 errors (log:
  `.local/interface-contract/p4/20260726_step3/app_suite_pass.log`; the pre-fix failing run is
  `app_suite.log`).

**This fix is not yet in the built candidate image.** `nic-p4-candidate:20260726` is still built
`FROM` nintent `179a12a` (the tuple that was actually pushed and resolvable via `git+https://...` at
step start); `e8732f1` exists only as a local commit plus the in-container hot-patch proof above.
Per plan Section 3.4, "pushing repaired commits is owned by the user," and per Section 9.1, "the
implementation must stop before the candidate build if the required remote SHAs are unavailable."
The superproject's `nintent` submodule pointer was bumped locally to `e8732f1` (matching the
Step 1/Step 2 pattern of committing the pointer bump before push), but **`e8732f1` needs to be
pushed to `github.com/iwaag/nintent` before a final candidate can be rebuilt and re-verified against
it** — that rebuild is a small remainder of Step 3, not a new step, and is otherwise identical to
the verification already performed below.

## 4. Candidate build (plan items 9-10)

```
docker build -f devenv/nautobot/Dockerfile -t nic-p4-candidate:20260726 .
```

from the superproject root. Build succeeded in ~3s (base layer cached); the commit-equality check
(Section 2) and the `COPY`/checksum step both passed inline during the build.

- Image ID: `sha256:d77790eefd59150a44e75a68dfed1b56a5544d3932da4300bbbeaf8b838f9e0c`
- `/opt/nautobot/build_info.json`: `{"nintent_commit":
  "179a12ac48b00f33512acc739c9a9ec01a3c6854", "nauto_commit":
  "2635e648469d6e6bad87af113f7427b878b0a387"}`
- `/opt/nautobot/intent_sources.yaml.sha256`:
  `598391e02041c433df468629cc86d2a2c948c94b80f89a1746a28057b557455b` — identical to
  `sha256sum nauto/seed/intent_sources.yaml` on the checked-out `nauto` submodule.

Full App suite (`nautobot-server test nautobot_intent_catalog`) and `makemigrations
nautobot_intent_catalog --check --dry-run` ("No changes detected") both ran successfully inside a
disposable container from this image — see Section 5.

## 5. Disposable web/worker/scheduler triplet (plan item 11)

New compose project `nic-p4-step3` at
`.local/interface-contract/p4/20260726_step3/docker-compose.yml`: fresh Postgres/Redis, then
`nautobot` (port `18001`, distinct from live's `8000` and Step 2's `18000`), `nautobot-worker`, and
`nautobot-scheduler` — all three running `nic-p4-candidate:20260726`, none built via `docker compose
build` (so the live compose project was never touched), and all three bind-mounting the *real*
`devenv/nautobot/nautobot_config.py` (not a copy) to prove the actual deployment config file, not a
stand-in, resolves correctly in every service.

- `nautobot-server check --deploy` (run automatically by the base image's entrypoint before
  `runserver`): passed with only the same 5 expected `security.W00x` warnings Step 2 saw.
- `showmigrations nautobot_intent_catalog`: ends at `0016_remove_reconciliation_dashboard_surfaces`
  in all three, matching live.
- `settings.PLUGINS_CONFIG` inside the running `nautobot` service resolved to
  `{'nautobot_intent_catalog': {'intent_sources_file': '/opt/nautobot/intent_sources.yaml'}}`.
- All three services (`nautobot`, `nautobot-worker`, `nautobot-scheduler`) independently reported:
  - the same `build_info.json` (`nintent_commit`/`nauto_commit` above);
  - the same `intent_sources.yaml` SHA-256;
  - the same installed `direct_url.json` `vcs_info.commit_id` (`179a12a...`); and
  - the same Docker image ID via `docker inspect ... --format '{{.Image}}'`.

Full evidence: `.local/interface-contract/p4/20260726_step3/verification_summary.txt`.

## 6. Job discovery (plan item 12)

**nintent — exactly 3 Jobs**, all `installed=True`, matching the roadmap's final Job contract:

```
Analyze Intent Sources        | nautobot_intent_catalog.jobs | AnalyzeIntentSources
Import Intent Sources         | nautobot_intent_catalog.jobs | ImportIntentSources
Reconcile Desired IPAM Intent | nautobot_intent_catalog.jobs | ReconcileDesiredIPAMIntent
```

(`Preview Intent Source Analysis`, `Evaluate Endpoint/Node/Service Intent`, `Export Ansible Hosts
Intent`, `Export Production Inventory`, `Export dnsmasq Records`, `Sync Deployment Profiles` — all
present in the pre-Phase-1 baseline captured in Step 0 — are absent, confirming the Phase 1-3
deletions carried through to a real pip-installed package, not just the source tree.)

**nauto — final Job set.** A `GitRepository` (`nauto_step3`, `remote_url=
https://github.com/iwaag/nauto`, `branch=main`) was synced against the real, already-pushed nauto
remote (read-only clone, no live Nautobot involved). `current_head` after sync:
`2635e648469d6e6bad87af113f7427b878b0a387` — the exact pinned nauto commit. Discovered nauto Jobs:

```
AI Resource Review        | nauto_step3.jobs.ai_resource_review
Ingest Nodeutils Inventory | nauto_step3.jobs.ingest_nodeutils_inventory
Seed Home Cluster         | nauto_step3.jobs.seed_home_cluster
```

`Generate Desired Services` (deleted in Phase 1) is absent, confirming no duplicate desired-state
writer/generator ships in the pinned nauto tuple.

## 7. Evidence retention and teardown

Evidence at `.local/interface-contract/p4/20260726_step3/` (directory mode `0700`, files `0600`):
`docker-compose.yml`, `app_suite.log` (pre-fix failing run), `app_suite_pass.log` (post-fix passing
run), `verification_summary.txt` (image ID, build_info/YAML-digest/installed-commit per service,
migrations, Job lists, GitRepository sync result), `setup_nauto_repo.py`. No token, credential, or
private prose present (checked by grep before setting permissions).

`docker compose -p nic-p4-step3 down -v` removed all 5 containers, both volumes, and the network;
confirmed absent by name in `docker ps -a`/`docker volume ls`/`docker network ls`. The three live
`nautobot-*` containers (`nautobot-nautobot-1`, `nautobot-nautobot-worker-1`,
`nautobot-nautobot-scheduler-1`) were running, untouched, before and after this entire step. The
built `nic-p4-candidate:20260726` image was left in the local Docker image store (a build artifact,
not a running service — not required to be removed by Section 3.4).

## What Step 3 does not close

- **`e8732f1` is not pushed.** The candidate image, and everything verified against it above, is
  pinned to `179a12a`/`2635e64` — the tuple that was actually resolvable via `git+https://...` at
  step start. `e8732f1`'s fix was proven correct only via a hot-patch inside that same running
  container (Section 3), not via a rebuild-from-git. **Requesting: please push nintent's `main`
  branch (now at `e8732f1`) to `github.com/iwaag/nintent` so the candidate can be rebuilt and
  re-verified against the exact pushed tuple** — a short remainder of this step, not a new one.
- The superproject's `nintent` submodule pointer was bumped locally to `e8732f1` but not yet
  committed at the superproject level pending confirmation the rebuild-and-reverify remainder above
  succeeds (committing the report and Dockerfile/compose/config changes now; the submodule pointer
  bump will be included in the same commit since `git add` picks up the current submodule SHA, but
  the *candidate image* itself does not yet reflect it — flagging this explicitly rather than
  overclaiming).
- No live database dump, media archive, or maintenance-window work was attempted — Step 4's job, not
  this one's.

## Verification

- `docker build -f devenv/nautobot/Dockerfile -t nic-p4-candidate:20260726 .`: succeeded; commit
  and checksum checks passed inline.
- `nautobot-server check --deploy` (disposable, all 3 services' shared entrypoint): clean, 0 errors.
- `nautobot-server test nautobot_intent_catalog` (disposable): 304/304 pass after the hot-patch
  (304 total both before and after; before-fix run had 1 failure).
- `nautobot-server makemigrations nautobot_intent_catalog --check --dry-run`: "No changes detected."
- `python3 -m unittest discover -s nautobot_intent_catalog/tests` (local, fixed source): 226
  passed, 13 skipped — unchanged.
- Image ID / `nintent_commit` / `nauto_commit` / YAML SHA-256 identical across `nautobot`,
  `nautobot-worker`, `nautobot-scheduler`.
- nintent Job discovery: exactly 3 Jobs, all installed. nauto Job discovery via real GitHub sync:
  `current_head` matches the pinned commit exactly; 3 Jobs, `Generate Desired Services` absent.
- `git -C nintent diff --check`: clean.
- Disposable teardown: containers/volumes/network confirmed removed; live stack confirmed
  untouched throughout (`docker ps` before/after identical for `nautobot-*`).

Next: push nintent `e8732f1`, rebuild+re-verify the candidate against it (small remainder of this
step), then Step 4 (approve maintenance, freeze writers, verify backups) — a live-adjacent step
requiring explicit operator approval per plan Section 3.4.
