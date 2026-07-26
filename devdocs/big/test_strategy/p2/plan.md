# Test Strategy Phase 2 Implementation Plan: Consolidate Deterministic Tier B and Adapter Tier C Coverage

Parent: [roadmap.md](../roadmap.md) — Phase 2.

Depends on: [Phase 0 final report](../p0/report.md), status **`complete`**, and [Phase 1 final
report](../p1/report.md), status **`complete`**.

Status: proposed; test-only consolidation with bounded local verification. It does not change
supported cluster behavior.

## 1. Goal

Express each deterministic rule once in a readable, diagnostic contract table, and retain only
the CLI, transport, and read-only presentation tests that detect failures unique to those adapters.

```text
repeated one-branch tests and duplicate adapter success matrices
  -> domain-owned deterministic tables with stable row IDs
  -> canonical transport fixtures per retained wire contract
  -> smoke-depth adapters with distinct failure coverage
  -> unchanged Tier A safety and transition proof
```

The Phase 0 inventory contains 1,028 Tier B and 50 Tier C primary contracts. Phase 1 removed the
29 superseded removal-surface assertions and consolidated their lasting contracts; it does not
authorize deletion of other old, long, or similar-looking tests. A lower test count is a
measurement, never a reason to merge or delete a proof.

## 2. Handoff and baseline

Use, but do not edit, the Phase 0 evidence:

```text
.local/test-strategy/p0/20260726T034839Z/
  test-ownership.tsv
  fixture-ownership.tsv
  external-boundaries.tsv
  transition-manifest.tsv
  measurements.tsv
  collected-cases.tsv
```

Relevant fixed findings:

- 22 of 23 retained transition risks are proven. The DesiredNode real-HTTP reset gap belongs to
  Phase 3 and must remain visible.
- Compute remains intentionally inert; its safety proof must remain.
- The root coordinated-breaking-change rule governs current consumers, while existing operation
  evidence remains readable through `nctl ops show`.
- Phase 1 measured nctl at **72 files / 900 definitions / 19,663 test lines** and nintent at
  **279 definitions / 5,129 test lines**. Re-measure; do not set a reduction target.
- The Nautobot/Postgres/Redis stack is persistent local scratch infrastructure. Reuse it and the
  named `test_nautobot` database during iteration. Recreate only the smallest incompatible or
  lifecycle-owned boundary.

Before edits, record a fresh root/submodule revision and dirty-state tuple. If a submodule moved
since Phase 1, compare changed tests/contracts with the manifest and record the delta before
proceeding.

## 3. Scope

### In scope

- Turn repeated Tier B normalization, lifecycle, closed-schema validation, candidate selection,
  placement, freshness, comparator, rendering, classification, and error-mapping cases into
  contract-owned tables.
- Consolidate nctl GraphQL/REST response builders by actual query or mutation contract.
- Reduce Tier C CLI cases to representative success/JSON/text smoke checks plus unique usage,
  approval, exit-code, formatting, and redaction checks.
- Preserve the complete read-only UI route/permission/no-POST manifest while removing only
  duplicate rendering coverage; retain one rendering proof per unique template/content semantic.
- Keep a golden only for a named downstream byte consumer and pair it with semantic assertions.
- Rename, split, or merge test files by lasting contract ownership; remove fixtures/helpers/
  snapshots/dependencies only after their final consumer is recorded.
- Run focused tests, each affected component's ordinary suite, and a local-source Nautobot gate
  whenever framework-owned nintent/nauto behavior changes.
- Produce a final Phase 2 report and before/after measurements.

### Out of scope

- Production-code refactors, except a minimal behavior-preserving seam required to test a real
  adapter boundary; record its contract and focused regression proof.
- Any change to desired/actual state, drift, planning, reconciliation, actuation, observation,
  durable evidence, GraphQL, REST, Job, SSH, Ansible, nodeutils, or Nautobot semantics.
- Weakening Tier A mutation, trust, authorization, scope, freshness, partial-progress, durable
  evidence, approval, redaction, or no-repeat tests.
- Phase 3 external conformance work, including real-HTTP DesiredNode linking, OpenSSH, Ansible,
  helper, dnsmasq, and IPAM multi-round proof.
- Compute realization, VM seed/cutover, public-network tests, CI, a generic framework, and
  property-testing dependencies without the decision in Section 8.
