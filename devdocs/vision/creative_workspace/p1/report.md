# Creative Workspace — Phase 1 Report: Observation and service-representation removal

## Exit criteria

| # | Criterion | Evidence |
|---|---|---|
| 1 | A real collection on `agpc` produces an `observed_workspaces` entry for `/home/eiji/projects/pj-voxel3dprint` with the promoted fields populated. | [report_step6.md](report_step6.md) — live `nctl reconcile agpc --refresh-observation` collected `present: true, path, head_sha, remote_url, branch, ahead, behind, dirty, last_commit_at, checked_at`; user-confirmed the values match the real tree. |
| 2 | Ingest lands it in Nautobot (visible on the `agpc` Device). | Same evidence — fetched live from `agpc`'s `observed_workspaces` custom field via the REST API after the reconcile round. |
| 3 | `nctl drift` reports no `service_missing` (or any other service finding) for `pj-voxel3dprint`, and `pj-voxel3dprint` is gone from `IMPORTANT_SERVICE_NAMES`. | [report_step4.md](report_step4.md) (desired-state delete) + [report_step6.md](report_step6.md) (fresh drift after live rollout: zero `voxel` occurrences, `ok: true`); [report_step1.md](report_step1.md) (`IMPORTANT_SERVICE_NAMES` removal, tested). |
| 4 | Test gates pass for every touched component. | [report_step5.md](report_step5.md): nodeutils 76 passed, nauto 112 passed, nctl 1109 passed, Nautobot runtime gate `--keepdb` 216 cases `OK`. |

All four exit criteria **complete**.

## What was built, by step

- **Step 0** ([report_step0.md](report_step0.md)): read-only baseline — confirmed the exact
  `DesiredService`/`DesiredServicePlacement` row ids and the single `service_missing` drift finding
  that Step 4 needed to target.
- **Step 1** ([report_step1.md](report_step1.md), nodeutils `5ebd415`): `observed_workspaces`
  collector — bounded, metadata-only `git` probes (`safe.directory` workaround, never fetches),
  degrading gracefully on any missing path, non-git directory, or individual command failure.
  Removed `pj-voxel3dprint` from `IMPORTANT_SERVICE_NAMES` in the same commit.
- **Step 2** ([report_step2.md](report_step2.md), nctl `32d3e6d`): `DesiredWorkspace` added to the
  GraphQL desired-state fetch; `render_probe_hints` emits `workspace_probe_hints` for
  active/present workspaces on the target node, keeping the declared path single-owner.
- **Step 3** ([report_step3.md](report_step3.md), nauto `2f453f1`): seeded the
  `observed_workspaces` JSON custom field; `build_custom_fields` passes it through as pure ledger
  transport, no normalization.
- **Step 4** ([report_step4.md](report_step4.md)): deleted the one `DesiredService` +
  `DesiredServicePlacement` row pair for `pj-voxel3dprint` from the scratch Nautobot via
  `nctl desired apply` (dry preview, then `--yes`).
- **Step 5** ([report_step5.md](report_step5.md)): full affected-matrix gate run, then pushed
  nodeutils/nauto/nctl/superproject to GitHub (all approved).
- **Step 6** ([report_step6.md](report_step6.md)): live rollout — Nautobot Git Repository re-sync,
  seed job run, `nctl reconcile agpc --refresh-observation` (dry then `--yes`), and full positive
  evidence (rendered probe config, pinned nodeutils version in operation evidence, live custom
  field contents, fresh drift).

## Deviations from the plan

None of substance. Two implementation choices the plan left open:

- `desired_workspaces` is decoded in nctl with `.get(...) or []` (not a required GraphQL key like
  the older `desired_service_bindings`), matching the newer compute-root leniency pattern so none
  of the ~8 pre-existing `DESIRED_DATA` test fixtures across the repo needed updating.
- The observation rides in `inventory_raw_json.facts.workspaces` — its own raw key, sibling to
  `facts.services` — because that mirrors exactly where the nodeutils collector promoted it
  (`facts.workspaces`, not nested inside `facts.services`).

`instance_name` for the deleted placement was `agpc-primary`, not `pj-voxel3dprint` as initially
assumed when drafting the delete op — looked up live before applying (Step 4).

## Handed to Phase 2

Phase 2 ("Evaluation and the workspace view") needs a reader in
`nctl/src/nctl_core/sources/actual.py` for the `observed_workspaces` custom field — deliberately
not built here, per the plan.

**Exact names Phase 2 will read verbatim:**

- Custom field key on the Device: `observed_workspaces` (JSON), keyed by workspace slug
  (e.g. `pj-voxel3dprint`).
- Promoted per-workspace fields: `present` (bool), `path`, `head_sha`, `remote_url`, `branch`,
  `ahead` (int, absent if no upstream), `behind` (int, absent if no upstream), `dirty` (bool),
  `last_commit_at` (ISO 8601), `checked_at` (ISO 8601). A non-git directory has `present: true` and
  no identity fields; a missing path has `present: false` only.
- Everything else lives under `raw` (currently: `is_git` when false, `upstream`, `stash_count`,
  `submodule_status`) — unmodeled, promote only when a Phase 2 rule actually consumes it.
- `DesiredWorkspace` (nctl `sources/desired.py`) fields available for identity/presence matching:
  `slug`, `lifecycle`, `desired_presence`, `source_remote_url`, `expected_path`, `node_id`,
  `node_slug`.

## Scope confirmation

Touched: nodeutils, nctl, nauto, `.local/desired-state.yaml` (gitignored operator input), and
superproject submodule pointers, exactly as the plan's Scope section stated. No nintent code
change — `DesiredWorkspace` was consumed read-only via GraphQL as planned. No drift/evaluation
logic was added to nctl (that is Phase 2, per the plan's explicit exclusion).

Phase 1 is complete.
