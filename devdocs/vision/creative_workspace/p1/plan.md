# Creative Workspace — Phase 1 Plan: Observation and service-representation removal

Parent: [roadmap.md](../roadmap.md). Its Premises and Hard rules are the only prohibitions.
Everything below not marked **required** is a recommendation or a hint — deviate freely when the
code argues for it.

## Goal

Collect `observed_workspaces` on cluster nodes via nodeutils, ingest it into Nautobot via nauto,
and — in the same rollout — remove the old service representation of `pj-voxel3dprint` so a
workspace can never again raise `service_missing`.

**Exit criteria (required):**
1. A real collection on `agpc` produces an `observed_workspaces` entry for
   `/home/eiji/projects/pj-voxel3dprint` with the promoted fields populated.
2. Ingest lands it in Nautobot (visible on the `agpc` Device).
3. `nctl drift` reports no `service_missing` (or any other service finding) for
   `pj-voxel3dprint`, and `pj-voxel3dprint` is gone from `IMPORTANT_SERVICE_NAMES`.
4. Test gates pass for every touched component (nodeutils, nauto, nctl; runtime gate because
   this crosses components).

## Scope

nodeutils (collector), nauto (ingest + custom-field seed), nctl (desired snapshot + probe-hint
rendering only — **no drift/evaluation logic**, that is Phase 2), `.local/desired-state.yaml`
(service-row deletion), and superproject submodule pointers. No nintent code change is expected;
the `DesiredWorkspace` model from Phase 0 is consumed read-only via GraphQL.

## Key design facts discovered while planning

- **How the collector learns which paths to observe.** nodeutils is desired-state-agnostic; the
  existing bridge is nctl's per-host probe config: `render_probe_hints()` in
  `nctl/src/nctl_core/observation.py` renders `service_probe_hints` from the desired snapshot
  into `probe-config/<host>.yaml`, which the collection playbook hands to the collector as its
  config. **Recommended:** extend the same file with a `workspace_probe_hints` (name → expected
  path) section rendered from declared workspaces, so the declared path keeps one owner
  (README_DEV lesson 4). This requires adding workspaces to `DesiredSnapshot`
  (`nctl/src/nctl_core/sources/desired.py`) — Phase 0 explicitly deferred that to the first
  consumer, which is now. The GraphQL query and proven field names are in
  `p0/report_step6.md`; the plural is `desired_workspaces`.
- **Where observations land.** nauto's ingest writes node facts as Device custom fields
  (`build_custom_fields` in `nauto/jobs/ingest_nodeutils_inventory.py`; `observed_services` is
  the direct precedent at ~line 645). Custom-field *definitions* are seeded from
  `nauto/seed/home_cluster.yaml` (`observed_services` entry ~line 336) by the seed job — a new
  `observed_workspaces` JSON custom field needs a seed entry and one seed-job run.
- **No `desired_service: pj-voxel3dprint` exists in `.local/desired-state.yaml`** — the rows
  live only in the scratch DB from an older apply (the yaml is input, not a synced mirror).
  Removal is therefore explicit `op: delete` batch operations, not deleting a yaml stanza.
  Deletes run in reverse `KIND_ORDER`, so placement + service deletes in one document sequence
  correctly.
- **Deployment paths differ per component.** nodeutils deploys at the exact commit pinned by
  the superproject (`resolve_nodeutils_version`), so the superproject pointer must be updated
  and pushed before live collection. nauto Jobs arrive via the Nautobot Git Repository — push,
  then re-sync the repository in Nautobot (no image rebuild). nctl runs locally from the
  worktree. nintent needs no rebuild this phase.

## Proposed observation shape

One entry per hinted workspace, keyed by workspace slug/name, promoted fields flat, everything
else under `raw`:

| promoted field | source | consumer (Phase 2) |
|---|---|---|
| `path`, `present` | hint + `os.path` / git detection | presence drift |
| `remote_url` | `git config --get remote.origin.url` | identity matching |
| `head_sha` | `git rev-parse HEAD` | identity/activity |
| `ahead`, `behind`, `dirty`, `branch` | `git status --porcelain=v2 --branch` | activity classification |
| `last_commit_at` | `git log -1 --format=%cI` | activity classification |
| `checked_at` | collection timestamp | freshness contract |

