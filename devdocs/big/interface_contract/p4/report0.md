# Phase 4 Step 0 Report — Recapture boundary, evidence, and live preservation baseline

Plan: [plan.md](plan.md), Step 0.

Status: complete. Read-only recapture only. No live mutation, no Job run, no service
stop/restart, no database/media action.

Evidence directory: `.local/interface-contract/p4/20260725_161413/` (mode `0700`; all files
inside mode `0600`). Not committed. Contains raw command output referenced below; no token,
authorization header, Braindump body, Alignment Review summary, or raw custom-field payload was
written to any evidence file (prose fields were hashed, never copied; the `nctl braindump list`
output contains only titles/timestamps/authorship, which was accepted as the tool's normal
non-secret listing format, consistent with prior phases' evidence).

## 1. Exact local/root/submodule/remote state

| Repo | HEAD | Branch tracking | Dirty | Remote `origin/main` after fetch |
|---|---|---|---|---|
| superproject | `6e94147c34c4ad1b0f3bfdaeca9b4e176b7bf6cc` | `main...origin/main` | only untracked `devdocs/big/interface_contract/p4/` (this plan work) | n/a (superproject has no single fast-forward remote check beyond submodule pointers) |
| nintent | `5881a6f85bae07a5d2a48aaa94b067e0bcc197e5` | up to date | clean | `5881a6f85bae07a5d2a48aaa94b067e0bcc197e5` (equal) |
| nctl | `bafe7d2b9a9a5d704087e7c2edf96226d349ac8f` | up to date | clean | `bafe7d2b9a9a5d704087e7c2edf96226d349ac8f` (equal) |
| nauto | `2635e648469d6e6bad87af113f7427b878b0a387` | up to date | clean | `2635e648469d6e6bad87af113f7427b878b0a387` (equal) |
| nodeutils | `3a0fdf9817d970935847aafd46c35bf07133c20c` | up to date | clean | `3a0fdf9817d970935847aafd46c35bf07133c20c` (equal) |
| ansible_agdev | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | up to date | clean | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` (equal) |

All five submodules are clean and exactly equal to the Section 3.2 planning-time snapshot and to
their remotes. No unclassified desired/YAML change occurred since Phase 0/1: the checked-out
`nauto/seed/intent_sources.yaml` SHA-256 (`598391e0...` below) matches the value already recorded
in [`p1/report2.md`](../p1/report2.md) line 61, and the container image IDs below match
[`p0/report0.md`](../p0/report0.md) lines 38–39 and [`p1/report0.md`](../p1/report0.md) line 32
exactly — the live stack has not been touched since those reports.

Item 3 of the plan ("confirm all required repaired commits are available remotely") does not yet
apply: Step 1 has not produced any repaired commit. The check performed here instead confirms the
pre-repair baseline itself is fully pushed, so Step 3's later re-check has a known-good starting
point.

## 2. Live container/image/version state

| Container | Image ID | Started | Health |
|---|---|---|---|
| `nautobot-nautobot-1` (web) | `sha256:bde751b17d15...` | 2026-07-25T11:14:08Z | healthy |
| `nautobot-nautobot-worker-1` | `sha256:7cc4a365bfcf...` | 2026-07-25T11:02:30Z | healthy |
| `nautobot-nautobot-scheduler-1` | `sha256:909f8f54e8d0...` | 2026-07-25T11:02:30Z | healthy |

Installed nintent direct-url SHA in all three containers: `c343c5a56047b0df9ad901dd4459863ef1954053`
(package `nautobot-intent-catalog==0.9.0`), matching Section 3.2 and confirming no rebuild has
occurred. Nautobot 3.1.3, Django 5.2.14, PostgreSQL 15.17, redis-py client 7.4.0. Applied
migrations for `nautobot_intent_catalog` end at `0016_remove_reconciliation_dashboard_surfaces`
(no later migration exists in any container).

## 3. Available remote commits and dirty-state confirmation

Covered in Section 1 above; no push was performed by this step.

## 4. Evidence directory

Created at `.local/interface-contract/p4/20260725_161413/` with `drwx------` (0700) permissions;
every file written into it was subsequently `chmod 600`.

## 5. Live preservation manifest (Section 5.2)

Captured via a read-only script executed through `nautobot-server shell` (stdin) in the web
container, computing counts and per-row digests without ever printing `body` or `summary` text
(only their SHA-256 prefixes). Full result: `preservation_manifest.json` in the evidence
directory. Root counts, matching the Section 5.3 planning-time hypothesis exactly:

| Root | Live count |
|---|---:|
| IntentSource | 2 |
| DesiredNode | 5 |
| DesiredEndpoint | 5 |
| DesiredIPRange | 3 |
| DesiredNodeOperationalOverride | 0 |
| DesiredService | 6 |
| DesiredDependency | 0 |
| DesiredServicePlacement | 1 |
| DesiredComputePlatform | 0 |
| DesiredComputeInstance | 0 |
| **Declared-root total** | **22** |
| BrainDumpDocument | 5 (all `user_direct` authorship; body only hashed, never exported) |
| AlignmentReview | 5 (summary only hashed, never exported) |
| DesiredNode realized links | 5 |
| DesiredEndpoint realized links | 5 |

This is the pre-Phase-4 baseline for the Step 9 preservation-audit comparison; it is not itself an
approval of any change.

## 6. Jobs / JobResults / ScheduledJob / JobHook

No conflicting Job is active: `JobResult` objects in `PENDING`/`RUNNING`/`STARTED`/`SCHEDULED`
status = 0. Latest `JobResult` is `AI Resource Review`, `SUCCESS`, completed
2026-07-24T18:31:33Z. `ScheduledJob` count = 0. One `JobHook` is registered and enabled:
`AI Resource Auto Review`. Installed nintent Jobs currently discoverable: `AnalyzeIntentSources`,
`ImportIntentSources`, `PreviewIntentSourceAnalysis`, `ReconcileDesiredIPAMIntent` (four, not the
Phase-4 target of three — expected pre-repair state; not a Step 0 defect). Full listing:
`jobs_and_results.txt`.

## 7. Canonical YAML file, roots, and identities

`nauto/seed/intent_sources.yaml` (checked-out working copy) SHA-256:
`598391e02041c433df468629cc86d2a2c948c94b80f89a1746a28057b557455b`. Contains exactly the nine
required roots (`intent_sources`, `desired_nodes`, `desired_endpoints`, `desired_ip_ranges`,
`desired_compute_platforms`, `desired_compute_instances`, `desired_services`,
`desired_service_placements`, `desired_node_operational_overrides`) with list lengths
`2/5/5/3/0/0/6/1/0` — exactly the 22-identity hypothesis, confirmed by plain YAML parse (not yet
run through the production `ImportIntentSources` Job, which is out of scope for a read-only Step
0; the loader-shape confirmation is deferred to the disposable proof in Step 2 and the live
`apply=false` preview in Step 6).

## 8. nauto GitRepository revision/path behavior — confirms Section 3.3's blocker precisely

This step reproduces and sharpens the Section 3.3 finding with exact current evidence
(`git_repository_state.txt`, `yaml_path_check.txt`):

- The `GitRepository` row (`main`, `https://github.com/iwaag/nauto`, branch `main`) has
  `current_head = 251b056549f1b01f604b42b486fdc12d667db521`.
- The **worker and scheduler** containers' on-disk checkout at
  `/opt/nautobot/git/main/seed/intent_sources.yaml` is at that exact same commit
  (`git rev-parse HEAD` inside the worker container returns
  `251b056549f1b01f604b42b486fdc12d667db521`) and its SHA-256 is
  `af7c38d1cc29c8b3037ce3f8b4405c018ab4b086456283aa5a0f03e4d54ed28d` — this matches
  [`p1/report0.md`](../p1/report0.md) line 32 exactly, so the worker/scheduler Git sync has not
  advanced since Phase 1.
- The **web** container has no `/opt/nautobot/git/main` checkout at all. It instead reads
  `/nauto/seed/intent_sources.yaml` (and an identical copy under the installed package's own
  `.local/lib/.../nauto/seed/` path), whose SHA-256 is `598391e0...` — the *current* checked-out
  nauto submodule content, not the Git-repository-synced content.
- `PLUGINS_CONFIG` for `nautobot_intent_catalog` is `{}`/`None` in the web container — no explicit
  `NAUTOBOT_INTENT_SOURCES_FILE` is configured anywhere.

Net effect, precisely recorded: web, worker, and scheduler would resolve the "canonical" YAML to
three different filesystem paths today, and web's path has different content (current nauto
`main`) than worker/scheduler's path (nauto Git repository last synced to commit
`251b056...`, older than the current nauto submodule HEAD `2635e648...`). This is exactly the
blocker Section 3.3 requires Step 3 to close before any Import Job can be trusted, now confirmed
with exact paths, commits, and digests rather than the earlier approximate description.

