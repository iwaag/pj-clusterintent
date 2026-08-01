# Creative Workspace Management — Design Opinion 2

## 1. Proposal in one sentence

Treat a development workspace as a first-class domain beside services, retain broad and
versioned raw observations about it, let agents turn those observations into attributed
assessments and candidates, and promote only the small set of facts required by a proven
deterministic operation into typed desired-state contracts.

This proposal intentionally does not preserve the current representation of
`pj-voxel3dprint` as a `DesiredService` and `DesiredServicePlacement`. The system is in a
breaking-change phase, so a clearer final boundary is more valuable than compatibility with
the existing rows or APIs.

## 2. Why a workspace is not a service

A service is a logical workload expected to be running, reachable, configured, or bound to
another service. Its placement is naturally evaluated using process state, endpoints,
managed configuration, and provider bindings.

A development workspace is a working context placed on a node. It may contain one repository
or many repositories, installed host tools, container images, generated artifacts, caches,
and one or more temporarily running services. Its useful states include:

- whether its checkout exists at the expected location;
- which repositories, remotes, branches, commits, and submodules it contains;
- whether local work differs from its upstreams;
- whether dependencies and development tools appear usable;
- whether expensive build results exist and still correspond to current inputs;
- whether a Compose-based development environment is stopped, partially running, or ready;
- when source, build, test, and runtime activity was last observed; and
- whether the available evidence is sufficient for a deterministic operation.

Forcing those dimensions into service observation produces misleading conclusions. A Git
checkout does not become missing merely because no process with its project name is running.
Conversely, a running Compose container does not prove that the workspace is clean, current,
build-ready, or safe to modify.

The two domains may be related, but neither should contain the other. A workspace can develop
or launch services, and a service can be built from a workspace, without the workspace itself
being a service.

## 3. The governing data policy

The workspace domain should follow an explicit data maturity ladder:

```text
raw observation
    -> agent assessment and candidate facts
    -> deterministic derived fact
    -> promoted typed contract
    -> deterministic plan and operation
    -> fresh raw observation proving the result
```

Each transition has a different authority.

| Layer | Meaning | Typical writer | Authority |
|---|---|---|---|
| Raw observation | What a collector, command, or agent saw | nodeutils, bounded scripts, agent | Evidence, not intent |
| Agent assessment | A non-deterministic interpretation of evidence | agent | Advisory and revisable |
| Candidate fact | A proposed stable field, relationship, or policy | agent or analysis job | Awaiting contract adoption |
| Deterministic derived fact | A reproducible result from identified inputs and rules | Python/nctl | Operationally trustworthy while inputs remain valid |
| Typed desired contract | A declared value required by deterministic behavior | operator through the desired-state writer | Authoritative intent |
| Operation evidence | Plan, execution, and verification records | nctl, Ansible, scripts | Durable proof of a transition |

Raw data should be captured generously because its future uses are not yet known. Typed
columns should remain deliberately sparse. A field is not promoted merely because it is
frequently displayed or because an agent has inferred it with high confidence. Promotion is
justified when a deterministic validator, planner, renderer, or actuator has adopted a stable
meaning for it.

Raw evidence must remain available after promotion. A promoted fact is a projection from
evidence, not a replacement for that evidence. The projection should identify the observation
and rule version from which it was derived so that a later rule can recompute or reject it.

## 4. Proposed domain boundary

### 4.1 WorkspaceProject

`WorkspaceProject` represents the logical development project independently of any one PC or
checkout. `pj-voxel3dprint` is one such project even if it is checked out on several nodes or
has several working copies on one node.

Its initial typed identity should be minimal:

- stable slug;
- human-readable name; and
- declared lifecycle.

A canonical repository URL, project kind, manifest format, component list, build system, and
similar information can first live as raw observations or agent-proposed candidates. They
should become typed fields only when deterministic identity checking or actuation depends on
their precise semantics.

### 4.2 DesiredWorkspacePlacement

`DesiredWorkspacePlacement` expresses the operator's wish that a workspace be available in a
particular context on a particular desired node. It is the workspace equivalent of placement,
but it is not a subtype of `DesiredServicePlacement` and does not use a service deployment
profile.

The durable identity should distinguish multiple working copies of the same project. A useful
conceptual key is:

```text
(workspace_project, instance_name)
```

The smallest likely desired contract is:

- workspace project;
- desired node;
- instance name;
- desired presence; and
- local location, once deterministic discovery or actuation requires it.

User identity, path interpretation, checkout policy, branch policy, remote policy, build
policy, environment policy, and automatic-management mode should not automatically become
columns. They may begin in a raw or candidate policy document. Each should be promoted only
when a deterministic consumer can validate the complete contract and fail closed on ambiguity.

In particular, `active development` is not desired presence. A workspace may be intentionally
present but dormant, or actively used while temporarily dirty or broken. Declared lifecycle,
desired presence, and derived activity are three different dimensions.

