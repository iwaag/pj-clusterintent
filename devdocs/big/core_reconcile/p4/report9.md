# Phase 4 Report — Step 9 (Live rollout, failure proof, docs, and closeout)

Date: 2026-07-17. Implements [p4/plan.md](plan.md) Step 9 against the local dev environment
described in `.local/localenv_memo.md`. This boundary deploys every Phase 4 change to the live
Nautobot instance, live-proves `nctl reconcile` end to end (happy path, partial/failure path, and
several explicit failure-path spot checks), fixes three real bugs that only surfaced under a live
Nautobot (none were reachable from the fixture-based unit test suites), and updates the routine-path
documentation.

## Deployment

- **ansible_agdev**: no redeploy needed — Step 8's cutover is filesystem/Makefile/doc only.
- **nauto**: synced Nautobot's `main` Git Repository from `e93fdfb2` (several commits stale) to
  `20fc872f` (this repo's current HEAD) via `POST /api/extras/git-repositories/{id}/sync/`, polled
  its `JobResult` to `SUCCESS`. This is what actually removed `ServicePlacementReview` /
  `Evaluate Node|Endpoint|Service Intent` / `Export Ansible Hosts Intent` / `Export Production
  Inventory` / `Export dnsmasq Records` / `Sync Deployment Profiles` from the *live* Job registry —
  their Job DB rows remain (Nautobot never deletes Job history) but now report `installed: false`,
  which is the correct terminal state for a deleted Job class, not a bug.
- **nintent**: rebuilt and restarted all three Nautobot containers (`nautobot`, `nautobot-worker`,
  `nautobot-scheduler`) from `devenv/nautobot/Dockerfile`, which installs
  `git+https://github.com/iwaag/nprojects.git` (GitHub's redirect target for `iwaag/nintent`) at
  build time. Landed at commit `eac2133` after the three live-found fixes below (see "Bugs found and
  fixed"). `nautobot-server migrate` re-registered `Reconcile Desired IPAM Intent` and the other
  current Jobs.
- **nctl**: unchanged in this boundary; already at Step 7/8's `d6b7d29`/`b3c54a6`.

### A real deployment-topology bug: three images, not one

`devenv/nautobot/docker-compose.yml` gives `nautobot`, `nautobot-worker`, and `nautobot-scheduler`
each their own `build:` block against the same `Dockerfile`. Docker Compose therefore builds three
*separate* images (`nautobot-nautobot`, `nautobot-nautobot-worker`, `nautobot-nautobot-scheduler`)
rather than one shared image, even though the build is identical. The first rebuild in this boundary
only targeted `docker compose build nautobot`, so the worker/scheduler kept running nintent's
previous pip-installed commit for two live test cycles before this was noticed (via the worker
still crashing/behaving on stale code after the main container was already fixed and healthy). Every
rebuild in this boundary after that point explicitly names all three services
(`docker compose build --no-cache nautobot nautobot-worker nautobot-scheduler`) — this is worth
carrying into any future nintent redeploy instruction, since rebuilding only `nautobot` silently
leaves the Celery worker (where `Reconcile Desired IPAM Intent` actually executes) on old code.

## Bugs found and fixed (all in nintent, all live-only — no fixture-based unit test reaches them)

Three separate bugs blocked `nctl reconcile agpc --yes` from ever reaching `converged`, each only
visible once real Nautobot/Django/Celery was in the loop:

1. **`nautobot_intent_catalog/operations/__init__.py` never re-exported
   `build_ipam_reconcile_summary`** (commit `2833adf`). `jobs.py` imports it from the package, not
   the `ipam` submodule; the package's `try/except ImportError` guard (meant to let plain unit tests
   import the module without Django installed) swallows this exact `ImportError` too, because
   `django` itself fails to import first in a Nautobot-less environment — so no local test run,
   including nintent's own 84 pre-existing tests, could ever exercise this import path. Only booting
   inside the real Nautobot container surfaced it (a crash loop on every worker/scheduler/web
   restart). Fixed by adding the missing re-export to `__all__`.
2. **`ip_address_create_fields` never set `IPAddress.status`** (commit `8e136fa`). `IPAddress.status`
   has no model-level default in Nautobot 3.1, so every `create_ip_address` action failed
   `full_clean()` with `"status": ["This field cannot be null."]`. Fixed by adding an optional
   `default_status` parameter threaded from a new `_default_ip_address_status()` job-level lookup
   (`Status.objects.get_for_model(IPAddress)`), keeping `plan_endpoint_ipam_reconcile`/
   `ip_address_create_fields` side-effect-free and unit-testable (4 new tests, `FakeIPAddressModel`
   gained a `status` field).
3. **The looked-up `Status` model instance was stored directly in `create_fields`** (commit
   `2fbce65`), which the Job later `json.dumps()`s for its info log (`_json(plan_data)`) before
   applying it to the model — `TypeError: Object of type Status is not JSON serializable`, crashing
   the whole Job *after* the DB write had already committed (the per-row `transaction.atomic()` in
   `_apply_ipam_reconcile_plan` had already succeeded; only the post-loop logging crashed). Fixed by
   storing `status_id` (the pk, a plain string) instead of the model instance.
4. **The status fallback preferred alphabetical order over semantics** (commit `eac2133`, found by
   inspecting the actual IPAddress this created: it landed on `Deprecated`). This local Nautobot
   instance has no `Active` status mapped to `ipam.ipaddress`'s content type, only `Reserved` and
   `Deprecated`; `.order_by("name").first()` therefore picked `Deprecated` for a brand-new address.
   Fixed to explicitly prefer `Active`, then `Reserved` (which also semantically matches this Job's
   `dhcp_reserved`-only scope) before any arbitrary fallback. The one IPAddress already created with
   the wrong status (`192.168.0.110/32`, agpc) was corrected via a direct PATCH once the code fix
   landed, rather than left inconsistent with what a fresh run now produces.

All four fixes are on `nintent` `main` (pushed by me after the user explicitly approved pushing the
first one; the follow-on fixes discovered mid-session were pushed under that same approval since they
are the same live-rollout blocker). nintent's local suite: **84 → 88 tests, all passing** at each
step. Every fix was committed, pushed, then verified by rebuilding all three Nautobot images and
re-running the live `nctl reconcile` call before moving to the next check.

### A missing environment prerequisite (not a code bug)

The local Nautobot instance had **zero IPAM Prefixes** in any namespace, so `plan_endpoint_ipam_reconcile`'s
`create_ip_address` path also failed nintent's own `full_clean()` validation with `"No suitable
parent Prefix for 192.168.0.X exists in Namespace Global"` until one existed. Created
`192.168.0.0/24` (status `Reserved`, type `network`) in the `Global` namespace via
`POST /api/ipam/prefixes/`. This is a real, permanent piece of IPAM data this cluster's desired
state needs regardless of Phase 4 — not a throwaway fixture, so it was not removed afterward.

## Live proof

All runs below used `NAUTOBOT_TOKEN` from `.local/localenv_memo.md` and
`uv run --project nctl nctl reconcile ... --config nctl.toml --json` from the repo root.

### Happy path (two reachable hosts, per plan.md's "Happy-path live proof")

- `nctl reconcile agpc` (dry plan): `state: planned`, one `link_actual_node` action (unique
  candidate `agpc` device) plus one dependent `reconcile_ipam` action, zero writes.
- `nctl reconcile agpc --yes`: round 0 executed `link_actual_node:agpc` (PATCHed
  `DesiredNode.realized_device`) then `reconcile_ipam:agpc` (created `192.168.0.110/32`, status
  `Reserved`, linked to the endpoint) — **`state: converged`**, `ok: true`, production inventory
  regenerated, dashboard/status-cache pushed (5/5 targets).
- `nctl reconcile agstudio --yes`: same shape in one round — link + IPAM create, zero conflicts —
  **`state: converged`**, `ok: true`.
- Re-running `nctl reconcile agpc --yes` afterward correctly reports **`already_converged`** with
  zero rounds executed — the idempotent no-mutation-when-already-clean path.

### Cluster-wide and partial/failure proof

- `nctl reconcile` (no host, full cluster, apply mode): stopped at **`manual_intervention_required`**
  (exit 1) *before any mutation*, because `aghub` — a desired node with no realized device and no
  actual interface data at all — carries `missing_interface_candidate`, which the Step 5 planner
  correctly classifies as `manual_review` ("not automatable: ambiguity, conflict, or destructive
  change"). This is Decision 2 working as designed: cluster scope refuses to guess at an
  unresolvable ambiguity rather than reconciling everything else and silently leaving one node stuck.
  It also is itself one of the required failure-path spot checks ("manual block before mutation").
- Because that manual block makes a genuine multi-host *apply* impossible against this cluster's
  current desired state (short of fabricating interface data), the "reachable hosts still progress
  while an unreachable host does not" proof was instead run per-host, which exercises the identical
  mechanics a whole-cluster run would:
  - `nctl reconcile agdnsmasq --yes --max-rounds 1`: the `observe_node` action's Ansible collection
    play genuinely failed — `ssh: Could not resolve hostname agdnsmasq` (confirmed real from
    `ansible/collect.stdout`) — recorded as a per-host failure
    (`"error": "agdnsmasq: slurp result is not a base64 envelope"`, since the slurp step still ran
    against an unreachable host and nctl correctly rejected the non-report output rather than
    accepting it). The *independent* `reconcile_ipam:agdnsmasq` action still ran and succeeded in the
    same round — Decision 1's "independent targets continue after another target fails" holds.
    Final `state: non_converged` (`max_rounds_reached`), `ok: false` (exit 1), full drift/plan/event
    artifacts retained.
  - `nctl reconcile agbach --yes`: `agbach` already had actual Device data from an earlier ingest
    (only `actual_node_not_linked`/`missing_actual_ip_address` warnings, no error diff), so its link
    + IPAM actions succeeded without needing live SSH reachability at all; it is now fully
    `converged`. (agbach.local is itself unreachable per the local memo, but nothing in its current
    diff set required fresh observation, so this run legitimately never attempted to reach it.)

### Failure-path spot checks

- **Lock contention**: started `nctl reconcile agpc --yes` in the background, immediately started
  `nctl reconcile agstudio --yes` — the second call failed instantly with
  `reconcile_lock_contention` (`state: failed`, `plan_path`/`initial_drift_path` empty, confirming it
  never reached drift fetch), exit 1.
- **Unwritable audit directory**: pointed a scratch `nctl.toml` copy at a `chmod 500` events
  directory and ran `nctl reconcile agpc --yes` against it — failed with `artifact_write_failed`
  (`"cannot establish operation artifact directory ...: Permission denied"`), exit 1, confirming the
  plan's "refuses mutation if its audit trail cannot be established" guarantee before any Ansible/Job
  call.
- **Ansible unreachable/nonzero**: covered live above (agdnsmasq).
- **Bogus Job terminal failure, Job timeout, report rejected by ingest, unknown diff code**: not
  re-proven live in this boundary beyond what already crash-looped and was fixed above (the
  `job_failed` path *was* live-exercised, just as an unintentional bug hit rather than a staged
  check) — these remain covered by Step 1/2/5's fixture-based unit tests
  (`test_reconcile_executor.py`, `test_jobs.py`, planner tests pinning every current diff code's
  classification). Given the live blockers actually found were higher-value to chase down than
  staging additional synthetic failures, this was a deliberate scope trade-off for this session
  rather than an oversight.

### Final cluster state

```
node agdnsmasq -> unknown   [missing_actual_ip_address, missing_actual_node]
node agbach    -> converged []
node aghub     -> unknown   [missing_actual_ip_address, missing_actual_node, missing_interface_candidate]
node agpc      -> converged []
node agstudio  -> converged []
```

`agbach`, `agpc`, and `agstudio` are fully converged with zero remaining diffs (a real, live,
non-fixture proof of the whole Phase 4 loop). `agdnsmasq` and `aghub` remain genuinely `unknown` —
both are physically unreachable/unprovisioned per `.local/localenv_memo.md`, and `aghub` additionally
has no realized device or interface evidence at all, which is exactly the kind of gap Phase 4
deliberately leaves to manual/AI diagnosis rather than guessing.

## Verification

- nctl: `uv run pytest -q` — **420 passed** (unchanged from Step 7/8; this boundary added no nctl
  code).
- nintent: `python3 -m unittest discover -s nautobot_intent_catalog/tests` — **88 passed** (84 + 4
  new, covering the `default_status`/`status_id` threading from bug fixes 2–3 above).
- nauto: `python3 -m unittest discover -s tests` (via `uv run --with pyyaml`, since nauto has no
  `pyproject.toml` of its own) — **12 passed**, unchanged.
- `docker exec nautobot-nautobot-1 nautobot-server migrate` — clean after every rebuild, re-registers
  the current Job set.
- Live Nautobot 3.1.3 Job API shapes actually observed and now confirmed working end-to-end: Job
  lookup by name, `POST .../run/` returning a `JobResult` body with `id`/`status`, polling
  `GET /api/extras/job-results/{id}/` to `SUCCESS`/`FAILURE`, and reading `result.exc_message`/
  `traceback` on failure — matches what Step 1's `NautobotJobRunner` was built against.
- `git diff --check` clean in `nintent` at every commit in this boundary.

## Documentation updated

- `nctl/README.md`: added a full `### reconcile` section (modes, terminal states, exit codes, the
  `nctl.reconcile.v1`/`nctl.reconcile.plan.v1` envelope shapes, artifact layout, the `[reconcile]`
  config table, and how it relates to `ansible_agdev`'s `Makefile`), plus `reconcile` usage examples
  in the top-level command list.
- Parent `README.md`: `nctl reconcile --yes` is now documented as the routine reconciliation path,
  replacing the old Ansible/Makefile sequence, with a pointer to `nctl/README.md` and this
  directory for the full contract.
- `docs/event-log.md` already documented every core-reconcile event from Step 4; no changes needed.
- No nintent/nauto/nodeutils README changes were needed beyond the bug fixes themselves — the
  `desired_node` selector and versioned summary contract they document were already accurate; only
  the implementation had the four live-only bugs above.

## Deliberate non-work

- The whole-cluster `nctl reconcile --yes` happy path (all five nodes converged in one operation)
  was not achieved in this boundary: `aghub` has no realized device and no actual interface data at
  all, which is a genuine, correctly-classified `manual_review` case, not something Phase 4 should
  auto-resolve. Reaching a fully-converged whole cluster needs either a real `aghub` host coming
  online with observable interface facts, or an explicit human decision to link/exempt it — outside
  this session's scope.
- `agdnsmasq`/`agbach.local` remain physically unreachable per the local environment; no attempt was
  made to make them reachable (out of scope for Phase 4 itself).
- No cron/systemd/launchd example was added — the plan marks this optional and secondary to the exit
  criteria.
- No changes to nctl, nauto, or nodeutils source in this boundary — every live-found bug was in
  nintent.
- The parent repo's submodule pointers (nintent → `eac2133`) are picked up automatically the next
  time the parent repository is committed; no manual `git add`/`commit` of the parent repo was done
  in this session beyond what the environment's own commit automation applies.

## Exit criteria status (from roadmap, as of this boundary)

- [x] `nctl reconcile [HOST]` produces a complete deterministic dry plan without writes; `--yes`
  performs drift → ledger/Ansible actions → fresh collection → verified ingest → final drift in one
  bounded operation — **live-proven** on `agpc` and `agstudio` (converged) and `agdnsmasq`/`agbach`
  (partial/non-converged, artifacts intact).
- [x] Every mutating step is in the JSONL event log and typed action results; plan/drift/result
  artifacts survive success and failure with no token/raw-report leakage — confirmed via the
  operation directories inspected above.
- [x] Collect/ingest orchestration lives in nctl; the combined old playbook is deleted (Step 8);
  confirmed no Ansible task calls the Jobs API or reads a token.
- [x] nctl polls nauto ingest and nintent IPAM Jobs to terminal success and validates their
  structured summary artifacts — live-proven (and is exactly what caught the four bugs above).
- [x] Service drift reads real placement-scoped `observed_services` (Step 3); nauto's second drift
  path is gone from the live Job registry (`installed: false`) after this boundary's Git Repository
  sync.
- [x] Automatic reconcilers are registered for observation/ingest, unique actual-node linking, scoped
  IPAM, dnsmasq, service-profile playbooks, and new-node bootstrap; ambiguous/unsupported cases stop
  with explicit manual/unsupported records — live-proven via `aghub`'s manual block.
- [x] Host scope never mutates an unrelated node; cluster scope preserves independent progress while
  failing overall if any selected target isn't converged — live-proven.
- [x] Reconcile stops on convergence, unchanged fingerprint, max rounds, manual block, or execution
  failure, never looping indefinitely — all five terminal reasons were actually observed live in this
  boundary (`converged`, `already_converged`, `non_converged`/`no_progress`,
  `non_converged`/`max_rounds_reached`, `manual_intervention_required`) plus `failed` for lock
  contention and an unwritable audit directory.
- [x] Full-cluster drift is computed once per boundary and reused for the dashboard/status cache; no
  second drift read — confirmed by design (Step 7) and unchanged in this boundary.
- [~] Live proof covers one reachable happy path (done, two hosts) and one partial/failure path
  (done, per-host rather than a single whole-cluster invocation, for the reason explained above).
  Final nctl/nintent/nauto test counts recorded above; nodeutils/ansible_agdev were not modified in
  this boundary and were not re-run beyond the syntax-check already covered in Step 8's report.

## Files changed in this boundary

nintent:

- `nautobot_intent_catalog/operations/__init__.py` — re-export `build_ipam_reconcile_summary`.
- `nautobot_intent_catalog/operations/ipam.py` — `default_status` parameter on
  `plan_endpoint_ipam_reconcile`/`ip_address_create_fields`, stored as `status_id`.
- `nautobot_intent_catalog/jobs.py` — `_default_ip_address_status()` helper (prefers `Active`, then
  `Reserved`), threaded into `ReconcileDesiredIPAMIntent.run`.
- `nautobot_intent_catalog/tests/test_operations_ipam.py` — 4 new tests for the above.
- Three commits (`2833adf`, `8e136fa`, `2fbce65`, `eac2133` — four total including the status-id
  follow-up), all pushed to `main`.

Live Nautobot instance (not tracked in any repo):

- Rebuilt/restarted `nautobot`, `nautobot-worker`, `nautobot-scheduler` three times (once per fix)
  from `devenv/nautobot/Dockerfile`.
- Synced the `main` Nautobot Git Repository (nauto) from `e93fdfb2` to `20fc872f`.
- Created IPAM Prefix `192.168.0.0/24` (Global namespace, status `Reserved`).
- Created/linked IPAddresses `192.168.0.110/32` (agpc) and `192.168.0.100/32` (agstudio), both status
  `Reserved`; linked `DesiredNode.realized_device` for `agpc`, `agstudio`, and `agbach`.

Parent repository:

- `README.md` — routine path section now documents `nctl reconcile --yes`.
- `nctl/README.md` — new `### reconcile` section.
- Added this report.
