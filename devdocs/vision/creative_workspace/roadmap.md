# Creative Workspace Management — Implementation Roadmap

## Purpose

Represent development workspaces (composite Git checkouts under active development, e.g.
`pj-voxel3dprint` on `agpc`) as a first-class domain beside services, so the system can answer:
*which PC is developing which composite project, and is each workspace ready to use?*

Baseline design: [opinion2.md](opinion2.md), with two elements adopted from
[opinion1.md](opinion1.md) — the build-input-fingerprint model for build readiness (opinion1 §6)
and the workspace-mutation safety notes (opinion1 §10, applied lightly). Where this roadmap and
the opinions disagree, this roadmap wins.

## Premises

- **Breaking-change phase.** The current `DesiredService`/`DesiredServicePlacement` representation
  of `pj-voxel3dprint` is removed in the same rollout that lands the workspace concept. No dual
  readers, no aliases. Normal Django migration history is still kept.
- **Experimental cluster, single operator.** Security stays at the existing level (Nautobot token,
  LAN). Do not build authorization layers, signing, or audit machinery for this initiative.
- **Minimal first, promote on consumption.** One real workspace (`pj-voxel3dprint`) drives the
  schema. Raw observation data is recorded generously; a field becomes a typed model field or
  column only when a deterministic consumer (drift rule, view, planner) uses it. Agents read raw
  fields freely; unmodeled is not a defect.
- **Implementer discretion.** Exact field names, payload layout, module placement, and test shape
  are free choices unless a rule below constrains them. Prefer reusing existing patterns
  (freshness contract, batch writer, drift evaluation, `nctl relations`-style projection) over
  inventing parallel ones.

## Hard rules (the only prohibitions)

1. **No desired commit/branch/cleanliness.** The desired side never pins a revision. Divergence
   from origin and a dirty tree are evidence of work, not drift. If a "deploy exact revision"
   need appears, that is a separate release concept, not this one.
2. **Reconcile never acts on informational status.** Convergent drift codes and informational
   status codes live in separate fields/namespaces so a planner cannot consume the latter by
   accident. (Precedent: the `unreferenced` list in `nctl relations`.)
3. **Deleting a checkout stays behind the existing `--allow-destroy`-style explicit boundary.**
   A working tree may hold unpushed work — the least recoverable state in the cluster. Pull,
   reset, clean, and delete, when they eventually exist, are separate planned actions, never a
   generic "sync".
4. **Observation is metadata-only.** Bounded reads, no file contents, no credentials — same
   posture as existing nodeutils collectors.

Everything else — including how much raw data to collect — is implementer judgment.

## Domain summary

| Concept | Shape | Content |
|---|---|---|
| `DesiredWorkspace` | new nintent first-class model, parallel to services | slug/name, source remote URL, one placement (DesiredNode + expected path), `desired_presence` (present/absent), standard lifecycle |
| `observed_workspaces` | new nodeutils section, separate from `observed_services` | promoted fields + one open `raw` object per workspace |
| Workspace evaluation | nctl, fresh computation, never persisted | convergent drift + informational status + `nctl workspaces` view |

Promoted observation fields from day one (each has an immediate deterministic consumer):

| field | consumer |
|---|---|
| path, presence | presence drift |
| superproject remote URL, HEAD SHA | identity matching against the declared source |
| ahead/behind vs tracked remote, dirty flag, last-commit time | activity classification in the view |
| observation timestamp | standard freshness contract |

Everything else (per-submodule status, branch/stash/rebase markers, build/artifact markers,
compose-in-workspace state, disk footprint, newest-mtime hints) starts inside `raw` and is
promoted only by the phase that consumes it.

## Phases

Each phase follows the usual style: step-by-step execution, one report + commit per step, pause
for judgment before live/hard-to-reverse actions. Test gates per the README_DEV command matrix
for whichever components a phase touches.

### Phase 0 — Desired model and declaration

Add `DesiredWorkspace` to nintent; wire it into the batch desired-state writer (its own top-level
section in the batch document, mirroring first-class status) and the GraphQL reader. Declare
`pj-voxel3dprint` on `agpc` with its real path and remote URL in `.local/desired-state.yaml`.

Start with exactly one placement per workspace; relax only when a real multi-node development
pattern exists. Node retirement should require retiring hosted workspaces first, mirroring the
compute-platform protection rule — a validation error in the batch writer is enough.

Hints:
- nintent changes reach the local Nautobot only via commit → push (ask the user) → image rebuild;
  see `.local/localenv_memo.md`. Plan the phase so pure-domain tests run before the rebuild step.