## 9. Live GraphQL/REST/UI rollback baseline

- REST root (`/api/plugins/intent-catalog/`) currently exposes all seven pre-contraction
  collections: `nodes`, `braindumps`, `alignment-reviews`, `endpoints`, `services`,
  `compute-platforms`, `compute-instances` — confirms Phase 2's REST contraction is not deployed.
  `OPTIONS` on `nodes` shows full POST/PUT field authority (not yet narrowed to
  `lifecycle`/`realized_device`/`realized_device_source`). Full output: `rest_routes.txt`.
- GraphQL schema still registers singular/plural `intentSource`/`intentSources` roots — confirms
  Phase 2's GraphQL contraction is not deployed. Full field list: `graphql_roots.txt`.
- The checked-out **source** (`nintent/nautobot_intent_catalog/urls.py`) already declares exactly
  22 `path()` routes — consistent with the Section 2 audit's finding that Phase 3's UI deletion is
  present in source but not in the running (pre-Phase-1) package. `ui_route_count.txt`.
- `nctl status`, `nctl drift --json`, `nctl ops list`, and `nctl braindump list` all ran cleanly
  against live Nautobot (`nctl_status.txt`, `nctl_drift.json.txt`, `nctl_ops_list.txt`,
  `nctl_braindump_list.txt`) and form part of the rollback/read-only baseline required by the
  Section 7 verification matrix.

