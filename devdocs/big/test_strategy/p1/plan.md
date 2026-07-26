# Test Strategy Phase 1 Implementation Plan: Remove Orphan and Superseded Contract Coverage

Parent: [roadmap.md](../roadmap.md) — Phase 1.

Depends on: [Phase 0 final report](../p0/report.md), status **`complete`**.

Status: proposed; test/documentation cleanup with offline and disposable-environment verification.

## 1. Goal

Remove or replace only test coverage whose sole consumer has already been removed or whose
compatibility rule was explicitly superseded in Phase 0.

This phase is a contract-ownership cleanup. It must make the retained suite easier to read without
changing desired-state, actual-state, drift, planning, reconciliation, actuation, observation,
evidence, or presentation behavior.

The intended transition is:

```text
Phase 0 evidence
  29 nintent tests marked replace
  + one historical removal-owned test module
  + additive-forever compatibility wording and broad "frozen floor" snapshots
  + five nctl test filenames owned by historical phase names
  + zero confirmed active orphan references

to
  canonical model/migration, API, and UI owners for the lasting removal contracts
  + current-consumer compatibility contracts governed by coordinated rollouts
  + risk/domain-owned nctl test filenames
  + no removed-only tracked fixture, helper, dependency, snapshot, or current documentation
  + a deletion ledger proving every removed assertion has a removed consumer or a visible owner
```

A lower line or case count is diagnostic evidence, not the authorization for a deletion.

## 2. Phase 0 handoff and planning-time snapshot

Phase 0 established the following facts:

- all 1,377 statically declared tests have a tier, contract, environment, unique defect, and
  preliminary disposition;
- 1,348 tests are marked `keep` and 29 tests are marked `replace`;
- all 29 `replace` entries are in
  `nintent/nautobot_intent_catalog/tests/test_remove_unused_surfaces.py`;
- no active orphan was confirmed;
- 22 of 23 transition risks are proven, while the DesiredNode real-HTTP reset gap remains assigned
  to Phase 3;
- compute remains intentionally inert and its safety test must remain;
- the coordinated breaking-change policy in the root `README_DEV.md` supersedes the old
  deprecation-window policy; and
- historical operation evidence must remain readable through `nctl ops show`.

The authoritative private Phase 0 evidence is:

```text
.local/test-strategy/p0/20260726T034839Z/
  test-ownership.tsv
  fixture-ownership.tsv
  reference-classification.tsv
  compatibility-consumers.tsv
  compatibility-decision.md
  transition-manifest.tsv
  measurements.tsv
  run-results.tsv
```

Do not edit those files. Phase 1 may read and reference them but must write new raw evidence under a
new Phase 1 directory.

Planning-time revisions on 2026-07-26 are:

| Repository | Revision | State |
|---|---|---|
| superproject | `e3b144da6cdfe5fab0230018cdc43a5f41c5c9e8` | clean |
| `nctl` | `e813f6963afc17af74c48aae5660461d3f10498a` | clean |
| `nintent` | `e8732f17ae35d8c72d4d593e8d7311bd234fc0bf` | clean |
| `nauto` | `1c78af8bdbfc69cafdc293b4082f866de9f271b0` | clean |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean |
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | clean |

The executor must freeze a fresh tuple before editing. If any submodule moved, compare its tests
and contracts with the Phase 0 manifests and record the delta before applying this plan.

## 3. Scope

### 3.1 In scope

- consolidate the lasting assertions in
  `nintent/nautobot_intent_catalog/tests/test_remove_unused_surfaces.py` into canonical
  model/migration, API, and UI owners;
- delete that historical removal-owned test module after every retained assertion has a new owner
  or a documented duplicate owner;
- preserve Django migration history, including migrations `0009` and `0016`, and prove the current
  migrated model state;
- revise `nctl/docs/compatibility.md` and directly linked current documentation to use the Phase 0
  coordinated-rollout decision;
- replace additive-forever or deprecation-window snapshot semantics with contracts tied to named
  current consumers and durable historical readers;