- External Job/REST writes, SSH, Ansible, nodeutils, ingest, reconcile apply, Proxmox actions,
  deployment, pushes, or disclosure of secrets/private content.

## 4. Consolidation rules

### 4.1 Primary ownership

Every conversion retains one primary tier, `contract_id`, unique defect, and normative owner from
the Phase 0 manifest. A table may combine cases only when they exercise the same deterministic
contract at the same layer. Keep separate tests where the distinction is any of:

- pure domain truth versus wire parsing/error translation;
- adapter option/confirmation/exit/rendering/redaction behavior versus core success;
- malformed, missing, duplicate, unauthorized, stale, contradictory, or wrong-identity input
  producing different safe diagnostics or action decisions;
- semantic deterministic output versus an exact downstream byte contract;
- unique template escaping/prose semantics versus route permission/no-mutation; or
- external implementation semantics versus a mock that agrees with local code.

Never merge by assertion count, source resemblance, or fixture-dictionary shape.

### 4.2 Table contract

Use the native framework idiom (`pytest.mark.parametrize`, `unittest.subTest`, or a small loop),
not a new abstraction. Every row gets a stable lowercase-kebab-case ID, such as
`missing-prefix-excluded`, `ambiguous-candidate-conflict`, or
`malformed-envelope-structured-error`.

Each table has a nearby docstring/comment naming:

1. `contract_id` and tier;
2. the authoritative function/model/serializer/renderer/boundary;
3. varied input dimensions;
4. expected canonical value, classification, error code, or exception; and
5. excluded Tier A or adapter-specific checks.

Each row asserts enough normalized output to diagnose a failure: decision/value and stable
diagnostic code where one exists. Freeze time, IDs, and ordering when they affect output. Do not
assert private call order, helper names, or intermediate layout unless that is a public diagnostic
boundary.

### 4.3 Tier A firewall

Before changing a file, identify adjacent Tier A cases from the manifest. Preserve their collected
IDs, or record exact one-to-one renamed/replaced IDs in the ledger. Do not hide action, scope,
preflight, write, observation, evidence, or no-repeat proof in a broad table. Empty paths remain
failed proofs, not candidates for simplification.

### 4.4 Adapter depth

| Surface | Retained checks |
|---|---|
| CLI family | one representative success and JSON/text smoke; unique usage, approval, exit, option-conflict, and redaction cases |
| GraphQL/REST | canonical successful envelope parsing plus distinct malformed/missing/duplicate/unauthorized/stale/contradictory translations |
| Read-only UI | complete route/permission/no-POST manifest plus representative rendering per unique template/content semantic |
| Golden artifact | named byte consumer, semantic renderer/classifier assertion, and exact byte/digest check |

An adapter must not replay the full core matrix just to restate returned fields. It also cannot be
removed if it is the only proof of malformed input, invocation, consumer-visible output, or safe
rendering.

## 5. Work plan

### Step 0 — Evidence, queue, and protected baseline

1. Create `.local/test-strategy/p2/<UTC timestamp>/` with `umask 077`.
2. Record revisions, tool versions, scratch prerequisite state, and Phase 0/1 evidence locations
   without reading `.local/secrets`.
3. Export all Tier B/C cases grouped by component, file, `contract_id`, fixture, operation kind,
   and external boundary. Mark adjacent Tier A cases as protected.
4. Add a proposed `consolidation-ledger.tsv` row before changing each group. A proposal without a
   unique defect and retained assertion is not authorized.
5. Run focused pre-change tests for each group; run its component baseline if it has not passed
   since Phase 1.

### Step 1 — Domain-owned Tier B tables

Confirm candidate groups against the ledger; none is a mandatory deletion quota.

| Component | Candidate families | Protected distinction |
|---|---|---|
| `nctl` | drift candidate evaluation/comparators, desired/actual normalization, dnsmasq ranges/records, production composition, reconcile classification, error mapping | manual review vs automatic action; DNS bytes vs semantics; executor/ledger Tier A paths |
| `nintent` | loaders, model/API validation, IPAM planning/classification, lifecycle normalization | transaction, permission, and mutation proof |
| `nauto` | Proxmox schema validation, IP candidate extraction, create/update/no-op selection | partial/invalid ingest and write evidence |
| `nodeutils` | report normalization, managed-file digest/path validation, helper mapping | real privileged-helper integration |
| `ansible_agdev` helper | deterministic argument/output rules | real Ansible semantics |