## 10. Operation/artifact directory manifests

`~/.local/state/nctl/events` contains 918 entries (names/timestamps only, no content read) and
`.local/workspace/` contains prior session folders (`brainforge/...`); both recorded as entry-name
manifests in `operation_dir_manifest.txt` without opening any file that could carry private
prose or credentials.

## Gate check

- Live baseline is readable: yes (Sections 1–2, 5–9).
- No unclassified desired/YAML change since Phase 0/1: confirmed — image IDs, installed nintent
  SHA, and both YAML digests (web-path and worker/scheduler-path) are byte-identical to the values
  already recorded in `p0/report0.md` and `p1/report0.md`/`report2.md`.
- Evidence is sanitized: confirmed (Section "Evidence directory" above; no secrets, tokens, or
  prose bodies were written).
- No live mutation occurred: confirmed — every action taken was a `GET`/read-only ORM query,
  `docker exec`/`docker inspect`, `git status`/`fetch`, or a read-only `nctl` subcommand
  (`status`, `drift --json`, `ops list`, `braindump list`); no Job was submitted, no REST POST/
  PATCH/DELETE was issued, no container was restarted.

Step 0 gate is satisfied. Next: Step 1 (repair Phase 3 tests and active documentation), which is
source/test/documentation work and does not require a new live-maintenance approval.
