# autotask_intent — Plan

Goal: represent recurring on-node tasks (e.g. cron-driven scripts) as ordinary
desired services, verified by content-independent existence proof only. Final
acceptance: a new braindump-born cron task is declared in desired state, its
script is placed on a live node, and `nctl drift` reports the placement
converged.

Design decisions already agreed (see `braindump/braindump1.txt`,
`braindump/braindump2.txt` and the preceding discussion):

- No new nintent model or field. A cron task is a `DesiredService` +
  `DesiredServicePlacement` with a new deployment profile `cron_task`.
- The implicit per-service check knowledge becomes an explicit, closed,
  parameterized check schema owned by the profile layer
  (`ansible_agdev/vars/deployment_profiles.yml` → nctl pydantic), NOT by
  nintent DB fields, and NOT by name-keyed registries in nodeutils.
- Existence proof only. No output-freshness check, no task-content semantics.
  Cron-registration observation is the permitted ceiling for "activity", and
  it is optional in this plan.
- Breaking-change phase: delete superseded special-casing outright; no
  compatibility shims.

## Context and key facts (verified 2026-08-07)

Where the implicit check kinds live today:

- `nctl/src/nctl_core/reconcile/profiles.py` — `ProfileReconciliation`
  (~line 129): check kind is implied by field presence (`install_path` →
  file existence, `managed_files` → digest, `bindings` → JSON slot).
  `install_path` is profile-level, so it cannot express per-instance paths.
- `nctl/src/nctl_core/observation.py` — `render_probe_hints` (~line 66)
  copies profile reconciliation data into YAML hints for nodeutils; only
  `desired_state == "active"` placements on the node are included.
- `nodeutils/service_endpoint_probes.py` (lines 17–21) — `HTTP_PROBE_SPECS`
  hard-codes HTTP paths keyed by service *name* (ollama/swarmui/comfyui).
- `nodeutils/nodeutils_collect.py` — hard-coded launchd labels (~1026–1029),
  `IMPORTANT_SERVICE_NAMES` substring matching (~65–77), per-service branches
  around 1001–1029. `normalize_observed_services` (~1317) merges all sources
  into `observed_services[name] = {state, source, endpoint, ...}`.
- `nctl/src/nctl_core/drift/service_placement.py` — gap codes
  (`service_missing`, `service_not_running`, `service_observation_missing`,
  …); `RUNNING_STATES = {"running", "active"}` (~line 12). Observe-only /
  presence-based profiles converge on presence alone.
- Per-instance values already have a home: `DesiredServicePlacement.config`
  (versioned JSON, `nintent/nautobot_intent_catalog/models.py` ~line 664).

Environment facts:

- Live reachable nodes: `agpc.local`, `agstudio.local`. `agbach.local` and
  `agdnsmasq.local` are known-down; do not use them for the demo.
- Desired-state input flow: edit `.local/desired-state.yaml`, preview with
  `uv run --project nctl nctl desired apply -f .local/desired-state.yaml`,
  submit with `--yes`. Use `nctl desired export` to learn the exact batch
  document shape before writing new entries.
- Live observation deploys the nodeutils commit **pinned by the
  superproject**, not the local worktree. Any nodeutils change must be
  committed and the superproject pin updated (push via the user) before a
  live `reconcile --refresh-observation` exercises it.
- nintent container changes require push + image rebuild — a strong reason
  this plan avoids touching nintent at all.
- Direct SSH with `~/.ssh/ansible_key` is allowed after confirming with the
  user; Ansible ad-hoc from `ansible_agdev/` (its `ansible.cfg` supplies key
  and inventory defaults) is equally fine for placing the demo script.

## Step 1 — Explicit check schema in nctl

Add a closed `checks:` list to `ProfileReconciliation`:

```yaml
deployment_profile_reconciliation:
  cron_task:
    observe_only: true
    checks:
      - kind: file_exists
        path_from_config: script_path   # resolved from placement config
```

Tasks:

- Pydantic models: one spec class per kind. Start with only the kinds that
  have a consumer in this plan: `file_exists` (path literal or
  `path_from_config`) and `http` (list of paths, to absorb Step 2's
  migration). Do not pre-build kinds nobody consumes yet.
- `render_probe_hints` resolves `path_from_config` against the placement's
  `config` at render time and emits fully-resolved hints, so nodeutils never
  needs to understand placement config. Missing/empty config key at render
  time is a validation error, not a silent skip.
- Keep the existing `install_path` / `managed_files` / `bindings` fields
  working unchanged in this step; migration happens in Step 2. (dnsmasq's
  `managed_files` digest flow stays as-is permanently — it is a working
  content-convergence contract, out of scope here.)

Acceptance: nctl ordinary suite passes; a unit test shows `cron_task`-style
checks rendering into hints with the config-resolved absolute path.

## Step 2 — Generic check execution in nodeutils; delete name-keyed specs

Tasks:

- nodeutils executes hinted checks generically: `file_exists` → stat the
  path, report an observed service with `state` present/missing and a source
  like `check:file_exists`; `http` → probe the hinted paths (reuse the
  existing probe machinery, but driven by hints instead of
  `HTTP_PROBE_SPECS`).
