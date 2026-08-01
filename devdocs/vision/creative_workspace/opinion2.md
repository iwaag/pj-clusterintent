# Opinion 2: Modeling Development Workspaces Outside the Service Concept

Status: design proposal only. No migration plan, no implementation steps.
Written without reading opinion1.md, per instruction.

## 1. Problem

`pj-voxel3dprint` is a composite GitHub project (multiple repositories grouped
into one runnable unit) cloned onto `agpc` as a working checkout, with docker
compose brought up locally and active development happening inside it. Today
this reality is declared through `DesiredService` / `DesiredServicePlacement`,
the same models that describe daemons such as ollama or open-webui.

The fit is bad in a visible way: the service_relation Phase 0 audit already
records `pj-voxel3dprint` as permanently drifting with `service_missing`. That
is not a configuration mistake — the service observation contract (is a
process/container present?) simply cannot see what a workspace is. The states
that matter for a workspace are of a different kind:

- is the checkout present at its path, and which superproject commit is it at;
- how far it has diverged from `origin` (ahead/behind, dirty tree) — which is a
  signal of **active development**, not an error;
- whether long build artifacts are up to date, so a multi-hour build can be
  started in the background before the workspace is needed.

None of these belong in a service placement's config bag, and forcing them
there blocks exactly the workspace-specific management features we want.

## 2. Design principles

Three principles drive the shape of this proposal.

### 2.1 Thin desired, thick observation

For services, divergence from desired state is a defect and reconcile removes
it. For a workspace the most interesting states — ahead of origin, dirty tree,
half-finished build — are **evidence of work in progress**. A reconciler must
never "fix" them; converging a dirty working tree toward origin destroys work.

Therefore the desired side of a workspace carries only what the system may
legitimately act on (existence, location, identity of the composite project),
while everything else lives on the observation side as reported state. Most of
the workspace concept is a *ledger of what is actually happening*, not a target
to converge to.

### 2.2 Raw data first, promote on deterministic consumption

This system deliberately mixes non-deterministic agent operations with
deterministic Ansible/Python operations. The data policy follows from that:

- **Record generously as raw observation.** Anything a collector can cheaply
  and safely gather about a workspace goes into the observation payload as
  semi-structured raw data. Agents can read, interpret, and reason over raw
  fields freely; being unmodeled is not a defect at this stage.
