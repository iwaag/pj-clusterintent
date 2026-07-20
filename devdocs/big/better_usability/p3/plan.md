# Better Usability Phase 3 Implementation Plan: Intent Is Live on Creation

Parent roadmap: [`../roadmap.md`](../roadmap.md), Phase 3. Field authority and ingress inventory:
[`../p0/field-classification.md`](../p0/field-classification.md), especially §2, §5, §7, and §8.
Prerequisites: Phase 1's target-local production findings and Phase 2's derived operational values
are deployed and verified by [`../p1/report1.7.md`](../p1/report1.7.md) and
[`../p2/report2.8.md`](../p2/report2.8.md).

## Goal

Make the ordinary single-operator action mean what it appears to mean: creating a desired node is
enough to put it in production scope. A new `DesiredNode` defaults to `active` through every
creation path, needs no operational-config row, and is eligible for the next reconcile. Preserve
the complete lifecycle vocabulary for deliberate staging, promotion, demotion, and a future
permissioned approval flow.

This phase changes only the node lifecycle default and adds an explicit lifecycle mutation
command. It does not make lifecycle automatic after creation, collapse the state machine, or
silently rewrite existing rows.

## Current state (after Phase 2, 2026-07-21)

- Phase 1 localizes production composition failures and reports active placements that are not
  applied because their node is outside production scope. A bad newly eligible node cannot abort
  healthy neighbors.
- Phase 2 removed the required `DesiredNodeOperationalConfig` runtime surface. Linux/macOS,
  endpoint, connection, policy, and safe optional values now come from one resolver; genuine
  exceptions use optional `DesiredNodeOperationalOverride` rows. Production report schema `2.0`
  exposes provenance.
- The live GraphQL cutover has 5 desired nodes, 5 endpoints, and 0 operational overrides. All 5
  nodes remain `planned`; Phase 2 deliberately did not mutate them.
- `DesiredNode.lifecycle` still defaults to `planned` at four independent code sites identified by
  Phase 0: the model, `DesiredHostQuickAddForm`,
  `create_desired_node_with_primary_endpoint()`, and the strict YAML loader. Regular ModelForm and
  REST creation inherit the model default when the field is omitted.
- Production eligibility remains explicit and unchanged: node lifecycle `approved` or `active`
  plus an eligible node type. `planned`, `deprecated`, and `retired` stay outside production
  inventory. Bootstrap/dnsmasq exports have their existing broader lifecycle behavior and are not
  changed by this phase.
- `DesiredService.lifecycle` defaults to `proposed`. It contributes
  `service_lifecycle_inactive` warning evidence but does not gate production composition;
  placement desired state and node eligibility do. Analysis-created services intentionally need
  review, while manual YAML/seed entries can already say `active`.
- nintent's deployed revision is `2ba5402`, nctl's is `54f7fda`, and the Phase 2 regression
  baselines are 89 nintent tests and 587 nctl tests.

## Decisions taken head-on

### 1. `DesiredNode.lifecycle` defaults to `active` everywhere, and explicit values always win

Change all four independent defaults together:

| Creation boundary | New behavior when `lifecycle` is omitted | Explicit `planned`/other state |
|---|---|---|
| `DesiredNode.lifecycle` model field | `active` | preserved |
| regular `DesiredNodeForm` | model-provided initial/default is `active` | preserved |
| `DesiredHostQuickAddForm` | visible initial choice is `active` | preserved |
| `create_desired_node_with_primary_endpoint()` | signature default is `active` | preserved |
| strict YAML `DesiredNodeEntry` + normalizer | omitted key normalizes to `active` | preserved |
| REST `POST /nodes/` | omitted field falls through to model default `active` | preserved |
| seed/example YAML | existing explicit values remain authoritative | preserved |

Do not hide the Quick Add lifecycle field. `active` is the convenient ordinary choice, while the
same form remains a discoverable way to deliberately register a staged `planned` node. Do not add
a save signal or post-create promotion hook: creation itself writes the final requested state.

`accepted_actual_types`, node type, endpoint derivation, placement state, service lifecycle, and
IP-range lifecycle keep their current defaults and semantics. In particular, this phase does not
broaden `PRODUCTION_ELIGIBLE_LIFECYCLES`; it changes what new node rows contain.

### 2. Keep every lifecycle state and provide one direct, idempotent nctl setter

Add:

```text
nctl lifecycle NODE STATE [--json] [--config PATH]
```