- Migrate `ollama`, `swarmui`, `comfyui` HTTP paths and the
  swarmui/comfyui `install_path` entries into explicit `checks` in
  `deployment_profiles.yml`. Then delete `HTTP_PROBE_SPECS` and the
  service-name keying in `service_endpoint_probes.py`.
- Discretionary: the launchd/systemd hard-codes for `node-agent` and the
  `IMPORTANT_SERVICE_NAMES` scan may be left alone or partially migrated —
  only clean them up if it falls out naturally. They are not on this plan's
  critical path.

Acceptance: nodeutils + nctl ordinary suites pass; drift output for the
observe-only trio is unchanged before vs after migration (compare
`nctl drift --json` against the scratch environment, or a fixture-level
equivalent). Superproject nodeutils pin updated and pushed (ask the user).

## Step 3 — Drift evaluation for check-based observations + `cron_task` profile

Tasks:

- Ensure `evaluate_active_placement` treats a check-observed service the
  same as today's presence sources: all checks pass → converged (profile is
  observe-only), any `file_exists` miss → `service_missing`. Map states so
  the existing gap-code vocabulary is reused; invent no new codes unless a
  distinct remediation genuinely exists.
- Add the `cron_task` profile to `deployment_profiles.yml`: profile entry
  (group, `config_schema_version: "1"`, expected config key `script_path`)
  plus the reconciliation entry from Step 1.
- One real control-loop test (README_DEV lesson 8): placement with
  `script_path` → hints rendered → simulated observation without the file →
  `service_missing` → simulated observation with the file → converged, no
  planned action (observe-only).

Acceptance: that control-loop test passes; `nctl drift` on the scratch
Nautobot with a `cron_task` placement and no script shows `service_missing`.

## Step 4 — End-to-end live demo: braindump to converged

Tasks:

1. Write `braindump/braindump3.txt` (conversational, as policy intends):
   e.g. "every 10 minutes, append a timestamp line to `~/mycron/heartbeat.log`
   on agpc". The clusterintent contract derived from it is only: script
   `~/mycron/heartbeat.sh` exists on that node.
2. Declare desired state in `.local/desired-state.yaml`: a `DesiredService`
   (e.g. `heartbeat-cron`) with one placement on the chosen live node
   (`agpc` or `agstudio`), profile `cron_task`,
   `config: {script_path: "~/mycron/heartbeat.sh"}` (decide and document
   whether `~` expansion happens at render or observation time — one owner).
   Preview, then apply with `--yes`.
3. Confirm the negative first: `nctl reconcile <NODE> --refresh-observation`
   (dry, then `--yes`) → fresh drift shows `service_missing`. Empty evidence
   is an unexercised path — this step proves the check actually ran.
4. Place the script (Ansible ad-hoc or direct SSH; a 2-line
   date-append script; registering it in crontab is nice-to-have, not
   asserted). Re-run `nctl reconcile <NODE> --refresh-observation --yes`.
5. Acceptance: final drift for the placement is converged, the operation
   evidence under `<events.log_dir>/<operation_id>/` records the observation,
   and a repeat reconcile plans nothing.

## Step 5 — Report and follow-ups

- Write `report.md` beside this plan: what was exercised, exact drift
  outputs before/after, precise completion state per README_DEV §9
  (`complete` / `partially complete` / …).
- Record deferred items explicitly so they are decisions, not omissions:
  cron-registration check kind, output-freshness (`file_fresh`) check kind,
  remaining nodeutils name-keyed scans, "coding agent implements the task
  from the braindump" (out of scope by prior agreement).
- If any part of the session was painful or a second occurrence, create a
  WorkflowEpisode (`nctl workflow-episode create`).

## Constraints (minimal) and advice

Hard constraints — keep these, drop nothing else:

- No nintent model/API changes in this plan.
- Existence proof only; no task-output semantics in drift.
- No compatibility shims for deleted registries (breaking-change phase).
- Live-node actions: confirm target with the user once per session; only
  `agpc`/`agstudio`; the demo script and `~/mycron/` are disposable.
- No secrets/tokens/private payloads in committed files or reports.

Advice (non-binding):

- Read `nctl desired export` output first; matching its canonical shape for
  the new entries avoids guessing the batch schema.
- The scratch Nautobot stack (`.local/localenv_memo.md`) is reusable —
  don't rebuild it per run; `test_nautobot` + `--keepdb` for Django tests.
- Test gates that apply here (README_DEV matrix): nctl ordinary, nodeutils
  ordinary. The Nautobot runtime gate is only needed if something
  unexpectedly touches nintent/nauto — which this plan is designed to avoid.
- When comparing pre/post-migration drift in Step 2, differences in
  `checked_at`-style volatile fields are expected; compare the semantic
  fields (state, gap codes), not raw bytes.
- If `~` expansion turns awkward, an absolute `/home/<user>/mycron/...` path
  in placement config is a perfectly acceptable simplification for the demo.
