# Retire core Phase 1 — implementation plan: persist explicit Desired absence

Parent: [roadmap.md](../roadmap.md) — Phase 1. Predecessor: [p0/report.md](../p0/report.md).

Status: proposed. One nintent schema change, one migration, one contract/fixture change, one nctl
read change, one scratch deployment. No Proxmox call, no drift semantics, no actuation.

## 1. Goal

Make `desired_presence` a first-class, writable, readable field so that an atomic desired-state batch
can record "this node is retired and its compute resource should not exist", and nothing else in the
system changes behavior yet.

```text
current
  DesiredComputeInstance has no presence field; deletion intent cannot be expressed at all

after Phase 1
  desired_presence = present | absent, default present, on every row
  + one atomic batch can set DesiredNode.lifecycle=retired + instance desired_presence=absent
  + absent with a non-retired effective lifecycle is rejected by the ordinary write path
  + nctl's typed snapshot carries the field and shows it in ordinary compute evidence
  + zero new drift codes, zero classification changes, zero action changes
```

Phases 2–4 consume the field. Phase 1 must not anticipate them: no destroy code, no `--allow-destroy`,
no VM presence field, no planner change.

## 2. Frozen inputs from Phase 0

| Input | Value |
|---|---|
| field | `DesiredComputeInstance.desired_presence`, `present` \| `absent`, default `present` |
| semantics | current intent only; omission/unmanaged/observation failure never imply `absent` |
| removal declaration | one atomic batch: node → `retired`, instance → `absent`; platform stays active |
| required projections | model + migration, batch `_FIELDS`, GraphQL, nctl `DESIRED_QUERY`, nctl `DesiredComputeInstance`, compute conformance fixture, ordinary compute JSON/text evidence |
| explicitly excluded | timestamp, reason, schedule, approval, provenance, retention, protection, case fields |
| validation | simplest boundary that rejects `absent` whose effective lifecycle is not `retired`; no workflow or approval model |

## 3. Findings that shape the plan

Measured on the checked-out tree (superproject `eb42033`, nintent `d388049`, nctl `df170b8`) on
2026-07-30.

**F1 — the write path is narrow.** `nautobot_intent_catalog/views.py` exposes compute instances
read-only (`ObjectListView`/`ObjectView`); there is no form. The only writers are the batch service
(`batch.py`) and direct ORM/model `clean()`. So one entry in `_FIELDS` plus one rule in the shared
topology validator covers every supported write.