`raw` is yours: per-submodule status (`git submodule status` is one bounded call), stash count,
rebase/merge markers, newest-mtime hints, disk footprint, compose files present — collect
generously (roadmap: "raw is recorded generously"), but keep each read bounded like the existing
collectors (`run_command` with timeout, `MAX_*` truncation). Exact key names are yours; reuse the
`observed_services` normalization/compaction style.

Handle these as *normal observations*, not errors: path missing (`present: false`), path exists
but is not a git repo (present, identity fields absent, note in `raw`), individual git command
failure (record what succeeded). The collector must never fail the whole inventory because one
workspace probe misbehaved.

## Steps

One report + one commit per step (`p1/report_stepN.md`). Pauses marked.

### Step 0 — Record the current live baseline (read-only)

Via GraphQL/REST against the local Nautobot: confirm whether `DesiredService` /
`DesiredServicePlacement` rows for `pj-voxel3dprint` actually exist in the DB, and run
`uv run --project nctl nctl drift --json` to record whatever findings `pj-voxel3dprint`
currently raises. This is the before-picture the exit criteria are measured against, and it
tells Step 4 exactly which delete ops to write.

### Step 1 — nodeutils collector

- Add workspace observation to `nodeutils/nodeutils_collect.py`: read `workspace_probe_hints`
  from the config (same `load_config` path as `service_probe_hints`), emit a top-level
  `observed_workspaces` section in the inventory (wire it through `collect_inventory` and
  `build_inventory_report` the same way `observed_services` flows).
- Remove `"pj-voxel3dprint"` from `IMPORTANT_SERVICE_NAMES` (~line 74) in the same commit — the
  rollout is coordinated, and nodeutils only reaches nodes as one pinned commit anyway.
- Keep `SCHEMA_VERSION` at `nodeutils.inventory.v2` unless you find a consumer that breaks on an
  additive section — `nctl/src/nctl_core/dumps.py` checks the version string only, and the v1→v2
  bump precedent was a *restructuring*, not an addition. Your call; if you bump, update
  `nauto/seed/nodeutils_ingest.yaml` `schema_versions` and `dumps.py` together.
- Git-in-another-context gotcha: the collector may run as a different user than the workspace
  owner, and git then refuses with `detected dubious ownership`. `git -c safe.directory=<path>
  …` per invocation is a clean metadata-only workaround; verify on `agpc` in Step 6 rather than
  assuming. Ahead/behind is only as fresh as the last fetch — expected, do **not** fetch
  (roadmap hard rule 4 posture; fetch is a Phase 3 action).
- Tests: `nodeutils` ordinary gate (`uv run pytest -q`). Fixture a fake git repo in `tmp_path`
  (real `git init` is fine and preferred over mocking — README_DEV lesson 2) covering: present
  clean, present dirty/ahead, missing path, non-git dir, git command failure.

### Step 2 — nctl probe-hint plumbing

- Extend `DesiredSnapshot` with workspaces: add `desired_workspaces` to the GraphQL query and a
  small model in `sources/desired.py` (slug, node slug, expected path, presence, lifecycle,
  remote URL — cheap to carry all Phase 0 fields now, Phase 2 will want them).
- In `observation.py`'s `render_probe_hints`, emit `workspace_probe_hints` for workspaces placed
  on this node. Decide and document the filter (recommended: lifecycle `active` and presence
  `present` get hints; observing a retired path is harmless but noisy).
- Tests: nctl ordinary gate; extend the existing probe-hint rendering tests with a workspace
  case.

### Step 3 — nauto ingest

- Seed: add an `observed_workspaces` JSON custom field entry to `nauto/seed/home_cluster.yaml`
  next to `observed_services`.