- rename the five currently tracked nctl test modules whose filenames describe a historical phase
  instead of their lasting risk;
- update stale phase-oriented module docstrings and direct test references while retaining useful
  historical provenance where it explains a defect;
- conditionally remove a tracked fixture, helper, dependency, generated snapshot, or current
  document only when its last active consumer is proven removed;
- run focused, ordinary, and disposable Nautobot verification; and
- record before/after counts using the Phase 0 measurement method.

### 3.2 Out of scope

- production-code changes made merely to simplify or merge tests;
- changes to desired, actual, GraphQL, REST, Job, drift, planner, reconcile, SSH, Ansible,
  nodeutils, nauto, or durable evidence semantics;
- new migrations, migration squashing, or deletion of historical migration files;
- closing the Phase 3 DesiredNode real-HTTP reset gap;
- consolidating broad Tier B truth tables or CLI Tier C matrices assigned to Phase 2;
- adding the OpenSSH, Ansible, Nautobot real-HTTP, or helper conformance gates assigned to Phase 3;
- compute drift, compute planning, provider action, VM seeding, or first realization;
- running a live Job, REST mutation, SSH enrollment, Ansible playbook, nodeutils collection,
  ingest, reconcile apply, or Proxmox mutation;
- rebuilding or restarting the long-running Nautobot web, worker, or scheduler services;
- reading `.local/secrets`, printing tokens, or copying private Braindump or Alignment Review
  prose into evidence; and
- pushing commits. Per `.local/localenv_memo.md`, a future nintent deployment requires a user
  push and image rebuild; this test-only phase does not perform that deployment.

## 4. Safety, authority, and stop conditions

### 4.1 Allowed actions

- read tracked source, tests, documentation, Git metadata, and sanitized Phase 0 evidence;
- create private Phase 1 inventories and logs with restrictive permissions;
- edit and delete tracked tests and current documentation within the exact scope above;
- use `git mv` for risk-owned test renames;
- run offline component suites;
- run the nintent App suite against a disposable Django test database using local Phase 1 test
  sources; and
- inspect the local Nautobot container/image and migration state read-only to establish
  prerequisites.

### 4.2 Prohibited actions

- do not delete a test because it is long, old, phase-named, mocked, or slow;
- do not delete a production-bug reproducer or Tier A boundary unless its unique defect is
  visibly preserved by the named replacement;
- do not delete or weaken the compute-inert test;
- do not convert an exact failure into a broader smoke assertion;
- do not preserve old and new duplicate tests as rollback;
- do not treat a substring match such as `serve` inside `server` or `observe` as a removed-surface
  reference;
- do not edit generated mirrors under `build/` or `__pycache__/` as though they were tracked source;
- do not use the installed nintent package's unchanged tests as proof for locally edited tests;
- do not run ordinary tests against the public internet; and
- do not expose `.local/secrets`, API tokens, raw SSH keys, or private user prose in commands,
  logs, fixtures, or reports.

### 4.3 Stop conditions

Stop the affected workstream and record a finding if any of the following occurs:

1. a supposedly removed surface has a current production implementation or named active consumer;
2. a proposed deletion maps to a retained mutation, authorization, evidence, migration, trust,
   exact-scope, freshness, or non-repetition contract;
3. the local replacement cannot state the unique defect preserved from the old test;
4. nctl compute drift, planning, or action dispatch has become active under another roadmap;
5. the compatibility audit finds an active or historical reader not represented in the Phase 0
   consumer matrix;
6. a compatibility change would make an existing operation log unreadable through `nctl ops show`;
7. a test cleanup exposes a production defect or requires a production seam;
8. the disposable Nautobot gate runs the installed old tests instead of the local Phase 1 tests;
9. a required Tier A test disappears from collection or changes its positive evidence; or
10. a disposable test leaves a container, process, database, network, volume, or synthetic row.

A production defect found here remains a failing reproducer. Fix it only under a separate bounded
plan unless it is an unambiguous correction to an already-authoritative contract and separately
approved.