For every selected family, enumerate its input axes and distinct outcomes, convert same-layer
cases to stable-ID rows, retain explicit tests that are clearer than a row, add/retain semantic
invariants for a golden, run focused tests, and compare collected cases with the ledger. Split a
table if it would mix independent normalizations, authority sources, or output contracts.

### Step 2 — nctl transport fixtures

1. Inventory GraphQL/REST builders by exact query/mutation and envelope, not generic JSON shape.
2. Keep one small deterministic conformance fixture/factory per canonical contract, exposing only
   parser-relevant fields.
3. Preserve separately named malformed-envelope, missing-field, duplicate-identity,
   authorization, stale-observation, contradictory-response, and wrong-identity variants whenever
   they produce distinct diagnostics.
4. Keep transport parsing/error mapping separate from core drift/planner cases. Fixtures must not
   become a second schema implementation; assert required consumer fields in conformance tests.

### Step 3 — CLI adapter disposition

For every retained nctl command family (`status`/`drift`, `render`, `reconcile`, `ops`, and any
currently exposed family), record a disposition table with its public consumer, one success smoke,
unique adapter error/approval/exit/redaction checks, the core owner of normal success semantics,
and every merged/deleted/retained test ID. Keep dry-plan/`--yes` boundaries, confirmation,
non-zero exits, JSON envelope shape, and redaction where they apply. Those may be Tier A despite
using the CLI.

### Step 4 — Read-only UI presentation

Keep the canonical nintent route/permission/no-POST manifest complete: it is authority coverage,
not ordinary presentation duplication. Keep a rendering test for each unique template/content
semantic. Braindump and Alignment Review remain independently represented where autoescaping or
non-executable-prose behavior differs. Convert repeated static field/label/list cases to a
template-owned table only for one shared output rule. Do not replace runtime permission or HTTP
method checks with source inspection or snapshots.

### Step 5 — Goldens and ownership cleanup

For every retained golden/snapshot record: consumer, byte contract, deterministic inputs,
semantic companion assertion, and update procedure. Delete a golden only when no consumer reads
exact bytes. Keep byte/digest checks for externally consumed inventory, dnsmasq, event, or other
serialized artifacts where byte compatibility is contractual.

Remove a fixture/helper/dependency only after its final consumer is gone and the ledger records
`deleted_no_consumer`. Similar payloads that encode different authority, freshness, schema, or
transaction boundaries remain separate. Rename/move files only after direct references and
collection IDs are updated.

### Step 6 — Verification

Run focused tests after every conversion and each affected component's ordinary suite when its
workstream completes. If nintent/nauto work uses Django/Nautobot semantics, run the changed local
source through `nautobot-server test` in the existing scratch stack and named `test_nautobot`
database, using `--keepdb` during iteration. Record a source-resolution check proving that the
edited local package, not the installed package, ran.

Recreate a test database only for incompatible schema, migration/lifecycle coverage, or final
clean verification. Repair stale scratch state at that named boundary and rerun the gate; it does
not block unrelated offline work.

### Step 7 — Final ledger reconciliation

Re-run the Phase 0 measurement method for files, definitions, collected cases, Python lines,
runtimes, slow tests, skips/xfails, and fixture/mock concentration. Verify each protected Tier A
case is collected and has unchanged positive evidence or an exact replacement. Check ledger rows
against focused/component results; search for stale names, duplicate builders, public-network
calls, secret literals, and current references to removed helpers. Publish `report.md` with
revisions, commands, conversions, retained adapter/golden proof, measurements, deviations, and
Phase 3 work explicitly left untouched.

## 6. Required private evidence

```text
.local/test-strategy/p2/<UTC timestamp>/
  README.txt
  revisions-start.tsv
  revisions-end.tsv
  commands.jsonl
  phase0-phase1-delta.tsv
  tier-bc-work-queue.tsv
  consolidation-ledger.tsv
  protected-tier-a.tsv
  contract-table-map.tsv
  transport-fixture-map.tsv
  cli-disposition.tsv
  ui-render-manifest.tsv
  golden-consumers.tsv
  fixture-consumers.tsv
  focused-results.tsv
  component-results.tsv
  nautobot-runtime-result.tsv
  scratch-state-before.tsv
  scratch-state-after.tsv
  measurements-before.tsv
  measurements-after.tsv
  collection-before.tsv
  collection-after.tsv
  searches.tsv
  skips-xfails.tsv
  findings.tsv
```