### 4.3 WorkspaceObservation

`WorkspaceObservation` is the primary evidence surface. Observations should be append-oriented
and versioned rather than a single mutable JSON field on the placement. A new observation does
not rewrite what was previously seen.

Every observation needs a small typed envelope so it can be selected and trusted without
understanding its payload:

- workspace placement or discovery scope;
- desired/actual node identity where known;
- observation kind and schema version;
- collector identity and collector version;
- observed-at and received-at times;
- success, partial, or error status;
- payload digest and raw payload; and
- sensitivity/visibility classification where necessary.

The payload can initially contain whatever bounded information is useful, including:

- resolved paths and filesystem metadata;
- Git worktree, branch, HEAD, upstream, ahead/behind, dirty, staged, and untracked summaries;
- remote names and normalized URLs;
- submodule and nested-repository status;
- detected project manifests, lockfiles, build files, and Compose files;
- host-tool versions and relevant container images;
- build, test, and artifact evidence;
- Compose project/container state;
- recent activity timestamps available from trustworthy local evidence;
- incomplete scans, timeouts, permission failures, and truncation notices; and
- agent-supplied discoveries that are clearly marked as agent observations.

Raw does not mean unbounded. Collectors must still constrain paths, command time, payload size,
secret exposure, and filesystem traversal. Raw means schema-flexible evidence, not arbitrary
host exfiltration.

### 4.4 WorkspaceAssessment

Agent interpretation should be stored separately from both desired state and raw machine
observation. A `WorkspaceAssessment` can describe conclusions such as:

- this appears to be a superproject containing several cooperating repositories;
- development appears recent;
- a build is probably required before use;
- the detected remote is probably the intended origin;
- this Compose project seems to be a development runtime rather than a managed cluster service;
- these files likely define the authoritative build inputs; or
- a typed policy field may now be worth adopting.

An assessment should carry provenance, cited observation identifiers, model/agent identity,
creation time, confidence, limitations, and an optional expiry or supersession relation. It is
not silently converted into desired state and is never sufficient by itself to authorize a
destructive or external mutation.

Assessments may propose candidate fields and relationships. Repeated agreement among agents is
useful evidence for design evolution, but it is not the promotion criterion. The criterion is
adoption by a deterministic contract.

## 5. Deterministic projections without premature schema

Most useful workspace status can initially be calculated as a deterministic projection over
raw observations rather than persisted as first-class columns. Examples include:

- checkout present or missing;
- origin matches or differs from a supplied expected origin;
- upstream ahead/behind counts;
- clean, dirty, or observation-incomplete;
- submodule set complete or inconsistent;
- build evidence fresh, stale, missing, or indeterminate; and
- Compose runtime ready, stopped, degraded, or unknown.

Each projection must name:

- the exact observations consumed;
- the deterministic rule/profile version;
- the result and structured reasons;
- any missing or stale evidence; and
- the time at which the projection was computed.

This permits nctl and the UI to expose rich workspace status before committing to a large
relational schema. If a projection later becomes an input to rendering, reconciliation, or a
safety preflight, its input contract can then be promoted deliberately.

## 6. Build readiness is an evidence problem

`build_completed: true` is not a useful durable fact. A build is valid only relative to a
specific set of inputs and a build contract.

Raw build evidence should preserve as much as practical about:

- command/profile identity;
- source and dependency revisions;
- dirty-input treatment;
- lockfile and relevant configuration digests;
- toolchain or builder image identity;
- start, completion, exit, and verification results;
- produced artifact identities and locations; and
- logs or operation evidence references.

An agent may initially infer which inputs matter and propose a build fingerprint. Once a
deterministic build profile is adopted, a script can calculate an input fingerprint, compare it
with the fingerprint of the last verified successful build, and classify readiness
reproducibly.

```text
current deterministic input fingerprint
    == last verified successful build input fingerprint
    -> build ready

different, absent, or incompletely observed
    -> stale, missing, or unknown
```

An expensive background build should then be an explicit operation with durable evidence, not
a side effect of viewing workspace status and not an opaque update to a desired-state row.

## 7. Relationship to services and runtimes

The system should allow relationships between workspaces and services without merging their
models. Possible relationships include:

- a workspace develops or produces a logical service;
- a build artifact realizes a service version;
- a workspace runtime launches one or more observed containers;
- a workspace depends on an externally managed desired service; and
- a service deployment consumes an artifact produced outside the workspace node.

These relationships should also begin as observations or agent candidates unless a
deterministic consumer needs them. For example, discovering a Compose service does not
automatically create a `DesiredService`. Promotion requires an operator decision that the
container represents a cluster-level logical service with an intended lifecycle and placement.

This avoids both errors: treating every development container as infrastructure intent, and
treating a complete development workspace as though it were merely one running daemon.

## 8. Mixed agent/deterministic control loop

The intended collaboration can be expressed as the following control loop:

```text
bounded deterministic collection
    -> raw workspace observations
    -> agent exploration, correlation, and candidate proposal
    -> operator acceptance of desired intent or deterministic profile
    -> deterministic validation and dry plan
    -> explicit authorization where required
    -> Ansible/Python execution
    -> fresh bounded collection
    -> deterministic verification
    -> agent investigation only when evidence is ambiguous or convergence stops
```

The agent is well suited to discovering project structure, interpreting unfamiliar manifests,
forming hypotheses, selecting additional safe observations, explaining ambiguity, and proposing
new deterministic profiles.

Ansible, Python, and nctl are suited to enforcing adopted contracts, computing fingerprints,
checking exact paths and revisions, producing repeatable plans, applying known actions, and
verifying the result.

The authority boundary is therefore not "agent versus automation." It is evidence and proposal
versus adopted deterministic contract. An agent may run deterministic tools, but its free-form
conclusion remains advisory until it passes through the contract and authorization boundary.

## 9. Drift semantics

Workspace drift should be reported under its own target kind and vocabulary. It should not emit
`service_missing` or `service_not_running` for a checkout.

Initial workspace findings can distinguish at least:

- `workspace_observation_missing`;
- `workspace_observation_stale`;
- `workspace_checkout_missing`;
- `workspace_location_mismatch`;
- `workspace_identity_ambiguous`;
- `workspace_remote_mismatch`;
- `workspace_source_diverged`;
- `workspace_submodules_incomplete`;
- `workspace_build_missing`;
- `workspace_build_stale`;
- `workspace_runtime_not_ready`; and
- `workspace_state_unknown`.

Not every finding should be an error. Local commits, dirty files, or a branch different from an
upstream default may be normal active development and should generally be evidence or a review
condition until an explicit deterministic policy says otherwise. Missing an intentionally
present checkout is a stronger desired-versus-actual gap.

Derived activity should likewise be explanatory rather than authoritative:

```yaml
activity:
  classification: recently_active
  confidence: high
  reasons:
    - local_source_changes_observed
    - successful_build_observed
  evidence: [observation-id-1, observation-id-2]
```

It must not silently change the project's declared lifecycle or trigger a pull, reset, clean,
checkout, or rebuild.

## 10. Safety and evidence rules

Workspace automation introduces unusually high risk because uncommitted source, generated
assets, credentials, and long-running work may coexist in one tree. The following boundaries
should be part of the design from the beginning:

- Observation never implies permission to modify a workspace.
- Unknown, partial, stale, or conflicting evidence fails closed for mutation.
- Pull, checkout, reset, clean, submodule update, dependency upgrade, and artifact deletion are
  distinct actions rather than one generic "sync workspace" action.
- Dirty and untracked content is evidence to preserve, not drift to erase automatically.
- Plans identify the exact node, user context, resolved path, repositories, expected revisions,
  and actions.
- Deterministic preflight re-reads mutation-sensitive state immediately before execution.
- Post-operation success requires fresh observation of the state the action was meant to change.
- Raw payloads and operation evidence exclude secret contents even when their existence or digest
  is useful.

These rules still allow aggressive breaking changes to the management schema. Breaking the
catalog representation is different from destructively rewriting a developer's worktree.

## 11. Consequence for pj-voxel3dprint

`pj-voxel3dprint` should be represented as a `WorkspaceProject` with a desired workspace
placement on `agpc`. Its current service and service-placement representation can be removed
rather than retained as a compatibility alias.

The existing knowledge that it is a meta-level repository, is cloned under the user's projects
directory, contains cooperating repositories, uses host tools and Docker-based dependencies,
and can run through Compose is valuable initial raw evidence. It should not all be normalized
into columns immediately.

The first truthful system result would be closer to:

```text
workspace pj-voxel3dprint on agpc
  desired presence: present
  checkout observation: present
  source state: observed, with raw Git evidence
  project composition: agent-assessed, not yet a deterministic contract
  build readiness: unknown until a build profile is adopted
  runtime readiness: observed separately from service intent
```

This is more informative than `service_missing`, while honestly preserving what the system does
and does not yet know.

## 12. Deliberate non-goals of this proposal

This document does not prescribe migrations, API payloads, Django field definitions, collector
commands, Ansible roles, delivery phases, or a compatibility strategy. It also does not require
the first version to clone repositories, update worktrees, or run builds automatically.

The proposal establishes the domain and authority boundaries within which those later decisions
can be made:

1. workspace is a first-class domain, not a service subtype;
2. broad versioned raw evidence is retained;
3. agent conclusions remain attributed and advisory;
4. deterministic projections can mature before relational promotion;
5. only adopted deterministic inputs become typed desired contracts; and
6. every mutation is planned and verified through fresh evidence.

That boundary supports the intended hybrid system: exploratory and non-deterministic where the
project is still being understood, deterministic and auditable where the system has committed to
acting.