## 5. Required evidence

Create a private directory such as:

```text
.local/test-strategy/p1/<UTC timestamp>/
  README.txt
  revisions-start.tsv
  revisions-end.tsv
  commands.jsonl
  baseline-collection.tsv
  replacement-ledger.tsv
  removed-surface-search.tsv
  compatibility-consumers.tsv
  historical-rename-map.tsv
  focused-results.tsv
  full-results.tsv
  measurements-before.tsv
  measurements-after.tsv
  leak-check-before.tsv
  leak-check-after.tsv
  findings.tsv
```

Use `umask 077`. Raw logs may be stored beside these summaries when useful, but tracked reports
must contain only sanitized counts, test IDs, revisions, timings, public schema facts, and
digests.

`replacement-ledger.tsv` must contain at least:

```text
old_test_id
old_contract_id
tier
unique_defect
action
removed_consumer_or_superseding_decision
replacement_test_id
positive_evidence
focused_command
result
```

Allowed `action` values are:

- `moved`: the same unique assertion now lives under a canonical owner;
- `merged`: several same-layer cases are represented by one readable matrix;
- `covered`: an already-existing canonical test proves the same defect;
- `deleted_removed_consumer`: no supported consumer remains; or
- `retained`: Phase 0's preliminary replacement decision was too broad and the assertion stays.

Every deleted test or helper needs one ledger row. A blank replacement is allowed only for
`deleted_removed_consumer`, with the removed consumer named.

## 6. Target manifest

### 6.1 nintent removal-contract consolidation

The 29 Phase 0 `replace` entries are currently all in:

```text
nintent/nautobot_intent_catalog/tests/test_remove_unused_surfaces.py
```

Use these final owners:

| Lasting contract | Final owner | Required treatment |
|---|---|---|
| `DesiredNode` and `DesiredService` no longer expose reconciliation cache fields/constants | `test_model_contract.py` | one runtime matrix over both models and both removed fields; keep diagnostic subtests |
| migration history introduced and then removed the cache without rewriting history | `test_model_contract.py` plus the real App suite | inspect the migration graph/project states and prove the full disposable migration chain applies |
| removed filter fields, table columns/helpers, dashboard route/path, navigation entries, and app setting | `test_ui_contract.py` | add only missing rows to the existing route/navigation/no-mutation manifests; retain one canonical absence matrix |
| retained list/detail UI, compute UI, Braindump UI, and navigation still work | `test_ui_contract.py` | use the existing complete retained route and runtime render matrices; do not keep separate removal-phase smoke tests |
| REST responses omit removed fields and retained PATCH still works | `test_api_contract.py` | fold field absence into the exact response-field contract and use the existing PATCH authority test |
| old GraphQL fields fail validation while retained roots return data | `test_api_contract.py` | add removed fields to one schema-validation table and rely on the retained-root runtime matrix |
| compute GraphQL registration remains present | `test_api_contract.py` | use the existing complete retained GraphQL registration/root matrices |

Create `test_model_contract.py` because model and migration state have no canonical owner today.
It must not become a second API or UI suite.

The consolidation must preserve these distinct failure modes:

- a removed ORM field reappears;
- a removed model constant or choice reappears;
- the current migration state unexpectedly restores a removed field;
- a removed route becomes reversible or its literal path resolves;
- navigation or table metadata regains a mutation/dashboard affordance;
- REST or GraphQL exposes a removed field;
- the narrow DesiredNode PATCH contract stops working; and
- a retained compute/UI/API registration is accidentally removed.

Where an existing canonical test already proves one of these defects, mark the old test `covered`
instead of copying its body.

After focused replacements pass, delete
`nintent/nautobot_intent_catalog/tests/test_remove_unused_surfaces.py`. Do not delete migrations
`0009_reconciliation_status.py` or `0016_remove_reconciliation_dashboard_surfaces.py`; they are
historical migration evidence.

### 6.2 nctl compatibility policy and contract ownership

Update:

```text
nctl/docs/compatibility.md
nctl/docs/event-log.md
nctl/docs/output-format.md
nctl/tests/test_compatibility_snapshots.py
```

Rename `test_compatibility_snapshots.py` to `test_current_consumer_contracts.py` if the final file
continues to own several current-consumer schemas. The name must describe its lasting contract,
not the former "floor forever" mechanism.

The final policy must say:

1. the root coordinated breaking-change rule governs;
2. a schema change is made in one matched-version rollout across its current producers and
   consumers;
3. obsolete parallel writers, serializers, aliases, and deprecation-only versions are not kept;
4. each pinned field or event has a named current consumer or durable historical reader;
5. existing on-disk operation evidence remains readable through a minimal historical reader or an
   explicit offline migration when required; and
6. a version label is a current contract identifier, not a promise to run obsolete producers
   indefinitely.

Replace `FROZEN_*` and "floor, not ceiling" terminology with current-consumer terminology.
Current-version field checks should be exact when the consumer needs an exact shape. A coordinated
future change updates writer, reader, documentation, and test together.

At minimum, retain named coverage for:

| Contract | Named consumer or reader | Required evidence |
|---|---|---|
| `EventRecord` JSONL shape | `nctl ops list`, `nctl ops show`, historical operation logs | real write/read test, corruption behavior, and restart/disk readability |
| `nctl.drift.v1` | reconcile and AI/operator inspection | exact current data contract |
| `nctl.render.dnsmasq.v3` | reconcile and Ansible actuation | exact current data contract |
| `nctl.render.hosts-intent.v1` | inventory composition and Ansible | exact current data contract |
| `nctl.render.production.v1` | inventory composition and Ansible | exact current data contract |
| operations index/list/show | `nctl ops` and historical artifacts | real-file list/show tests, including an old result containing a removed dashboard field |
| `nctl.reconcile.v2` result | operation artifacts and `ops show` | exact current fields and explicit absence of reintroduced dashboard presentation |

For every other envelope currently listed in the old snapshot test, name its current consumer and
either:

- retain an exact current-version contract;
- point to an existing command/adapter contract that already owns the unique failure; or
- delete the duplicate snapshot assertion only after the replacement ledger identifies why no
  distinct compatibility failure remains.

Do not infer that a schema is unused merely because it is absent from the short Phase 0 summary
table. Reconcile the complete test file against `compatibility-consumers.tsv` and current CLI
documentation first.

The source-text scan for quoted event names is not automatically retained. Prefer executable
emitter/readback evidence in the owning operation tests. Keep a literal-source assertion only if
there is no executable registry or path and the report names the current consumer that depends on
that literal.

### 6.3 Historical nctl test filenames

Rename the following tracked modules with `git mv`:

| Current file | New risk/domain-owned file |
|---|---|
| `test_p4_deployment_profiles_unavailable_contract.py` | `test_deployment_profile_availability_contract.py` |
| `test_p4_intent_effect_summary_contract.py` | `test_intent_effect_summary_contract.py` |
| `test_p4_mixed_node_orchestration.py` | `test_mixed_node_orchestration.py` |
| `test_phase3_lifecycle_transition.py` | `test_lifecycle_drift_transition.py` |
| `test_vm_p3_compute_stays_inert.py` | `test_compute_actuation_inert.py` |

For each rename:

- capture old collected test IDs and their contract IDs before the move;
- keep every assertion unless a separate replacement-ledger row authorizes consolidation;
- update the module docstring to lead with the lasting contract and risk;
- remove stale statements such as "currently failing" when the baseline proves the test passes;
- keep a short historical reference only when it explains the origin of a regression; and
- collect and run the new module immediately after the move.

The compute test remains Tier A and must still run the real drift/planner dispatch over valid
compute rows and assert that no compute diff, manual-review record, unsupported record, or action
is emitted.

Phase references inside already domain-owned test files are not deletion targets by themselves.
Rewrite them only when they actively misstate the current contract.