`NODE` is an exact desired-node slug. `STATE` is one of `planned`, `approved`, `active`,
`deprecated`, or `retired`. The command sets the requested state directly; it does not impose an
adjacency graph that the model does not enforce today. This supports promotion and demotion without
pretending that a permissioned approval workflow or audit policy already exists.

The command is itself an explicit mutation containing both target and destination, so it does not
add a second `--yes` ceremony. It is reversible by running the same command with another state.
Behavior is:

1. fetch desired state through GraphQL and resolve exactly one node by unique slug;
2. if its current state already equals `STATE`, return success with `changed=false` and make no
   REST write;
3. otherwise PATCH only `{"lifecycle": STATE}` to
   `/api/plugins/intent-catalog/nodes/{id}/`;
4. refetch through GraphQL and require the exact ID, slug, and lifecycle to match; and
5. return the before/after state and `changed=true` only after confirmation.

Reads therefore retain the project-wide GraphQL convention and the mutation uses the existing
nintent REST ViewSet. A partial-object PATCH avoids overwriting unrelated node edits. The pure
operation belongs in a focused module such as `nctl_core/lifecycle.py`; Typer only parses arguments,
calls it, renders the envelope, and selects an exit code.

Add closed output schema `nctl.lifecycle.v1`:

```json
{
  "schema": "nctl.lifecycle.v1",
  "generated_at": "...",
  "ok": true,
  "data": {
    "node_id": "...",
    "node_slug": "agpc",
    "previous_state": "planned",
    "requested_state": "active",
    "current_state": "active",
    "changed": true
  },
  "errors": []
}
```

Text output must be equally explicit (`agpc: planned -> active`) and distinguish the idempotent
case. Do not print the token, response body, or unrelated node fields.

### 3. Lifecycle mutation errors are command-scoped; no new drift code is introduced

This phase changes no composer failure and creates no new drift finding. A lifecycle change merely
makes the target eligible for the existing Phase 1/2 findings and reconcile classifications.

| Code | Scope | Evidence | Result |
|---|---|---|---|
| `unknown_node` | requested node only | requested slug | usage exit; no PATCH |
| `invalid_lifecycle` | command contract | requested state + allowed values | Typer usage exit; no fetch/PATCH |
| `lifecycle_update_rejected` | requested node only | slug, requested state, HTTP status; bounded safe API detail only | failed envelope; no success claim |
| `lifecycle_confirmation_mismatch` | requested node only | node ID/slug, requested vs. confirmed state | failed envelope; fail closed |
| existing Nautobot connection/auth/GraphQL errors | global command dependency | existing sanitized error contract | failed envelope; no write or no success claim |

No entry is added to `drift.registry` or `reconcile.classify.CODE_CLASSIFICATION`: these errors are
not desired-vs-actual facts and never enter reconcile planning. Tests must prove that a successful
promotion causes the next drift/render/reconcile to use existing target-local behavior, including
`active_placement_not_applied` disappearing when lifecycle was its only blocker and a Phase 2
derivation error blocking only that node when it is not.

### 4. Existing rows are reviewed with the command, never changed by migration

Migration `0012_*` is an `AlterField` changing the Django default only. It contains no `RunPython`,
bulk update, trigger, or lifecycle inference. All current `planned` rows remain `planned` after
migration.

After deployment, obtain the live node slug/lifecycle list read-only. Review each planned node and
run `nctl lifecycle <slug> active` only for nodes whose recorded intent should now take effect.
There is deliberately no Phase 3 bulk `--all` switch: five personal-cluster rows are small enough
to make the one-time decision explicit, and future large-scale lifecycle policy is out of scope.

Run `nctl drift --host <slug> --json` and a dry `nctl reconcile <slug> --json` after each promotion.
Only run `nctl reconcile <slug> --yes` when its derived endpoint/OS evidence and planned actions are
appropriate. Promotion is not reported as convergence and does not suppress missing actual/link/
interface evidence; it exposes those existing findings honestly.

### 5. `DesiredService.lifecycle` remains `proposed`

Record Phase 0's decision as final for this phase:

- production eligibility has no service-lifecycle gate;
- inactive service lifecycle produces a warning through service evaluation;
- analysis-created services are discoveries and should remain `proposed` until reviewed; and
- hand-declared seed/YAML services already use explicit `active` when intended.

Changing the default would therefore be cosmetic for actuation and would incorrectly approve
analysis-derived catalog rows. Do not alter the model, loader, importer hard-code, seed, output
schema, or reconcile classification for `DesiredService.lifecycle`.

### 6. This is a compatible two-component rollout, not a coordinated schema break