- Reuse the existing lifecycle vocabulary and batch-writer validation patterns rather than new ones.

Exit: batch apply (preview then `--yes`) creates the row; GraphQL returns it; nintent test gates
pass.

### Phase 1 — Observation and service-representation removal

Add the `observed_workspaces` collector to nodeutils (promoted fields above + `raw`), and ingest
it through nauto into actual state. In the same rollout, remove `pj-voxel3dprint` from
`IMPORTANT_SERVICE_NAMES` and delete its `DesiredService`/`DesiredServicePlacement` rows — after
this phase it must be impossible for a workspace to raise `service_missing`.

Hints:
- `git status --porcelain=v2 --branch` gives branch, upstream, ahead/behind, and dirty state in
  one parseable call; `git rev-parse HEAD` and `git config --get remote.origin.url` cover
  identity. Ahead/behind counts are only as fresh as the last `git fetch`; that staleness is
  acceptable and expected — do not fetch from inside the collector (it is a network write to the
  workspace's remote-tracking state, and fetch-only refresh is a Phase 3 action).
- Fixed to `origin` for divergence measurement until a real workspace breaks that.
- A missing or non-git path is a normal observation result (presence=false / identity unknown),
  not a collector error.
- Remember the nintent rebuild cache gotcha: `docker compose build` can silently reuse a stale
  commit; use `--no-cache` and verify the resolved SHA in the build log.

Exit: a real collection on `agpc` produces the workspace observation; ingest lands it in
Nautobot; `nctl drift` no longer reports `service_missing` for `pj-voxel3dprint`; nodeutils/nauto
gates pass.

### Phase 2 — Evaluation and the workspace view

Add workspace evaluation to nctl:

- **Convergent drift** (reconcile may act, actuation itself still absent):
  `workspace_missing` (desired present, checkout absent), `workspace_identity_mismatch` (checkout
  present, remote differs from declared source), `workspace_retired_present` (desired absent,
  checkout present — report only), plus observation-missing/stale via the standard freshness
  contract.
- **Informational status** (separate namespace, per hard rule 2): `active_development` (ahead
  and/or dirty), `behind_origin`, `idle`. Include structured reasons so the classification is
  explainable from the promoted fields it consumed.
- **`nctl workspaces`**: computed on demand, never persisted, `--json` for agents — same style as
  `nctl relations`. One row per declared workspace: node, presence, identity match, activity
  class, observation freshness.

Hints:
- Reuse the drift evaluation plumbing; workspace findings get their own target kind so service
  vocabulary never leaks in.
- Keep `nctl drift` and `nctl workspaces` calling the same evaluation so they cannot disagree —
  the same invariant `nctl relations` already holds.

Exit: live run shows `pj-voxel3dprint` as present, identity-matched, with a truthful activity
class; nctl gate passes. **This is the minimal useful system; later phases are demand-driven.**

### Phase 3 — Actuation ladder (optional, in value order)

Build each rung only when actually wanted, and promote exactly the raw fields it consumes:

1. **Fetch-only refresh** — a planned action running `git fetch` so ahead/behind is current
   without touching the working tree. Safe, read-mostly; a good first actuation.
2. **Background pre-build** — the motivating feature: when a workspace is build-stale, plan a
   build task so a multi-hour build finishes before the user needs it. Adopt opinion1 §6 here:
   promote build readiness as *current input fingerprint == fingerprint of last verified
   successful build*, never as a `build_completed` boolean. Requires defining a build profile
   (command, inputs) for `pj-voxel3dprint` first; let that one real project decide the shape.
   Raw build/artifact markers collected since Phase 1 are the substrate for choosing fingerprint
   inputs.
3. **Bootstrap clone** — materialize a `workspace_missing` workspace on a new node. Follows the
   existing plan/apply/observe/fresh-drift loop; simplest last rung.

## Relationship to services

Unchanged from opinion2 §3.5: workspaces and services stay orthogonal. `docker compose up` inside
a workspace creates no service intent. If a workspace-hosted stack should be cluster-managed,
that is declared as a normal `DesiredService`, optionally carrying an informational reference to
the workspace. Nothing in the service evaluation path changes.

## Non-goals

- No desired revision pinning, no "sync my workspace" action (hard rule 1).
- No generic project management (issues, CI status) — only existence, identity, activity, and
  readiness of checkouts on cluster nodes.
- No generalization to non-git workspace kinds until a second real workspace demands it.
- No persisted workspace status dashboard — status is always a fresh computation.