- **Promote sparingly to schema.** A field becomes a real database column /
  typed model field only once a *deterministic* consumer exists — a drift rule,
  a planner input, a renderer, a validation. This is the same discipline as the
  existing provider advice ("add only fields with a named drift, planning,
  actuation, or safe-identification consumer"), restated as a two-tier
  raw/promoted lifecycle instead of a one-shot modeling decision.

Concretely: the observation schema gets one open `raw` object per workspace
from day one, and the promoted fields listed in section 4 are the only ones
with schema status. Everything else waits in `raw` until something
deterministic needs it.

### 2.3 Breaking-change phase applies

There is no requirement to preserve the current `pj-voxel3dprint` service
declaration, its placement rows, or the `IMPORTANT_SERVICE_NAMES` treatment in
nodeutils. When the workspace concept lands, the service-shaped representation
of workspaces is removed in the same coordinated rollout — no dual readers, no
compatibility aliases.

## 3. Proposed concepts

### 3.1 Desired side: `DesiredWorkspace` (minimal)

A new first-class desired model, parallel to (not nested under) services:

- **identity**: slug/name of the composite project (e.g. `pj-voxel3dprint`);
- **source**: the superproject remote URL (public identity only; credentials
  and clone mechanics stay outside nintent, as with compute providers);
- **placement**: the `DesiredNode` that should host the checkout, and the
  expected path on that node;
- **desired_presence**: `present` / `absent` — the only convergent axis;
- **lifecycle**: the standard proposed → active → retired vocabulary already
  used by other desired models.

Deliberately absent: desired commit, desired branch, desired build state,
desired cleanliness. Pinning a workspace to a commit would make active
development itself read as drift, which inverts the concept's purpose. If a
"deploy this exact revision" need appears later, that is a different concept
(a release/deployment target, service-shaped) and should not be retrofitted
onto the development workspace.

Whether one workspace can be desired on multiple nodes at once can start
restricted (one placement per workspace) and be relaxed only when a real
multi-node development pattern exists.

### 3.2 Observation side: `observed_workspaces` (rich, raw-first)

nodeutils gains a dedicated `observed_workspaces` section, separate from
`observed_services`. `pj-voxel3dprint` leaves `IMPORTANT_SERVICE_NAMES`. Per
workspace, the observation carries:

**Promoted (schema-level, because deterministic consumers are already known):**

- path and presence — consumed by presence drift;
- superproject remote URL and current commit SHA — consumed by identity
  matching (is this checkout the declared workspace?);
- ahead/behind counts vs the tracked remote, dirty-tree flag, last commit
  timestamp — consumed by the informational activity report (section 3.3);
- an observation timestamp — the standard freshness contract; cached
  workspace facts without a collection time are not current.

**Raw (open object, agent-readable, promotion candidates):**

- per-submodule status (each submodule's SHA, ahead/behind, dirty);
- branch name, stash count, in-progress rebase/merge markers;
- build/artifact markers (e.g. presence and mtime of named build outputs,
  compose image build status) — the raw substrate for the future
  "pre-build in background" planner;
- compose project state as seen from inside the workspace (services defined
  vs running);
- disk footprint, recent-activity hints (newest mtime under the tree).

The collector must respect the existing observation safety posture: bounded
reads, no file contents, no credentials, public identifiers and digests only.
A workspace observation is a metadata probe, not a backup or content scan.

### 3.3 Drift semantics: two explicitly separate classes

This is the core of the proposal. Workspace evaluation produces two outputs
that must never be merged:

1. **Convergent drift** — the only class reconcile may act on:
   - `workspace_missing`: desired present, checkout absent → plannable
     clone/bootstrap action (actuation itself can come later; the drift code
     comes first);
   - `workspace_unexpected` / identity mismatch: a checkout exists at the
     declared path but its remote does not match the declared source;
   - `workspace_retired_present`: desired absent, checkout still present —
     reported, and destruction stays behind the existing
     `--allow-destroy`-style explicit boundary since a working tree may
     contain unpushed work.

2. **Informational status** — reported, rendered, and available to agents and
   planners, but **structurally unreachable from reconcile actions**:
   - `active_development` (ahead of origin and/or dirty);
   - `behind_origin` (fetchable updates exist);
   - `build_stale` / `build_ready` (once build markers are promoted);
   - `idle` (clean, in sync, no recent activity).

The system already has a precedent for an informational, never-actuated
projection: the `unreferenced` service list in `nctl relations`. Workspace
activity status is the same kind of citizen. The separation should be enforced
by construction — informational codes live in a different field/namespace than
convergent drift codes, so no future planner can accidentally treat "dirty
tree" as something to fix.

### 3.4 Projection: a workspace view in nctl

The user-facing question this concept exists to answer is: *which PC is
actively developing which composite project, and is each workspace ready to
use?* That is a fresh projection over desired + observed state, in the same
style as `nctl drift` and `nctl relations`: computed on demand, never
persisted, with `--json` for agent consumption. One row per declared
workspace: node, presence, identity match, activity class, and (later)
build-readiness.

### 3.5 Relationship to services

Workspaces and services stay orthogonal, connected by reference only:

- A workspace is **not** a service, and running `docker compose up` inside a
  workspace does not automatically create service intent.
- If a workspace-hosted stack should be managed as a real service (converged,
  bound, monitored), that is declared explicitly as a normal
  `DesiredService`/`DesiredServicePlacement`, which may carry a reference to
  the `DesiredWorkspace` that provides its runtime. The reference is
  informational context ("this service runs out of that checkout"), not a
  dependency edge with reconcile semantics — at least until a deterministic
  consumer for such an edge exists.
- Nothing in the service evaluation path changes; workspaces simply stop
  abusing it.

### 3.6 Future actuation, in order of appearance

Actuation is intentionally out of scope for the first cut, but the design
should leave room for these, in this order of likely value:

1. **fetch-only refresh**: update remote-tracking state so behind/ahead is
   accurate without touching the working tree — safe, read-mostly;
2. **background pre-build**: when a workspace is `build_stale` and the node is
   idle, plan a build task so a multi-hour build finishes before the user
   needs it — the first real planner consumer of the build markers, and the
   trigger to promote them from raw to schema;
3. **bootstrap clone**: materialize a `workspace_missing` workspace on a new
   node.

None of these justify adding fields today. Each one, when built, names the raw
fields it consumes and promotes exactly those.

## 4. What gets promoted now vs later

| data | tier now | promotion trigger |
|---|---|---|
| path, presence | promoted | presence drift (immediate) |
| remote URL, superproject SHA | promoted | identity matching (immediate) |
| ahead/behind, dirty, last-commit time | promoted | activity classification (immediate) |
| observation timestamp | promoted | freshness contract (immediate) |
| per-submodule status | raw | a deterministic per-submodule rule appears |
| branch, stash, rebase markers | raw | agent-only until proven otherwise |
| build/artifact markers | raw | the pre-build planner is built |
| compose-in-workspace state | raw | a service↔workspace consumer is built |
| disk footprint, activity hints | raw | likely never; agent context only |

## 5. Non-goals

- No desired commit/branch pinning; no "sync my workspace" reconcile action.
- No content observation of files inside the workspace beyond public metadata
  and digests of named build markers.
- No generic "project management" system — issues, tasks, and CI status stay
  outside; this concept covers only the checkout's existence, identity,
  activity, and readiness on cluster nodes.
- No premature generalization to non-git or non-compose workspace kinds; one
  real workspace (`pj-voxel3dprint`) drives the schema, per the established
  one-real-resource-first rule.

## 6. Open questions

1. Should workspace registration begin observation-only (nodeutils detects
   checkouts under declared scan roots) with desired declaration added once
   bootstrap-clone actuation is wanted, or start desired-first as proposed?
   Desired-first is recommended because the ledger question ("which PC should
   be developing what") is itself the primary use case, but the
   observation-only start is cheaper.
2. Where does the workspace→node association live in the desired-state batch
   document — as its own top-level section (recommended, mirroring its
   first-class model status) or nested under nodes?
3. How is "the" remote defined for divergence measurement when a workspace has
   multiple remotes — fixed to `origin`, or declared per workspace? Start
   fixed to `origin` and revisit only if a real workspace breaks it.
4. Does retiring a `DesiredNode` that hosts a workspace require the workspace
   to be retired first (mirroring the compute-platform protection rule)?
   Probably yes, for the same reason: unpushed work is the most valuable and
   least recoverable state in the cluster.