The nctl lifecycle command can run against the current Phase 2 nintent REST/GraphQL shape. The
nintent default change does not alter GraphQL fields, REST fields, choices, or existing values, and
old nctl revisions already accept `active`. No dual reader, API alias, compatibility shim, or
output-version bridge is needed.

Preferred deployment order:

1. land/test nctl command and documentation;
2. land the complete nintent default/migration/test batch;
3. have the user push nintent, then rebuild/restart Nautobot once;
4. verify migration/default behavior read-only; and
5. review/promote existing nodes using the deployed nctl command.

Rollback before existing-row promotion is: revert/rebuild nintent to restore the creation default
and revert nctl if desired. Rows created while Phase 3 was deployed retain their explicit `active`
value after rollback; they must be demoted intentionally if that is wanted. Rows already promoted
also remain active. This is data written by explicit user actions, not something a reverse
migration should guess away.

## Reader/writer and transition matrix

| Boundary | Phase 3 contract | Required change | Tests |
|---|---|---|---|
| nintent model/migration | new nodes default `active`; choices unchanged | `AlterField`, no data migration | model default + migration inspection |
| regular node form | new form shows/inherits `active`; all states editable | verify inherited initial; no hidden override | new-instance and explicit-planned form tests |
| Quick Host Add | visible default `active` | change `initial`; keep field | form cleaned-data + template/operation test |
| host creation operation | omitted lifecycle writes `active` | change signature default | default and explicit-planned atomic creation tests |
| strict YAML loader | omitted node lifecycle normalizes to `active` | dataclass + normalization fallback | omitted, each explicit state, invalid state |
| importer/Job | normalized value is upserted exactly | no new fallback in importer; update fixtures | create/update/idempotence tests |
| REST node create/update | omission inherits model; explicit state survives | serializer behavior audit, likely no runtime code | POST omission, PATCH only lifecycle, explicit planned |
| GraphQL/typed snapshot | lifecycle vocabulary/shape unchanged | no schema/model change | existing source tests plus command refetch fake |
| nctl lifecycle operation | exact-slug direct setter | new core module, envelope, render | idempotence, PATCH payload/path, refetch, errors |
| nctl CLI | thin command wrapper | add command/options/exit mapping | text/JSON/help/usage tests |
| production composer/render | approved/active eligibility unchanged | no implementation change | new default node enters eligible path |
| drift/dashboard/status | existing findings react to new value | no new code; refresh behavior only | lifecycle-only blocker disappears; local failures remain local |
| reconcile planner/executor | existing node-local classification and filtering | no automatic lifecycle action | mixed active-good/active-bad dry plan + host execution |
| services | `DesiredService.lifecycle=proposed` remains | decision/documentation only | pin default and warning behavior |
| seed/examples | explicit lifecycle remains authoritative | remove redundant node lifecycle only where teaching omission is useful; do not mechanically churn seed | loader parses seed; explicit values preserved |
| live existing rows | unchanged by migration | reviewed per-node setter | pre/post count and per-node confirmation |
| operator docs | creation is live unless explicitly staged | update current recipe and scenario note | command/doc grep + literal recipe review |

## Mandatory Phase 0 gate coverage

1. **Failure scope:** command validation/dependency failures are separated from a requested-node
   update failure. Making a node active exposes only existing Phase 1/2 structured target-local
   composition findings; shared profile/output corruption remains global.
2. **End-to-end findings:** no new drift code is created. Tests follow existing lifecycle and
   derivation findings through render, drift/dashboard effect, reconcile classification, and
   target filtering after a node changes state. Command errors stay in `nctl.lifecycle.v1` and
   cannot become unclassified reconcile diffs.
3. **Readers and writers:** the matrix covers model, regular/Quick Add forms, use-case operation,
   REST, YAML loader/import Job, seed/examples, GraphQL snapshot, composer, drift/dashboard,
   reconcile, docs, migrations, and live rows.
4. **Overrides and provenance:** an explicit lifecycle supplied through any ingress always wins;
   `planned` remains available. The default is discoverable in forms, command output, GraphQL,
   drift evidence, and docs. No hidden promotion hook exists.
5. **Schema/data transition:** Decision 4 specifies `AlterField` only, no existing-row update,
   reviewed promotion, deployment order, and rollback semantics. No nctl output schema other than
   the new command envelope changes.
6. **Isolation and orchestration:** Steps 3.4–3.7 cover pure operation behavior, REST confirmation,
   mixed good/bad active nodes, render/drift/reconcile, a literal new-node flow, and reviewed live
   transition.