- Ingest: map `observed_workspaces` from the report into the custom field in
  `build_custom_fields`, and let it ride along inside `inventory_raw_json.facts.services` or as
  its own raw key — mirror wherever the collector put it. Keep the pass-through dumb; no
  normalization beyond what nodeutils already did (nauto's job is ledger transport, evaluation
  is nctl's).
- Tests: nauto ordinary gate (`python3 -m unittest discover -s tests`) plus the runtime ingest
  test (`tests_runtime/test_ingest_runtime.py`) via the Nautobot runtime gate.

### Step 4 — Delete the service representation  **(pause: desired-state write)**

Append `op: delete` operations to `.local/desired-state.yaml` for exactly the rows Step 0 found
(placement(s) first in reading order is not required — reverse-`KIND_ORDER` delete ordering
handles it, but keep them adjacent for the reader). Preview with
`nctl desired apply -f .local/desired-state.yaml`, show the user the plan (expected: the
recorded number of deletes, everything else `unchanged`), then `--yes`.

If Step 0 found no rows, record that and skip the write — the exit criterion is absence, not the
delete itself.

### Step 5 — Gates, commits, pushes  **(pause: ask the user to push)**

Run the full affected matrix from README_DEV: nodeutils ordinary, nauto ordinary, nctl ordinary,
then the Nautobot runtime gate `--keepdb` (and `--clean` once if any migration-adjacent doubt —
none is expected this phase; no new nintent migration). Check the stated `cases=` count.

Commit each submodule; update superproject pointers. **Ask the user to push nodeutils, nauto,
nctl, and the superproject** — live collection deploys the superproject-pinned nodeutils commit,
and the nauto Git Repository sync pulls from GitHub.

### Step 6 — Live rollout and proof  **(pause before each live action)**

Scratch-adjacent but touches a real node (`agpc`), so confirm at each arrow:

1. Re-sync the nauto Git Repository in Nautobot and run the seed job so the
   `observed_workspaces` custom field exists (idempotent for everything else it ensures).
2. `uv run --project nctl nctl reconcile agpc --refresh-observation` — dry first, read the plan,
   then `--yes`. This runs the full observe → ingest → fresh-drift loop with the pinned
   nodeutils SHA recorded in the operation evidence.
3. Positive evidence, not absence-of-error (README_DEV lesson 1): fetch the `agpc` Device's
   `observed_workspaces` custom field and confirm the promoted fields match reality (the user
   knows whether the tree is currently dirty/ahead — ask); confirm the operation evidence shows
   the expected nodeutils version; run `nctl drift --json` and confirm no `pj-voxel3dprint`
   service finding remains and no *new* unrelated finding appeared.

If collection works but ingest rejects the report, the fix loops back through Step 3 + a nauto
re-sync only — no node-side redeploy needed.

### Step 7 — Phase report

`p1/report.md`: exit-criteria table with evidence, deviations, and a short "handed to Phase 2"
note listing the exact promoted field names and the custom-field key, since Phase 2's evaluation
reads them verbatim (`nctl/src/nctl_core/sources/actual.py` will need a reader — deliberately
left to Phase 2, which owns the first consumer).

## Known pitfalls, collected

- nodeutils reaches nodes only at the superproject-pinned commit — pointer update + push before
  Step 6, or the live run observes with the old collector and nothing appears.
- nauto Jobs update via Git Repository re-sync, not image rebuild; nintent (untouched) would
  need the `--no-cache` rebuild dance, which this phase avoids entirely.
- The custom field must exist *before* ingest writes it — seed job first (Step 6.1 before 6.2).
- A collector exception must degrade to a partial observation, never a failed report: the
  existing sections all follow "record what succeeded, omit what didn't" — match that.
- `.local/desired-state.yaml` is operator input, not a mirror — deleting DB rows requires
  explicit `op: delete` entries; removing an upsert stanza does nothing.
- Batch `_DELETE_BLOCKERS` may refuse a service delete while placements exist; deleting both in
  one document works because deletes run in reverse `KIND_ORDER`.
- Report payloads have a 2 MiB bound (`MAX_REPORT_BYTES`) and per-value truncation — a generous
  `raw` is fine, an unbounded submodule walk is not.