Use restrictive permissions. Successful-run records need only command, revision, duration, and
result; retain full raw output only for failures or needed framework/external-boundary proof.
Tracked reports contain sanitized public facts only.

`consolidation-ledger.tsv` columns are:

```text
old_test_id
old_contract_id
tier
unique_defect
old_owner
action
new_test_id_or_table_row
retained_assertion
adapter_or_domain_reason
protected_tier_a_neighbor
focused_command
focused_result
component_result
```

Allowed actions are `retained`, `table_row`, `merged_same_contract`, `moved_owner`, and
`deleted_no_consumer`. The last is only valid when the final active consumer is named; no retained
behavior assertion may use it. `contract-table-map.tsv` records table, tier, contract, row ID,
input class, canonical expected result, diagnostic/error code, and excluded Tier A/adapter checks.

## 7. Ordinary verification commands

```bash
cd nctl && uv run pytest -q --durations=20
cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests
cd nauto && python3 -m unittest discover -s tests
cd nodeutils && uv run pytest -q --durations=20
cd ansible_agdev && python3 -m unittest discover -s roles/nodeutils_pvesh_helper/tests
```

Use changed-file commands first. For framework-owned changes, the local-source Nautobot runtime
gate is required in addition to the fast command. These offline/scratch checks do not replace the
Phase 3 OpenSSH, Ansible, real-HTTP, helper, or multi-round transition gates.

## 8. Stop conditions and property-testing decision

Stop only the affected workstream and record a finding if a proposed merge crosses contract IDs,
Tier A boundaries, or normative layers; a table cannot state stable output without hiding a
behavior choice; a retained adapter/golden would lose its only unique proof; fixtures differ in
authority/trust/freshness/transaction/schema semantics; external behavior needs a Phase 3 gate;
Tier A collection or positive evidence changes; a minimal seam alters public behavior; the runtime
gate imports installed rather than local source; or an action could touch an external/unknown
target or secret-bearing data.

When behavior is authoritative and a bounded test-only correction is clear, make it and rerun the
highest relevant gate. Create a separate plan for a semantic choice, a new external mutation
boundary, or material scope expansion. Preserve production defects as failing reproducers.

Recoverable scratch failures are repaired and rerun at the smallest owned boundary. Do not call
the phase blocked because `test_nautobot` has stale schema or a temporary fixture needs cleanup.

Do not add Hypothesis or another property-testing dependency by default. It is permitted only if
the ledger identifies a concrete current generator that is clearer than a finite table, preserves
explicit diagnostic regression rows, has deterministic bounded runtime, and records dependency
impact before project metadata changes.

## 9. Exit criteria

Phase 2 is complete only if:

- Tier B rules are readable tables or have an explicit reason to remain standalone;
- every table row has stable ID, expected normalized result, and applicable diagnostic;
- retained GraphQL/REST fixtures have one canonical contract with distinct safe failures intact;
- CLI families retain smoke depth and unique authority/usage/exit/JSON/text/redaction checks,
  without replaying core matrices;
- UI retains the complete route/permission/no-POST manifest and unique-template rendering,
  including separate Braindump/Alignment Review semantics;
- every golden has a named consumer and semantic companion assertion;
- every merge/deletion is ledger-backed and no Tier A proof is hidden, weakened, or uncollected;
- focused and component gates pass, plus required local-source Nautobot gates;
- before/after measurement, skips, runtime, slow tests, fixture concentration, and deviations are
  recorded without arbitrary numeric targets; and
- `devdocs/big/test_strategy/p2/report.md` truthfully reports `complete`, `partially complete`,
  or `blocked` under `README_DEV.md` completion language.

## 10. Expected tracked changes

Tracked changes are limited to contract-owned tests, their affected final-consumer fixtures,
helpers, goldens, and narrowly related test documentation, this plan, and `p2/report.md`.
Historical reports, generated caches, `build/`, `__pycache__/`, private `.local/` evidence, and
installed packages are not tracked Phase 2 edits.