### 6.4 Conditional orphan cleanup

Phase 0 found zero confirmed active orphans. Therefore Phase 1 has no deletion quota and no
pre-authorized production or dependency deletion.

Re-run exact tracked-file searches for:

```text
serve
dashboard
reconciliation_status
reconciliation_checked_at
DesiredHostQuickAdd
source_yaml
PreviewIntentSourceAnalysis
GenerateDesiredServices
service_repositories.yaml
compatibility
deprecation
legacy
fallback
test_p4_
test_phase3_
test_vm_p3_
skip
xfail
```

Also run the remaining roadmap searches for mocks and external boundaries so a removal does not
accidentally erase a Phase 3 handoff:

```text
monkeypatch
MagicMock
Mock
respx
subprocess
ssh-keyscan
ssh-keygen
ssh -G
ansible-inventory
ansible-playbook
transaction.atomic
```

Search only Git-tracked active code, tests, fixtures, configuration, and current documentation for
deletion decisions. Exclude `.git/`, `.local/`, `build/`, `__pycache__/`, generated coverage, and
historical `devdocs/` from the active-orphan count, while still classifying historical documents
as history.

Use token-aware patterns or inspect context manually. In particular, `serve` inside
`server`, `observed`, or `observe_node` is not a removed `nctl serve` reference.

For each surviving active match classify it as:

- retained contract;
- external boundary;
- negative absence proof;
- migration history;
- historical documentation;
- candidate consolidation; or
- orphan.

Delete a tracked fixture, helper, snapshot, dependency, or current documentation only when:

1. `git grep` shows no active consumer;
2. the Phase 0 ownership manifests show no retained unique defect;
3. dependency reverse inspection shows no non-test consumer;
4. the replacement ledger names the removed feature or superseded rule; and
5. the relevant focused suite passes immediately after deletion.

If no such item exists, record `zero additional orphans` and make no artificial deletion.

## 7. Implementation procedure

### Step 0 — Freeze revisions, dirty state, collection, and private evidence

1. Read the roadmap, Phase 0 final report, Phase 0 compatibility decision, root `README_DEV.md`,
   and `.local/localenv_memo.md`.
2. Record root and submodule HEADs, branches, upstreams, and porcelain status.
3. Stop or isolate the phase if unrelated dirty changes overlap any target file.
4. Create the private Phase 1 evidence directory with `umask 077`.
5. Record the current test file digests and collected IDs for all target modules.
6. Run focused baseline tests before editing.
7. Record Docker, Nautobot, Python, uv, pytest, and Ansible versions without reading secrets.
8. Capture a leak baseline for disposable containers, processes, test databases, networks, and
   volumes.

Gate: the tuple is frozen, target tests pass, and every edit target has a Phase 0 disposition or a
new explicit finding.

### Step 1 — Revalidate Phase 0 classifications

1. Join the 29 `replace` rows to the current nintent test IDs.
2. Re-run the token-aware removed-surface searches.
3. Reconcile every old compatibility snapshot entry with a named consumer.
4. Verify the five historical nctl modules still collect and still own the contracts stated in
   Section 6.3.
5. Verify compute actuation is still absent.
6. Write the initial replacement ledger before deleting or moving a file.

Gate: no proposed deletion is justified only by age, count, naming, or a noisy substring match.

### Step 2 — Consolidate nintent removal contracts

1. Add the narrow model/migration owner described in Section 6.1.
2. Add only missing removal rows to the canonical API and UI manifests.
3. Point duplicates to existing exact-field, route, permission, render, and GraphQL tests.
4. Run the three focused canonical modules in the disposable Nautobot environment.
5. Delete `test_remove_unused_surfaces.py`.
6. Re-run focused nintent fast and disposable suites.
7. Confirm migrations `0009` and `0016` remain tracked and the migrated state omits the four
   removed model fields.

Gate: every one of the 29 old tests has a ledger disposition, no migration history was removed,
and the canonical runtime owners pass.

### Step 3 — Replace superseded compatibility policy and snapshots