## Step 3.1 — Freeze baselines and executable lifecycle contracts

1. Run the complete nintent and nctl suites and record exact counts in `p3/report3.1.md`.
2. Query live desired-node lifecycle counts read-only and confirm the expected five `planned` rows;
   record counts and slugs only, not tokens or unrestricted actual facts.
3. Re-run Phase 2 read-only production/drift checks to confirm target-local prerequisites remain
   deployed. Do not promote or actuate anything in this step.
4. Inventory lifecycle defaults/readers/writers with `rg`, starting from Phase 0 §7, and record any
   code path added since that audit.
5. Add contract tests for the exact CLI vocabulary, `nctl.lifecycle.v1` shape, idempotent no-write,
   one-field PATCH, and post-write confirmation before implementing the command.

## Step 3.2 — Add the nctl lifecycle operation and thin CLI command

1. Add typed lifecycle values and the closed data model/envelope builder in a focused core module.
2. Resolve nodes from `fetch_desired_snapshot()` by exact slug; do not accept fuzzy name/ID
   matches or arbitrary duplicates.
3. Return `changed=false` without a PATCH when current and requested states match.
4. PATCH exactly the lifecycle field through `NautobotClient.rest_patch()` and bound/sanitize API
   error detail.
5. Refetch through GraphQL and fail closed unless ID, slug, and requested state are confirmed.
6. Add deterministic text rendering and `--json`; map invalid state/unknown node to usage exit and
   transport/rejection/confirmation failures to failure exit.
7. Document the command in `nctl/README.md` and output format docs. State explicitly that it is a
   direct setter, not an approval engine and not part of `reconcile --yes`.

## Step 3.3 — Land the complete nintent default batch

In one nintent change:

1. change the model field default to `DesiredNode.LIFECYCLE_ACTIVE`;
2. change Quick Add initial and host-operation signature default to active;
3. change `DesiredNodeEntry` and YAML omission fallback to active;
4. generate migration `0012_*` containing only the lifecycle `AlterField` (apart from ordinary
   generated metadata); reject any accidental data operation;
5. verify regular ModelForm and REST omission inherit active, without adding duplicate defaults;
6. keep explicit planned/approved/deprecated/retired values untouched through all ingresses; and
7. update nintent README/CONCEPT current behavior, then run model/form/operation/loader/import/API
   tests and the complete suite.

Do not rebuild the running Nautobot until both component changes and cross-component tests are
ready, even though this rollout is compatible.

## Step 3.4 — Prove creation-path consistency and service non-change

Add a table-driven test matrix covering:

- direct model construction with omission and explicit `planned`;
- regular ModelForm creation with omission/initial and explicit `planned`;
- Quick Add default submission and deliberate staged submission;
- direct `create_desired_node_with_primary_endpoint()` omission/override;
- strict YAML omission, explicit values, invalid value, repeat import, and update of an existing
  row;
- REST POST omission, REST explicit planned, and lifecycle-only PATCH;
- seed files parsing without their explicit active values being overridden; and
- `DesiredService` model/manual-loader/analysis paths remaining `proposed` when omitted, plus the
  existing inactive-service warning.

Assert that no creation path manufactures an operational override. A minimal new active node with
one usable endpoint and valid fresh observation must reach production composition with schema 2.0
provenance.

## Step 3.5 — Test drift and reconcile isolation after lifecycle changes

1. Start with a planned node carrying an active placement and assert the existing
   `active_placement_not_applied` warning.
2. Change only lifecycle to active, rebuild drift, and assert that warning disappears when
   lifecycle was the sole reason for non-application.
3. Pair one newly active healthy node with one newly active node that has a missing/ambiguous
   endpoint or missing observation. Assert production includes the healthy node unchanged and
   reports the bad node with its existing structured code.
4. Assert cluster reconcile plans healthy-node actuation while pruning the locally blocked node;
   host-scoped dry plans remain scoped.
5. Assert a deliberate demotion back to planned removes the node from production, restores visible
   unapplied-placement evidence, and schedules no production actuation for it.
6. Assert lifecycle command failures never appear in drift records or
   `CODE_CLASSIFICATION` coverage.

## Step 3.6 — Update the current operator path without rewriting history

1. Update `nctl/docs/add-a-basic-service.md` so the target-node prerequisite says a newly created
   node is active by default, no lifecycle promotion is required, and no operational-config row is
   created. Keep `DesiredService.lifecycle=active` explicit because Decision 5 intentionally does
   not change that separate default.
