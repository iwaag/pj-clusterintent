# Phase 0 Step 0.7 — Define Phase 1 transition, tests, and rollout

Parent: [plan.md](plan.md), Step 0.7.

## Check performed

1. **Baseline change requirement.** Confirmed Phase 0 makes no runtime change: only
   `devdocs/big/braindump/p0/report0.1.md`–`report0.6.md` have been added/committed so far, no file
   under `nintent/` or `nctl/` was touched. The last documented live baseline (nintent 98 tests,
   nctl 617 tests, `devdocs/big/better_usability/p4/report4.8.md`) is therefore necessarily
   unchanged by this phase; per the plan's own Verification section 8, "No runtime tests or live
   writes are required because Phase 0 changes documentation only," so re-running the full suite
   was not attempted as part of this step. (A local `python3 -m unittest discover -s
   nautobot_intent_catalog/tests` was tried directly from a shell without nintent's project virtual
   environment and failed on `ModuleNotFoundError: No module named 'yaml'`; this is an environment
   setup issue, not a code regression, and is not evidence against the Phase 4 baseline since no
   nintent code changed.)

2. **REST API surface note (pre-existing, unrelated to Braindump).** `nintent/README_DEV.md:101`
   states "`DesiredNode` and `DesiredEndpoint` are the only two models with a REST API today", but
   Step 0.2 of this phase already confirmed `api/views.py`/`api/urls.py` register **three**
   viewsets/routes (`nodes`, `services`, `endpoints`) — `DesiredService` also has a REST API. This
   is a stale line in nintent's own dev doc from before the `services` route was added; it does not
   affect this plan (`plan.md`'s "Current state" section correctly says "nodes, services, and
   endpoints") and is out of Phase 0's scope to fix (Phase 0 only edits `devdocs/big/braindump/`).
   Recorded here so Phase 1 doesn't inherit the stale claim if it consults `README_DEV.md` for the
   three-file serializer/viewset/router pattern to follow.

3. **Transition rule check.** Confirmed against Step 0.2's migration inventory: nintent's last
   migration is `0013_analysis_provenance_and_generic_endpoint_policy.py`, so Phase 1's "one Django
   migration for both models" would be `0014_*`, additive only — consistent with "no transitional
   models, temporary JSON blobs, dual endpoints, or import compatibility."

4. **Test-plan completeness check.** Compared the plan's ten required Phase 1 test items against
   the existing test-module-per-concern layout confirmed in Step 0.2
   (`test_analysis.py`, `test_importers.py`, `test_loaders.py`, `test_names.py`,
   `test_operations_hosts.py`, `test_operations_ipam.py`, `test_templates.py`) — none of the ten
   required items (model fields/choices, whitespace validation, explicit API authorship, zero-or-one
   review, REST CRUD, GraphQL retrieval, cascade deletion, escaped-template rendering, multiple
   independent documents, no side-effect proof) overlaps an existing test file's concern, confirming
   a new `test_braindump.py` (or similar) is the correct, non-duplicating home for Phase 1.

5. **Rollout step check.** Confirmed against `.local/localenv_memo.md` and the existing coordinated
   rollout pattern (`report4.8.md`): commit → user push (never automated) → DB backup → image
   rebuild with `--no-cache` (per [[nintent-rebuild-cache-gotcha]], `docker compose build` can
   silently cache a stale nintent commit) → restart/migration → REST/GraphQL smoke checks → system
   check. The plan's Step 0.7 rollout list already names every one of these steps; no addition
   needed.

## Result

The plan's Step 0.7 transition/test/rollout obligations are confirmed complete and consistent with
current nintent/nctl state. One pre-existing, unrelated doc inaccuracy was found in
`nintent/README_DEV.md` (stale 2-model REST claim) and recorded as a Phase 1 heads-up; it does not
block Phase 0 and requires no edit to `plan.md`.