1. Rewrite the compatibility policy to the Phase 0 coordinated-rollout decision.
2. Update direct wording in `event-log.md` and `output-format.md`.
3. Rename and refactor the compatibility test around named current consumers.
4. Reuse real event/operations-index/CLI tests for disk round-trip, corruption, and historical
   readability instead of restating them through broad field floors.
5. Run focused compatibility, event, operations-index, ops-render, and CLI ops tests.
6. Search current nctl documentation and tests for obsolete `deprecation window`, `floor forever`,
   and parallel-writer claims.

Gate: every retained schema field has a named consumer, old operation evidence remains readable,
and no compatibility-only runtime writer is introduced.

### Step 4 — Rename historical nctl modules

1. Apply the five `git mv` mappings from Section 6.3 one at a time.
2. Update the lasting-contract docstring and direct references.
3. Collect the new module and compare test functions with the pre-move inventory.
4. Run the new module before proceeding to the next rename.
5. Update the replacement/rename ledger with old and new IDs.
6. Search tracked active tests for the old filenames.

Gate: all unique assertions remain represented and compute inertness remains positively tested.

### Step 5 — Remove any newly confirmed orphan support

1. Inspect only items proven to have lost their last test consumer in Steps 2–4.
2. Verify tracked status and reverse dependencies before deletion.
3. Delete the support item in the same component change as its last consumer.
4. Update current documentation only when it names an obsolete active command or policy.
5. Regenerate a lock or snapshot only if a tracked dependency was truly removed.
6. Run the owning component suite immediately.

Gate: every support deletion has a named removed consumer. It is valid for this step to delete
nothing.

### Step 6 — Run component and cross-component verification

Run the focused tests after each workstream, then the ordinary suites:

```bash
cd nctl && uv run pytest -q --durations=20
cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests
cd nauto && python3 -m unittest discover -s tests
cd nodeutils && uv run pytest -q --durations=20
cd ansible_agdev && python3 -m unittest discover -s roles/nodeutils_pvesh_helper/tests
```

The nintent fast suite is not sufficient for the model/API/UI/migration consolidation. Run the
full App suite in a disposable Nautobot test database with the local Phase 1 nintent checkout
mounted read-only ahead of the installed package. Record the exact validated command in
`commands.jsonl`.

The disposable harness must prove before test execution that:

- `nautobot_intent_catalog.__file__` resolves to the local Phase 1 checkout;
- the three changed canonical test modules resolve to the local Phase 1 checkout;
- the Django runner creates or uses only its disposable test database;
- the live `nautobot` database is not selected;
- no public network access is used; and
- teardown removes the test database and disposable container.

The intended command family is a one-shot `docker compose run --rm` using
`devenv/nautobot/docker-compose.yml`, a read-only bind mount of the local `nintent` checkout, and
`PYTHONPATH` pointing to that mount. Validate the image entrypoint before fixing the exact command.
Do not rebuild or restart the long-running Nautobot services for this test-only change.

If the local checkout cannot be loaded reproducibly in the disposable runner, stop. Do not
substitute the installed old tests or request a push/deployment merely to obtain a green result.

After all suites pass:

1. re-run the required searches;
2. compare retained Tier A IDs and transition owners with Phase 0;
3. remeasure files, static definitions, collected cases, tracked test lines, runtime, slowest
   tests, skips, and xfails with the Phase 0 method;
4. compare leak baselines; and
5. verify every worktree contains only intended Phase 1 changes.

### Step 7 — Commit boundaries and final report

Use reviewable component boundaries:

1. nintent test consolidation and removal;
2. nctl compatibility-policy/test replacement and historical renames; and
3. superproject submodule pointer updates plus `devdocs/big/test_strategy/p1/report.md`.

Do not push. Do not create compatibility duplicates as rollback.

The final report must record:

