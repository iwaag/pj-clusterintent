# autotask_intent — Final Report

Status: **complete** — all five plan steps exercised their stated acceptance
criteria; the final acceptance (a braindump-born cron task declared as
desired state, its script placed on a live node, and `nctl drift` reporting
the placement converged with no repeat action) was demonstrated live on
agstudio. Per-step details: `report1.md` … `report4.md`.

## What exists now

- **Explicit, closed, parameterized check schema** owned by the profile
  layer (`ansible_agdev/vars/deployment_profiles.yml` →
  `nctl_core.reconcile.profiles`): `checks:` on observe-only reconciliation
  entries, kinds `file_exists` (literal `path` or `path_from_config`) and
  `http` (rooted path list). Discriminated pydantic union; unknown kinds
  rejected at load time. (Step 1)
- **One-owner resolution**: `render_probe_hints` resolves
  `path_from_config` against the placement's own `config` at render time;
  nodeutils only ever sees final paths. Missing/empty/relative config
  values raise `CheckResolutionError` — never a silent skip. `~` expands at
  observation time on the target (nodeutils, login user). (Steps 1, 3)
- **Generic check execution in nodeutils**: `HTTP_PROBE_SPECS`,
  `probe_service_endpoint`'s name keying, and the `install_path` hint are
  deleted (no shims); checks execute by kind and record their results under
  the observed entry's `checks` list. A missing file is recorded evidence
  (`state: missing`, `source: check:file_exists`), not a silent no-entry.
  (Step 2)
- **Drift evaluation** reuses the existing gap vocabulary: failed existence
  proof → `service_missing` (even for manual placements, even beside richer
  running-state evidence); all checks passed (`state: present`) →
  convergence for the observe-only profiles that emit it. No new gap codes.
  (Step 3)
- **`cron_task` deployment profile**: observe-only, required `script_path`
  config key, one `file_exists` check via `path_from_config`. A recurring
  on-node task is now an ordinary `DesiredService` + placement — no nintent
  model or field was touched anywhere in this plan. (Step 3)
- **Live proof** (Step 4, agstudio, nodeutils pin
  `efb790f07a6e83176b24add6888c1cc1fdd48d2b`): negative round observed the
  check running and failing (`service_missing`), planner invented no action
  (observe_only stays `unsupported`); after placing the 2-line script the
  next `nctl reconcile agstudio --refresh-observation --yes` ended
  `converged`; a repeat dry reconcile planned `actions: []`. The migrated
  `ollama` http check also ran live from hints (200 → `active`).

## Exact drift outputs (semantic fields)

- Before placement (op `01KZC3R7GYBH3CP0CY5QB6WJSF`, fresh observation):
  `heartbeat-cron` → `status: drifting`, gap `service_missing`, observed
  entry `{state: missing, source: check:file_exists, checks: [{kind:
  file_exists, path: /Users/eiji/mycron/heartbeat.sh, status: missing}]}`.
- After placement (op `01KZC3TR5PGANVD4MZCW4SQRDG`): `heartbeat-cron` →
  `converged`, no diffs, observed entry identical but `status: present` /
  `state: present`.
- Step 2 pre/post-migration comparison: full-cluster `nctl drift --json`
  identical except volatile timestamps (report2).

## Test gates run (README_DEV matrix)

- nctl ordinary: 1275 passed (grew 1264 → 1275 across Steps 1–3).
- nodeutils ordinary: 84 passed.
- Nautobot runtime / nintent / nauto gates: not required — no nintent, nauto,
  or App change was made (by design of this plan).

## Deferred items (decisions, not omissions)

1. **Cron-registration check kind** (e.g. `cron_registered`): permitted
   ceiling for "activity" observation, deliberately not built — no consumer
   yet. Add only when a placement actually needs it (build-on-consumer rule
   from Step 1).
2. **Output-freshness check kind** (`file_fresh`): out of scope by design
   decision; existence proof is the contract.
3. **Crontab registration of the demo script**: plan-declared nice-to-have;
   not done, not asserted. The demo's converged claim covers script
   existence only.
4. **Remaining nodeutils name-keyed scans**: launchd/systemd hard-codes for
   `node-agent`, `IMPORTANT_SERVICE_NAMES` substring scan, blender/docker
   host-tool probes — left alone per plan's discretionary clause; candidates
   for future migration into `checks` when their profiles need parameters.
5. **"Coding agent implements the task from the braindump"**: out of scope
   by prior agreement (braindump2).
6. **Defect to fix — `nctl desired export` → batch create round-trip**:
   export emits identity fields in both `key:` and `values:`; the create
   path 409s (`TypeError: multiple values for keyword argument`). Bites
   exactly the documented recovery scenario (re-applying an export to a DB
   missing rows). Found and worked around in Step 3.
7. **Operator-file drift chore**: `.local/desired-state.yaml` had silently
   drifted from the DB and had to be hand-resynced before applying.
   Recurring friction; recorded in the WorkflowEpisode for the
   workflow-improvement session to judge.

## Self-report

WorkflowEpisode `b9fc98c5-d032-403c-a824-ce1e9548dddf` created
(tags `painful`, outcome `completed`) referencing operations
`01KZC3R1P88TR4GKC813X9SMDA`, `01KZC3R7GYBH3CP0CY5QB6WJSF`,
`01KZC3TR5PGANVD4MZCW4SQRDG`, `01KZC3VR3JMB69YJJXQ60P63JG`.