2. Update the current bootstrap/register flow in `nctl/README.md` to begin with node + primary
   endpoint + placement, then use the ordinary reconcile path once observation exists.
3. Add a narrow supersession note to the scenario-1 node-registration section in
   `devdocs/small/basic_service/plan.md`: preserve the historical transcript, but point current
   readers to the Phase 3 live-on-creation behavior and explicit lifecycle command.
4. Update nintent's Quick Add/YAML examples to demonstrate omitted lifecycle for the normal path
   and explicit `planned` only for deliberate staging.
5. Run doc/code greps for obsolete claims that new nodes default planned, require manual promotion,
   or require an operational-config row. Historical phase reports may retain dated facts.

## Step 3.7 — Deploy once and perform the reviewed live transition

1. Confirm clean component worktrees, capture component revisions, and back up the Nautobot DB
   before migration.
2. Have the user push the nintent commit. Build/recreate web, worker, and scheduler once; run
   `showmigrations`, `migrate`, system/health checks, and `makemigrations --check --dry-run`.
3. Without creating data, verify through model metadata/API behavior that the server-side node
   default is active and the GraphQL/REST shape is unchanged.
4. Requery existing nodes and prove all pre-existing planned rows remained planned.
5. Review each row. Use `nctl lifecycle <slug> active --json` only for accepted promotions; record
   previous/current state and `changed`, not credentials or unrelated payloads.
6. For each promoted node, run host-scoped drift and dry reconcile. Apply only reviewed viable
   plans. Known unreachable hosts may remain active with visible local findings; do not claim them
   converged or demote them merely to make the dashboard green.
7. Exercise the default end to end with a disposable test row only if the operator authorizes
   live creation/deletion; otherwise prove it through the deployed model/serializer test plus the
   full local integration scenario. Do not silently create production intent for verification.
8. Record results, counts, migrations, revisions, and any intentionally unpromoted nodes in
   `p3/report3.7.md`; ensure no token, unrestricted facts, or generated live artifacts enter Git.

## Out of scope

- User/role permissions, separation of proposer and approver, audit-log policy, or signed approval.
- An enforced lifecycle transition graph or automatic progression after successful reconcile.
- Bulk lifecycle mutation or lifecycle changes inside reconcile planning/execution.
- Removing `planned`, `approved`, `deprecated`, or `retired`.
- Changing production eligibility from `approved`/`active` or changing bootstrap/IP-range
  lifecycle semantics.
- Changing `DesiredService.lifecycle`, placement desired-state defaults, or service analysis.
- Auto-promoting existing rows through migration.
- Phase 4's broader recipe/feedback consolidation and residual field-tier cleanup.

## Exit criteria

- Every DesiredNode creation ingress defaults omission to `active`, while every explicit lifecycle
  value is preserved.
- The migration changes only the future-row default and leaves all pre-existing rows untouched.
- `nctl lifecycle NODE STATE` supports all five states, is idempotent, PATCHes only lifecycle,
  confirms the write, and has stable text/JSON/error contracts.
- `DesiredService.lifecycle` remains `proposed`, with its current warning-only behavioral role
  recorded and tested.
- A common-case node created with intent + primary endpoint + active placement, without an
  operational override, enters schema-2.0 production output and is actionable on the next
  reconcile.
- A malformed newly active neighbor remains a structured target-local skip and cannot suppress
  healthy-node planning or execution.
- Current recipes contain no ordinary manual node-promotion or operational-config step; deliberate
  staging uses explicit `planned` and the lifecycle command.
- Existing live planned nodes are each explicitly promoted or explicitly left planned after review;
  none changes as a side effect of migration.
- Full nintent/nctl suites, migration checks, docs grep, and the literal orchestration matrix pass,
  with results recorded in phase reports.

## Suggested commit order

1. **nctl:** lifecycle core operation, envelope/rendering, CLI, and focused tests.
2. **nintent:** all node-default ingresses, `0012_*`, docs, and complete tests in one rebuild batch.
3. **nctl/docs + root devdocs:** current recipe/bootstrap updates, historical scenario supersession
   note, cross-component orchestration tests, and Phase 3 reports.
4. **Deployment report:** user push/rebuild, migration verification, reviewed per-node transition,
   and read-only/live-safe validation results.

Commits 1 and 2 may be developed in either order, but deploy only tested matching revisions.
Never split the four nintent defaults across deployed commits, and never bundle the reviewed live
promotions into the schema migration.