- exact starting and ending revision tuples;
- every moved, merged, covered, retained, and deleted test;
- every removed consumer or superseding decision;
- before/after files, definitions, collected cases, and test lines;
- focused and full results, including the local-source disposable Nautobot proof;
- retained Tier A and compute-inert proof IDs;
- compatibility consumers and historical-reader evidence;
- final search classifications;
- leak/cleanup result;
- deviations, discovered defects, or deferred items; and
- one precise status: `complete`, `partially complete`, `implemented, not environment-verified`,
  or `blocked`.

## 8. Verification matrix

| Area | Required proof |
|---|---|
| Deletion authority | every removed test/support item has a ledger row naming a removed consumer or visible replacement |
| nintent model | one runtime matrix proves both models omit both cache fields and removed constants |
| migration history | `0009` and `0016` remain; current project state omits the fields; disposable migration chain applies |
| nintent API | exact REST fields omit the cache; old GraphQL fields fail; retained roots and PATCH behavior pass |
| nintent UI | complete retained/removed route manifest, no-mutation permissions, navigation, and representative rendering pass |
| Historical removal module | no tracked active `test_remove_unused_surfaces.py`; all 29 prior tests are accounted for |
| Compatibility policy | coordinated matched-version wording replaces deprecation-only dual runtime policy |
| Current consumers | every pinned schema/event names a writer and current or historical reader |
| Durable evidence | real JSONL/index/result files remain readable, including historical removed presentation fields |
| Historical names | five old module names are absent and all collected contracts appear under risk/domain names |
| Compute safety | valid compute rows still produce zero compute drift, plan record, and action |
| Tier A | no retained Tier A proof or positive-evidence assertion is lost |
| Searches | all exact active matches are classified; noisy substrings do not authorize deletion |
| Isolation | no public network, secret read, live mutation, or leaked disposable state |
| Measurements | before/after method matches Phase 0 and is reported as diagnosis, not success criteria |

## 9. Rollback

Most Phase 1 changes are test and documentation changes. Roll back by restoring the prior
component revision, not by keeping duplicate old and new tests.

If a canonical replacement fails after the historical test was deleted:

1. stop further consolidation;
2. restore the old test from the frozen revision;
3. keep the replacement ledger and failing evidence;
4. determine whether the failure is an incomplete move or a production defect;
5. rerun both the old focused test and the proposed new owner; and
6. do not claim the deletion complete until the unique defect is visibly preserved.

If compatibility verification cannot read historical evidence:

1. restore the prior reader and tests;
2. preserve the exact synthetic historical fixture that exposed the failure;
3. determine whether a minimal reader or explicit offline migration is required;
4. create a separate bounded plan if production behavior must change; and
5. do not restore obsolete writers merely as rollback.

If disposable Nautobot cleanup fails, preserve sanitized logs, remove only the exact disposable
scope, verify the live database and long-running services were untouched, and report the phase as
incomplete.

## 10. Exit criteria

Phase 1 is `complete` only when:

- every Phase 0 `replace` test has a recorded moved, merged, covered, deleted, or retained
  disposition;
- `test_remove_unused_surfaces.py` is gone and its lasting contracts have canonical
  model/migration, API, or UI owners;
- no active test belongs solely to a removed feature or superseded compatibility branch;
- every deletion names its removed consumer and no deletion depends on a numeric target;
- migrations and historical reports remain intact;
- the compatibility policy matches the root coordinated breaking-change rule;
- every retained current schema and durable evidence field has a named consumer or historical
  reader;
- historical `nctl ops show` readability is proven;
- the five nctl historical filenames are replaced by risk/domain names without losing collected
  contracts;
- compute inertness and all other retained Tier A proofs still pass;
- all focused, ordinary, and disposable Nautobot gates pass against the sources actually changed;
- required searches find no unexplained active orphan, stale compatibility claim, or old target
  filename;
- no secret, private prose, public network dependency, live mutation, or leaked disposable state
  occurred; and
- before/after measurements and all deviations are recorded in the final report.

If an environment-backed check is omitted, substituted, or runs the installed old tests, the
maximum truthful status is `implemented, not environment-verified`, not `complete`.