**F2 — the shared validator already exists and is already called from every write path.**
`validate_compute_instance_topology()` ([models.py:534](../../../../../../nintent/nautobot_intent_catalog/models.py#L534))
is documented as the service/model boundary validator and is invoked from
`DesiredComputeInstance.clean()`. It computes `effective_lifecycle(node, platform)` and then returns
early for non-actionable lifecycles. The presence rule belongs *before* that early return.

**F3 — batch ordering already makes the atomic retire+absent document safe.** `KIND_ORDER`
([batch.py:10](../../../../../../nintent/nautobot_intent_catalog/batch.py#L10)) applies
`desired_node` before `desired_compute_instance`, and `apply_batch` runs `full_clean()` per row
inside one `transaction.atomic()`. The node is therefore already `retired` when the instance
validates. No ordering work is needed.

**F4 — preview cannot see this rule.** `plan_batch()` never calls `full_clean()`; it only diffs
values. A document that sets `absent` without retiring the node previews as a normal `update` and
fails at apply with `transaction.status = rolled_back`. This matches every other `clean()`-enforced
rule in the app. Accept it; state it in the report rather than adding a second validator to the
planner.

**F5 — the field is not enforced on later node-lifecycle changes.** Retiring or un-retiring a
`DesiredNode` does not re-run its instance's `clean()`, so an existing `absent` instance can end up
under a non-retired node. Phase 1 enforces the rule on instance writes only. Phase 3 must treat
`absent` + non-retired effective lifecycle as an ordinary drift finding, not as an impossible state
and not as a crash. Record this as a Phase 3 handoff item.

**F6 — GraphQL needs no nintent change.** `DesiredComputeInstance` carries
`@extras_features("graphql")`, so Nautobot generates the field into the schema automatically. Only
nctl's `DESIRED_QUERY` selection set must be extended
([sources/desired.py:162](../../../../../../nctl/src/nctl_core/sources/desired.py#L162)).

## 4. Design decisions

### 4.1 Contract ownership

`compute_contract.py` is the semantic owner (roadmap: nctl must not add a second validator). Add
there, and mirror in `nctl/src/nctl_core/compute/contract.py`:

- `DESIRED_PRESENCE_PRESENT` / `DESIRED_PRESENCE_ABSENT` / `DESIRED_PRESENCE_CHOICES`;
- `validate_desired_presence(value, *, path="desired_presence")` — same `ComputeContractError` shape
  as `validate_power_state`; and
- one pure predicate pairing presence with an already-computed effective lifecycle, e.g.
  `desired_presence_requires_retired(presence, effective) -> bool`. Keep it pure and
  lifecycle-agnostic beyond the one rule: only `absent` constrains lifecycle; `retired` + `present`
  stays legal (roadmap semantics table row 3).

Add the new symbols to `compute_conformance.py` (`CONSTANTS`, `PUBLIC_SYMBOLS`, `CASES`) with valid,
invalid, and full presence × lifecycle cases, then regenerate
`nctl/tests/fixtures/compute_conformance.json` with
`devtests/test_strategy/generate_compute_conformance.py`.

### 4.2 nintent

- `models.py`: one `CharField(max_length=16, choices=..., default="present")` next to
  `desired_power_state`; validate it in `clean()` alongside the other contract fields.
- migration `0021_*` (latest is `0020_alter_intentsource_options`): add the column with the default so
  existing rows become `present`. A `CheckConstraint` on the value is optional — the choices plus
  `clean()` already cover the supported writers; add it only if it costs nothing.
- `validate_compute_instance_topology()`: reject `absent` unless the effective lifecycle is
  `retired`, before the `is_actionable_lifecycle` early return, using the §4.1 predicate. The error
  must name the field and both values so an operator sees why one atomic batch is required.
- `batch.py`: add `desired_presence` to `_FIELDS["desired_compute_instance"]`. Do **not** add it to
  `_CREATE_REQUIRED` — the default is the contract.
- Read surfaces (`tables.py`, `filters.py`, `desiredcomputeinstance.html`,
  `desiredcomputeplatform.html`): adding the column is cheap and makes the state visible; treat it as
  recommended, not required, and update `test_ui_contract.py`/`test_templates.py` if you do.
- Braindump models, API, and status behavior: untouched.

### 4.3 nctl

- `compute/model.py`: `desired_presence: str = "present"` on `DesiredComputeInstance`.
- `compute/collection.py::_build_compute_instance`: validate through the mirrored contract. An
  invalid value becomes a target-scoped `DesiredSourceIssue` (the row is dropped, the rest of the
  snapshot survives) exactly like `desired_power_state` today — not an exception out of
  `fetch_desired_snapshot()`.
- `sources/desired.py`: add `desired_presence` to the `desired_compute_instances` selection.
- `drift/compute_evaluation.py::_summary` ([line 132](../../../../../../nctl/src/nctl_core/drift/compute_evaluation.py#L132)):
  add `desired_presence` (and the effective lifecycle, if it is already at hand) to the desired side
  of `compute_realization_summary`. This is the "ordinary JSON/text evidence" projection p0 requires,
  and it is the whole of Phase 1's drift change. No new code, no severity change, no classification
  entry, no planner change.

### 4.4 Live proof target

Prove preview/apply on a **disposable desired node** in the scratch Nautobot, not on `agfixture`.
`agfixture` must stay `approved/present` because that is Phase 5's recorded acceptance start state.
If you do write it, restore it through the same writer and say so in the report.

## 5. Steps

Merge or split freely; the only ordering constraints are that the contract lands before the fixture
is regenerated, and that the deployment happens before the live preview/apply proof.

### Step 0 — Baseline

Record the revision tuple, the installed nintent/nauto commits inside the running containers, the
applied migration state, and `nctl drift --json` for the current converged state. This is the
before-picture that Step 4 must show as unchanged apart from the new field.

*Exit:* baseline recorded; any difference from p0's read-only inspection explained.

### Step 1 — Contract and fixture

Implement §4.1 in nintent, mirror it in nctl, extend the conformance cases, regenerate the fixture.

*Exit:* the compute conformance gate and `nctl/tests/test_compute_conformance.py` both pass with the
new cases; the two implementations of the rule are provably identical through the fixture.

### Step 2 — nintent persistence and validation

Implement §4.2. Tests (Nautobot runtime tier): default `present` on create; `absent` + `retired`
accepted; `absent` + active/approved/planned/deprecated rejected; one atomic batch document that
retires the node and sets `absent` commits (F3); the same document without the retirement rolls back
(F4); an unknown value fails as an ordinary choice/contract error; existing rows are `present` after
migration.

*Exit:* every listed case is a passing test; `present` compute workflows are byte-identically
unaffected.

### Step 3 — nctl read and evidence

Implement §4.3. Tests: a GraphQL row round-trips into the typed instance; a missing field defaults to
`present`; an invalid value yields a target-scoped source issue and drops only that row; the compute
realization summary carries the field; and existing compute drift codes, severities, classifications,
and plans are unchanged.

*Exit:* `nctl` ordinary suite passes; no new drift code and no action exists anywhere in the tree.

### Step 4 — Deploy and prove the write live

nintent is installed into the image from GitHub (`devenv/nautobot/Dockerfile`), so: commit → ask the
operator to push → `docker compose build --no-cache` → restart web/worker/scheduler →
`nautobot-server migrate`. Verify the resolved nintent commit from the build log/`build_info.json`
before trusting the container — a cached layer has silently carried a stale plugin commit before.

Then, against the scratch stack with a disposable node (§4.4):

1. `nctl desired apply -f <doc>` preview of the atomic `retired + absent` document;
2. the same document with `--yes`; confirm `transaction.status = committed`;
3. re-read through GraphQL/`nctl drift --json` and confirm `desired_presence = absent`;
4. the invalid variant (absent without retirement) applies to nothing and reports `rolled_back`; and
5. `nctl drift` for the whole cluster is otherwise identical to Step 0.

*Exit:* the field is writable and readable end to end through the canonical path, and no unrelated
drift moved.

### Step 5 — Gates and report

Run and state case counts for: nintent Django-free unittest (14 expected skips), compute conformance,
nctl ordinary pytest, and the Nautobot runtime gate with `--clean` (a new migration is in scope).
Write `p1/report.md` with the revision tuple, the decisions above, F4 and F5 as named accepted
limits, the Phase 3 handoff item, gate results, and one precise status.

*Exit:* one status of `complete`, `partially complete`, `implemented, not deployed`, or `blocked`,
with every omitted check visible.

## 6. Exit criteria

1. `desired_presence` exists on every `DesiredComputeInstance` row, defaulting to `present`, with the
   migration applied to the scratch database.
2. One atomic batch records `retired + absent` through the canonical writer and commits; the same
   document without the retirement rolls back.
3. Invalid values fail as ordinary contract errors on the write path and as target-scoped source
   issues on the read path.
4. nctl's typed snapshot and the ordinary compute summary carry the field.
5. The single owner still owns the rule: the conformance fixture proves nintent and nctl agree.
6. Existing `present` compute behavior — drift codes, classifications, plans, renders — is unchanged.
7. No destroy code, action, CLI option, or VM presence field was added.

## 7. Boundaries

Prohibitions, minimal:

1. **No Proxmox call and no actuation of any kind.** Phase 1 is persistence and reads.
2. **No second validator.** The presence rule has exactly one implementation in the contract owner,
   mirrored only through the generated fixture.
3. **No push.** Local commits are yours; pushing nintent/nctl stays the operator's step (and is the
   one thing Step 4 has to wait for).
4. **No Phase 2–4 surface.** No `proxmox_presence` on VirtualMachine, no destroy code or handler, no
   `--allow-destroy`.

Everything else is the implementer's call: module layout, field/constant/error spellings, whether the
predicate lives in the contract or the validator, constraint vs. choices-only enforcement, test
structure, commit granularity, step count, and whether the UI read surfaces change. Scratch Nautobot
migrations, rebuilds, restarts, test rows, and disposable desired rows need no approval. Ask the
operator only for the nintent push and for anything that writes `agfixture`.
