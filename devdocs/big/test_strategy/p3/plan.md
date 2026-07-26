# Test Strategy Phase 3 Implementation Plan: Close Tier A Transition and External-Boundary Gaps

Parent: [roadmap.md](../roadmap.md) — Phase 3.

Depends on: [Phase 0 final report](../p0/report.md), [Phase 1 final report](../p1/report.md), and
[Phase 2 final report](../p2/report.md), all with status **`complete`**.

Status: **`in progress`**. This phase adds and maintains test evidence. It does not authorize a
production/external mutation, compute realization, schema deployment, or change to supported
cluster behavior.

## 1. Goal

Make every retained Tier A mutation and automatic transition positively provable at the highest
practical layer, with particular emphasis on the one gap left by Phase 0:
representative fail-closed `link_actual_node` reset and confirmation failures have focused mock
coverage but no maintained real-HTTP proof against Nautobot.

```text
focused Tier A tests plus historical one-off environment reports
  -> retained focused tests for domain and orchestration failures
  -> small maintained gates for OpenSSH, Ansible, Nautobot/Django, HTTP, and the helper
  -> real DesiredNode GraphQL/PATCH/GraphQL transition and reset failures
  -> positive action, denial, observation, evidence, and no-repeat assertions
  -> no production/external write
```

Phase 3 does not maximize integration-test count. Each external gate must prove only behavior
owned by the normative implementation. Domain truth tables, executor sequencing, and
post-mutation evidence rules remain with their existing focused owners.

## 2. Authoritative handoff and current baseline

The governing contracts are the parent roadmap, `README_DEV.md`, and
`.local/localenv_memo.md`. The Phase 0 private manifests remain the inventory baseline:

```text
.local/test-strategy/p0/20260726T034839Z/
  transition-manifest.tsv
  external-boundaries.tsv
  risk-register.tsv
  test-ownership.tsv
  fixture-ownership.tsv
```

Phase 2's final disposition is also binding: retained Tier B/C tests have distinct contracts and
must not be consolidated incidentally while adding Tier A gates.

At plan-writing time the clean revision tuple is:

| Repository | Revision |
|---|---|
| superproject | `05757dc72c6a064dfc95d63c6bd72766e51b75e6` |
| `nctl` | `4ac8b7c42b4c957b1788db68f25824a2dd982816` |
| `nintent` | `2c1a8a4f0e774c7b683dd4758c6986451e571ddd` |
| `nauto` | `1c78af8bdbfc69cafdc293b4082f866de9f271b0` |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` |
| `ansible_agdev` | `da0dffe6bc0124bfb2dbbc8125660e4740bcaaa9` |

Step 0 must recapture this tuple and classify any delta rather than assuming it is unchanged.
Preserve pre-existing user changes and do not clean, reset, stash, or overwrite a dirty
worktree.

### 2.1 Proven contracts to retain

Phase 0 found 22 of 23 transition risks proven. In particular, retain:

- real drift/planner/executor multi-round dnsmasq content convergence and no-repeat coverage;
- non-DHCP IPAM link/refetch/convergence and partial-progress coverage;
- exact host scope through planning, SSH preflight, Ansible limit, and observation;
- dry-plan zero-write behavior;
- successful mutation followed by confirmation/final-drift failure with truthful evidence;
- forced observation refresh;
- Import and Analyze preview/apply/confirmation/repeat behavior;
- valid, stale, invalid, partial, and repeat ingest policy;
- missing-desired-state no-delete behavior;
- managed-file identity, path, digest, size, and freshness validation;
- Braindump/Alignment Review authority separation;
- durable event/artifact restart, corruption, privacy, and partial-log behavior;
- desired-MAC blocked rendering with no authoritative output or actuation; and
- compute desired rows remaining inert through real drift/planner dispatch.

These tests may receive fixture-only maintenance, but their real engines, positive action
assertions, exact scope, mutation evidence, observation, and no-repeat checks must remain intact.

### 2.2 Gaps this phase must close

| Boundary or transition | Current evidence | Required Phase 3 result |
|---|---|---|
| DesiredNode link | real success path was exercised historically; reset/error variants remain mocked | maintained real-HTTP GraphQL/PATCH/GraphQL success, reset/failure, truthful mutation evidence, fresh no-repeat |
| OpenSSH | focused subprocess fakes plus a historical disposable `sshd` report | maintained disposable real-tool gate for alias, port, offered key, store failure, mismatch, and effective options |
| Ansible | focused invocation fakes and historical command evidence | maintained real `ansible-inventory` and fixture-scoped `ansible-playbook` gate |
| Nautobot/Django | full App suite exists; nauto relies heavily on fake ORM | one reproducible runtime gate using exact local nintent/nauto source and a named test database |
| HTTP denial/failure | `respx` owns most status/error variants | representative real 401/403 and node-link failure paths through an actual local HTTP server |
| observation schema chain | each component has focused schema tests | one producer-to-ingest-to-reader conformance fixture with no independently rewritten schema |
| privileged helper | existing real helper integration test | retain and make it an explicit required Phase 3 gate |

Historical reports are design evidence, not passing Phase 3 results. The implementation must
create maintained tests or scripts in the repository and execute them from the frozen revision.

## 3. Scope

### 3.1 In scope

- Reconcile the Phase 0 transition/external-boundary manifests with the current test IDs.
- Add a small repository-owned external-conformance harness rather than more one-off command
  prose.
- Close the real-HTTP DesiredNode link gap against local scratch/test-owned Nautobot state.
- Exercise real OpenSSH and Ansible binaries only against local disposable fixtures.
- Run nintent Jobs and nintent/nauto ORM behavior in a real Nautobot/Django runtime.
- Add the smallest real-ORM nauto cases needed to replace fake-ORM-only confidence.
- Pass an actual nodeutils report through the retained nauto/nctl schema path.
- Prove user/AI prose changes cannot alter desired drift or emit an action.
- Preserve existing desired-MAC and compute-inert fail-closed boundaries.
- Record positive path evidence, environment prerequisites, exact tool versions, cleanup, and
  before/after scratch fingerprints.
- Fix a production defect only when the authoritative behavior is already fixed by the roadmap
  and the correction is bounded; retain the failing reproducer.
- Produce step reports and one truthful final Phase 3 report.

### 3.2 Out of scope

- Production/external cluster SSH, Ansible, Job apply, nodeutils collection, ingest, Nautobot
  writes, or Proxmox actions.
- Reading or modifying the real managed SSH store.
- Reconfiguring a real SSH daemon, weakening strict host-key checking, or fabricating trust for a
  real host.
- Using the repository-root `nctl.toml` or its live/scratch token for a test-owned HTTP server.
- Deploying local nintent changes into the persistent scratch service through the GitHub image
  flow; Phase 3 uses a test runtime that resolves exact local source.
- Desired compute seeding, compute drift/action, guest creation, resize, stop, replace, delete,
  migration, or provider abstractions.
- Desired-state schema, API, drift, planner, action, observation, or evidence changes made only to
  simplify testing.
- Re-running production/external acceptance from historical SSH, dnsmasq, interface-contract, or
  VM phases.
- Phase 2 consolidation, broad production modularization, a generic integration framework,
  public CI, a public-network dependency, or a new property-testing dependency.
- Phase 4's final repository-wide command matrix and final before/after strategy measurements,
  except for documenting the commands Phase 3 itself introduces.

## 4. Test ownership and harness design

### 4.1 Layer rule

Keep one primary owner per failure mode:

| Behavior | Primary owner |
|---|---|
| trust parsing, typed errors, planner classification, executor sequencing | existing focused component tests |
| real key lookup, effective SSH options, non-default port | disposable OpenSSH gate |
| inventory parsing, variable materialization, `--limit`, check/apply process behavior | real Ansible gate |
| model constraints, transaction rollback, permissions, Job discovery/execution | Nautobot runtime gate |
| REST/GraphQL routing and HTTP authentication/status | local real-HTTP gate |
| multi-round action/observation/no-repeat | existing nctl/nintent transition tests plus the real node-link gate |
| helper executable and allowlist boundary | existing nodeutils helper integration test |

Do not replay every focused failure through every environment gate. Conversely, do not claim a
real-tool contract from a monkeypatched subprocess result.

### 4.2 Maintained harness location

Create a bounded root-owned harness under:

```text
devtests/test_strategy/
  README.md
  conftest.py
  test_openssh_conformance.py
  test_ansible_conformance.py
  test_nautobot_http_conformance.py
  fixtures/
```

The exact split may be adjusted if an existing component is a clearer owner, but:

- cross-component/environment orchestration belongs in `devtests/test_strategy/`;
- component domain assertions stay in the component's current suite;
- framework-owned nintent tests stay under
  `nintent/nautobot_intent_catalog/tests/`;
- real-ORM nauto tests may live under `nauto/tests_runtime/` when they require Nautobot imports;
- shared fixtures contain synthetic public schema data only;
- no harness module may import `.local/secrets`, the repository-root `nctl.toml`, or live
  inventory; and
- each gate has one explicit command, prerequisite check, and non-skip failure mode in the
  required Phase 3 environment.

This is a narrow conformance harness, not a new general-purpose framework. Prefer pytest fixtures,
Nautobot's test runner, temporary directories, and existing component APIs over custom runner
abstractions.

### 4.3 Environment classes

Use three explicit boundaries:

1. **Persistent local scratch infrastructure:** the existing Postgres/Redis/Nautobot containers
   may be reused as prerequisites. Do not destroy the stack.
2. **Test-owned state:** named `test_nautobot` database rows, local loopback servers, keys, trust
   stores, inventories, playbooks, output files, and logs are disposable and must have exact
   ownership.
3. **Production/external state:** all physical nodes, Proxmox, external services, real inventories,
   and live credentials remain out of scope and read-only unless a later separately approved plan
   says otherwise.

During iteration, reuse `test_nautobot` with `--keepdb`. Recreate it only for incompatible schema,
migration/lifecycle verification, unexplained residue, or the final clean gate. A recoverable
scratch failure is repaired at the smallest owned boundary and rerun.

## 5. Work plan

### Step 0 — Freeze revisions, proof owners, prerequisites, and evidence

1. Create `.local/test-strategy/p3/<UTC timestamp>/` with directory mode `0700` and files mode
   `0600`.
2. Record root/submodule revisions, branches, dirty state, ahead/behind state, and tracked test
   digests.
3. Record Python, uv, pytest, Docker, Nautobot, Django, PostgreSQL, Redis, OpenSSH, and Ansible
   versions.
4. Confirm the three persistent local Nautobot containers and external Postgres/Redis
   prerequisites without reading secret values.
5. Verify whether installed nintent/nauto code matches the checked-out revisions. Regardless of
   the result, configure the test runtime to prove it imports the exact local source.
6. Copy the Phase 0 transition and external-boundary manifests into a Phase 3 work queue. Resolve
   every renamed Phase 1/2 test ID and record the current owner.
7. Mark each item `retain_and_run`, `add_real_boundary`, `replace_historical_only`, or
   `not_normative_here`, with a reason.
8. Run the existing focused Tier A baselines before editing:
   - node-link ledger/executor;
   - dnsmasq and IPAM multi-round;
   - SSH trust/enrollment/preflight;
   - durable evidence;
   - nintent Import/Analyze/IPAM;
   - nauto ingest;
   - nodeutils report/helper;
   - desired-MAC blocked render; and
   - compute inert dispatch.
9. Capture before-state manifests for fixture-owned processes, ports, databases, rows, files, and
   environment variables.

Gate: the current owners and the single known transition gap are explicit, exact local source can
be selected without changing the deployed scratch package, and no external target has been
contacted.

### Step 1 — Preserve current multi-round and mutation contracts

1. Pin the exact existing test IDs for dnsmasq mismatch/deploy/observe/converge/no-repeat and IPAM
   missing-link/apply/refetch/converge/no-repeat.
2. Assert those tests use the real drift engine and planner and do not replace the executor
   between classification and action.
3. Retain exact positive evidence:
   - expected initial drift code;
   - non-empty expected action;
   - non-empty SSH preflight when the action requires SSH;
   - exact target identity and host set;
   - mutation/write invocation;
   - supported observation/refetch;
   - fresh drift; and
   - no repeated action.
4. Retain dry-plan zero-write, forced observation, partial IPAM, post-mutation confirmation
   failure, final-drift failure, and operation-evidence restart/corruption cases.
5. Refactor fixtures only when needed for reuse by a real boundary. Do not move their primary
   assertions into the new environment harness.
6. Record any missing positive assertion as a bounded focused-test correction before starting
   external work.

Gate: all previously proven automatic transitions still pass with non-empty positive evidence;
the real-HTTP node-link reset gap remains visible rather than being mislabeled complete.

### Step 2 — Add the maintained disposable OpenSSH gate

Use only loopback and a temporary directory:

1. Locate the installed `ssh`, `sshd`, `ssh-keygen`, `ssh-keyscan`, and required support paths.
   A missing required binary fails this required gate with a prerequisite diagnostic; it does not
   silently skip.
2. Allocate a collision-safe loopback port and record it.
3. Generate disposable ED25519 host/client keys and an `authorized_keys` file with restrictive
   permissions.
4. Start a user-owned `sshd` bound only to `127.0.0.1` with password and
   keyboard-interactive authentication disabled. Validate its configuration before starting it.
5. Create a disposable nctl managed-store file containing the host key under a synthetic bare
   DesiredNode alias.
6. Using nctl's real probe/store functions and the real binaries, prove:
   - the bare stable alias succeeds on the non-default port;
   - endpoint or bracketed-port legacy naming does not satisfy the alias;
   - `ssh-keyscan` observes the fixture's actual offered key;
   - matching offered/managed public fingerprints produce `ready`;
   - a different offered key produces `ssh_host_key_mismatch`;
   - absent store produces `unenrolled`;
   - malformed and invalid-UTF-8 stores produce `ssh_store_read_failed`; and
   - effective `ssh -G` options contain the exact hostname, port, `HostKeyAlias`,
     `UserKnownHostsFile`, `StrictHostKeyChecking=yes`, `CheckHostIP=no`, and
     `UpdateHostKeys=no`.
7. Assert raw public-key blobs, private keys, and key contents are absent from retained command,
   event, and report evidence. Public SHA-256 fingerprints are allowed.
8. Prove the fixture directory is the only trust location read or written. Do not hash or open the
   real managed store unless a read-only existence/metadata check is strictly necessary; the
   preferred test does neither.
9. Stop the exact fixture process in `finally`/fixture teardown and prove the port and temporary
   directory are gone.

Gate: nctl's trust assumptions agree with the installed OpenSSH implementation and all negative
paths fail before any real/external host or service action.

### Step 3 — Add the maintained real Ansible boundary gate

1. Generate a temporary two-host YAML inventory with synthetic stable IDs, explicit local
   addresses, non-default-port metadata, and nctl-owned SSH policy variables.
2. Run installed `ansible-inventory --list` and `--host` and validate the parsed JSON rather than
   source YAML text.
3. Pass the parsed hosts through nctl's real inventory trust validator.
4. Inject each forbidden SSH-policy override individually and assert nctl rejects it before
   `ansible-playbook` starts.
5. Add a fixture-only playbook that targets both synthetic inventory hosts with
   `connection: local` and writes only host-specific temporary marker files.
6. Run it with `--check --limit <one exact host>`:
   - Ansible starts and reports the selected host;
   - neither marker is written; and
   - the sibling host is absent from recap/evidence.
7. Run the same fixture in apply mode with the same exact limit:
   - only the selected host's marker is written;
   - the sibling marker remains absent; and
   - the recorded invocation contains exactly the planned limit.
8. Run a failed-preflight case through the nctl boundary and prove no `ansible-playbook` process or
   marker exists.
9. Preserve the distinction between direct administrative full-group behavior and
   reconcile-owned exact-host behavior; this gate proves the latter.
10. Remove only fixture-owned inventory, playbook, markers, and logs.

`connection: local` is used only to prove Ansible parsing, limit, and check/apply process
semantics without contacting a host. OpenSSH policy and key identity remain owned by Step 2.

Gate: real Ansible confirms staged inventory parsing, exact host limiting, check/apply separation,
and zero playbook start after rejected trust policy.

### Step 4 — Establish the exact-local-source Nautobot runtime gate

1. Reuse the persistent scratch Postgres/Redis services and a named test database. Do not mutate
   the ordinary `nautobot` database.
2. Run the test web/runtime from the exact checked-out nintent and nauto source by an explicit
   bind/copy/import path. Record `module.__file__`, source revision, and a tracked-file digest so
   an installed stale package cannot satisfy the gate.
3. Use a test-only token and loopback URL in a test-only config. Never use the root `nctl.toml`,
   `.local/secrets`, or an inherited `NAUTOBOT_TOKEN`.
4. Run migrations and `makemigrations --check --dry-run` when the runtime is first prepared.
5. Run the complete nintent Nautobot App suite, including:
   - Import preview/apply/confirmation/repeat;
   - Analyze preview/apply/operator-field preservation/repeat;
   - IPAM transaction, exact field choice, rollback/partial result, and repeat;
   - retained GraphQL roots and narrow REST methods/fields;
   - lifecycle and node-link source/field behavior;
   - read-only UI permission and no-mutation manifest; and
   - authentication/authorization denial.
6. Add a small nauto real-ORM set that proves only framework-owned behavior currently hidden by
   fake ORM:
   - a valid nodeutils report creates/updates the expected actual ledger rows;
   - stale or structurally invalid input writes zero rows;
   - one malformed Proxmox guest is isolated without losing valid sibling results;
   - transaction/constraint failure does not leave an unreported partial write;
   - a repeat is a semantic no-op; and
   - missing desired state never deletes, unlinks, retires, or replaces actual state.
7. Keep fast fake-ORM tests for domain diagnostics that do not depend on Django behavior. Do not
   reproduce their full matrices in the runtime set.
8. Record database/row fingerprints before and after each fixture. Transaction rollback or exact
   synthetic cleanup must restore the declared boundary.

Gate: all framework-owned contracts run against real Nautobot/Django and the exact local source;
no required runtime case is hidden behind the fast suite's conditional skips.

### Step 5 — Close the DesiredNode real-HTTP transition and reset gap

Run this step against the Step 4 test runtime and named test database:

1. Start an actual local HTTP server on a recorded non-live loopback port.
2. Create a synthetic DesiredNode and one uniquely matching Device with stable test IDs and no
   realized link. Create a second Device only for wrong-identity confirmation cases.
3. Use the real `NautobotClient`, desired/actual GraphQL readers, drift engine, classifier, and
   planner to prove initial `actual_node_not_linked` and one exact `link_actual_node` action.
4. Run the real ledger writer:
   - GraphQL pre-read of the exact node;
   - exact REST PATCH of link and `source=derived`;
   - GraphQL post-read confirming the same node/candidate/source.
5. Recompute a fresh snapshot, drift, and plan. Assert the link action does not repeat; do not
   substitute a second call's `node_already_linked` error for fresh planning evidence.
6. Drive representative pre-write fail-closed fixtures through the real HTTP server:
   - node absent by ID;
   - returned slug/identity differs from the planned target;
   - an existing full or partial link/source must never be cleared or replaced;
   - authentication or permission denial; and
   - malformed or failed GraphQL pre-read.
7. Drive representative post-PATCH reset/confirmation fixtures through actual HTTP traffic and
   test-owned database control:
   - link reset before confirmation;
   - node disappears before confirmation;
   - different candidate is observed;
   - source changes from `derived` to `override`; and
   - confirmation HTTP/GraphQL failure.
8. Implement the reset controller outside production APIs, for example as a test-owned forwarding
   proxy or runtime fixture callback that mutates only the named synthetic row after observing the
   successful PATCH. Do not add a production-only test endpoint or weaken serializer/model
   policy.
9. For every successful PATCH followed by failure, assert:
   - typed failure code;
   - `success=false`;
   - `mutated=true`;
   - exact action/target retained;
   - the round and operation evidence retained;
   - `had_side_effects=true`; and
   - fresh final drift is recorded, or a typed failure truthfully marks it unknown.
10. For every pre-PATCH denial, assert `mutated=false`, no PATCH, no sibling-row change, and no
    action falsely reported complete.
11. Record HTTP method/path/status only. Assert non-empty GraphQL/PATCH/GraphQL traffic for the
    positive path and exact call boundaries for negative cases.
12. Restore/delete only the synthetic rows and confirm their IDs, ObjectChange attribution, and
    fixture fingerprints. Do not retain request bodies or token values.

Absent action, pre-linked setup, mocked `httpx` transport, ORM-only confirmation, or a repeat
writer refusal without fresh re-planning does not satisfy this gate.

Gate: the sole Phase 0 partial transition becomes proven through real HTTP, including truthful
post-mutation failure evidence and fresh no-repeat.

### Step 6 — Prove observation schema traversal without a second interpretation

1. Build one deterministic synthetic host observation using nodeutils' real report builder and
   schema/version constants.
2. Include:
   - stable node identity;
   - observation time;
   - managed dnsmasq path/digest evidence; and
   - a bounded Proxmox inventory with one valid guest and one target-local invalid/partial case.
3. Feed the produced report bytes/object directly into nauto's real ingest boundary in the Step 4
   runtime. Do not translate it through a new fixture dictionary.
4. Read the resulting actual state through nctl's retained actual GraphQL/source parser.
5. Assert identity, version, freshness, path, digest, guest-local error, and valid sibling values
   survive the path exactly once:

```text
nodeutils producer
  -> nauto validation and ORM ingest
  -> canonical actual GraphQL
  -> nctl source model
```

6. Prove wrong identity, stale timestamp, unsupported schema, wrong managed path, and oversized or
   malformed evidence fail at their current owner with zero unintended write.
7. Run the existing real privileged-helper integration test and assert its output is accepted by
   the same nodeutils report builder. Do not require a real Proxmox host or sudoers grant.
8. Keep fixture payloads synthetic and bounded; record only public schema fields and digests.

Gate: producer and consumers share one versioned contract fixture and framework-backed ingest
behavior is no longer inferred solely from parallel hand-built dictionaries.

### Step 7 — Prove prose authority, desired-MAC fail-closed behavior, and compute inertness

1. In the Nautobot test runtime, create a desired/actual snapshot and baseline drift/plan.
2. Create or update a synthetic Braindump body and Alignment Review summary through their
   retained authorized writers.
3. Refetch canonical desired state and recompute drift/plan. Assert:
   - no desired model row or operator-owned field changed;
   - no drift code, intent-effect classification, render bytes, or digest changed;
   - no planner action appeared;
   - no SSH, Ansible, Job, observation, ingest, or provider call occurred; and
   - private prose is absent from logs/artifacts.
4. Repeat the existing desired-MAC mismatch, ambiguity, and invalid-source cases and assert:
   - structured target-local diagnostics;
   - no authoritative dnsmasq bytes or digest;
   - an existing output remains byte-identical;
   - zero SSH/Ansible calls;
   - unrelated valid targets remain correctly isolated; and
   - the same target recovers deterministically when the canonical MAC becomes valid.
5. Run the current compute-inert proof using non-empty synthetic desired compute rows through the
   real drift registry/planner dispatch. Assert no compute drift, reconciler, writer, provider
   call, or hidden action exists.
6. Confirm Step 4's scratch database still has no unauthorized persistent compute seed.

Gate: prose remains non-executable, MAC ambiguity remains a safe stop with deterministic recovery,
and compute remains explicitly unsupported/inert.

### Step 8 — Full verification, cleanup audit, and final report

1. Run all changed focused tests after each workstream.
2. Run every retained Tier A owner from the Phase 3 work queue.
3. Run the five ordinary component suites.
4. Run the complete exact-local-source Nautobot runtime gate.
5. Run the real-HTTP node-link gate, OpenSSH gate, Ansible gate, schema traversal gate, and
   privileged-helper gate.
6. Run the Phase 0 required searches and classify new matches as retained contract, external
   boundary, test fixture, historical report, or defect. Do not treat match count as a deletion
   instruction.
7. Review every skip/xfail. A required Phase 3 gate may not silently skip in this environment.
8. Compare tracked test digests and worktree state. Explain every intended change and leave
   unrelated/user changes untouched.
9. Compare before/after:
   - fixture processes and loopback ports;
   - temporary keys/stores/inventories/playbooks/markers;
   - named test database and synthetic row fingerprints;
   - persistent scratch containers/networks/volumes; and
   - tracked/untracked files.
10. Remove only exact fixture-owned state. Persistent declared scratch services are not leaks.
11. Re-run a failed cleanup gate after bounded repair. Stop only when the target is unresolved,
    external, production, irreversible, or outside scope.
12. Reconcile every Phase 0 transition and external-boundary row with a passing maintained test or
    a visible truthful deviation.
13. Write per-step reports as useful and one `report.md` with revisions, commands, positive
    evidence, failures/corrections, cleanup, omissions, and final status.

Gate: every Phase 3 Tier A/external requirement points to a passing maintained test, all
fixture-owned state is accounted for, and no production/external mutation occurred.

## 6. Required private evidence

Store sensitive or verbose evidence only under:

```text
.local/test-strategy/p3/<UTC timestamp>/
  README.txt
  revisions-start.tsv
  revisions-end.tsv
  tools.tsv
  source-resolution.tsv
  scratch-state-before.tsv
  scratch-state-after.tsv
  transition-work-queue.tsv
  external-boundary-work-queue.tsv
  protected-tier-a.tsv
  commands.jsonl
  focused-results.tsv
  ordinary-results.tsv
  openssh-result.tsv
  ansible-result.tsv
  nautobot-runtime-result.tsv
  node-link-http-cases.tsv
  http-method-path-status.tsv
  nauto-orm-result.tsv
  observation-schema-result.tsv
  prose-authority-result.tsv
  mac-compute-boundaries.tsv
  helper-result.tsv
  skips-xfails.tsv
  cleanup.tsv
  searches.tsv
  findings.tsv
```

`node-link-http-cases.tsv` records:

```text
case_id
initial_state
expected_graphql_pre
expected_patch_count
post_patch_fixture
expected_error_or_success
expected_mutated
expected_final_drift_state
expected_repeat_action_count
actual_http_path_summary
result
```

Retained logs may contain synthetic IDs, methods, paths, statuses, public fingerprints, tool
versions, schema versions, and digests. They must not contain tokens, authorization headers, raw
SSH keys, private keys, live inventory, real managed-store contents, Braindump bodies, Alignment
Review summaries, raw ObjectChange payloads, or unrestricted provider payloads.

## 7. Verification commands

Exact focused IDs may change during Step 0's current-owner reconciliation. At minimum, preserve
these ordinary commands:

```bash
cd nctl && uv run pytest -q --durations=20
cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests
cd nauto && python3 -m unittest discover -s tests
cd nodeutils && uv run pytest -q --durations=20
cd ansible_agdev && python3 -m unittest discover -s roles/nodeutils_pvesh_helper/tests
```

The maintained conformance commands must be finalized in
`devtests/test_strategy/README.md`. Their intended shapes are:

```bash
uv run --project nctl pytest -q devtests/test_strategy/test_openssh_conformance.py
uv run --project nctl pytest -q devtests/test_strategy/test_ansible_conformance.py
uv run --project nctl pytest -q devtests/test_strategy/test_nautobot_http_conformance.py
cd nodeutils && uv run pytest -q tests/test_pvesh_helper_integration.py
```

The Nautobot runtime command must use the existing scratch stack, the named test database, and
exact local source. Record the final command only after Step 4 proves source resolution; do not
copy an obsolete historical compose command into the maintained documentation.

Run changed-file/focused commands first. The final gate includes one clean named-test-database run
only after the scratch-reusing iteration gates pass.

## 8. Defect handling and stop conditions

If a gate exposes a production defect:

1. retain the failing reproducer and sanitized evidence;
2. name the violated authority, trust, scope, mutation, freshness, or evidence contract;
3. make a bounded fix only when the roadmap already determines the correct behavior;
4. rerun the highest practical transition and its focused regression; and
5. record the correction separately from the original failure.

Stop the affected workstream and request a separate decision when:

- expected behavior is ambiguous or conflicts with an authoritative contract;
- a correction changes supported desired/actual/API/action/evidence semantics;
- a test requires a new production endpoint, security exception, or compatibility shim;
- exact local source cannot be distinguished from an installed package;
- a required reset cannot be isolated to named test state;
- an operation could reach a real inventory, host, Proxmox API, external service, or unknown
  database;
- cleanup ownership is unresolved;
- a secret, private prose body, raw key, or external payload would enter tracked evidence; or
- compute realization or another deferred capability is required.

Do not mark the phase blocked for a stale `test_nautobot` database, occupied loopback port,
fixture process, missing temporary file, or other recoverable owned scratch defect. Repair or
recreate the smallest affected boundary and rerun.

## 9. Exit criteria

Phase 3 is complete only if:

- every retained automatic transition has one real multi-round action/observation/no-repeat proof;
- dnsmasq and IPAM primary proofs remain intact and passing;
- DesiredNode linking is proven through real GraphQL pre-read, exact PATCH, GraphQL confirmation,
  fresh drift, and zero repeated action;
- representative pre-write and post-PATCH node-link resets run through real HTTP against named
  test state;
- successful PATCH followed by failure records `success=false`, `mutated=true`, retained
  action/round evidence, and fresh drift or a typed unknown state;
- real OpenSSH proves stable alias, non-default port, offered-key match/mismatch, store handling,
  and effective strict options;
- real Ansible proves staged inventory parsing, forbidden-override rejection, exact limit, and
  check/apply separation;
- the exact-local-source Nautobot runtime proves Import, Analyze, IPAM, API/GraphQL, permission,
  transaction, and selected nauto real-ORM behavior;
- nodeutils output traverses nauto ingest and nctl reading through one versioned contract fixture;
- the privileged-helper integration gate remains passing;
- Braindump/Alignment Review prose changes produce zero desired mutation, drift change, render
  change, or action;
- desired-MAC conflicts remain fail-closed and recover deterministically;
- compute desired rows remain inert through real registry/planner dispatch;
- every required gate records non-empty positive action, write, observation, denial, or tool
  invocation evidence;
- no required Tier A gate silently skips or substitutes a mock for the normative boundary;
- no test contacts the public internet or mutates production/external state;
- fixture-owned processes, rows, files, ports, and credentials are removed or rolled back, while
  declared persistent scratch infrastructure is left intact;
- ordinary component suites and all Phase 3 conformance gates pass from documented working
  directories; and
- `devdocs/big/test_strategy/p3/report.md` truthfully states `complete`,
  `partially complete`, `implemented, not deployed`, or `blocked` under `README_DEV.md`.

An empty action/preflight/write/observation/denial record is an unexercised path, not a pass.
Historical one-off evidence is not a substitute for a maintained Phase 3 gate.

## 10. Expected tracked changes

Expected tracked changes are limited to:

- `devtests/test_strategy/` conformance tests, fixtures, and usage documentation;
- bounded nctl/nintent/nauto/nodeutils/ansible test changes required by the named Tier A gaps;
- a minimal behavior-preserving production seam only if a real boundary cannot otherwise be
  observed;
- this plan and Phase 3 reports; and
- submodule pointers for reviewed commits.

Do not track `.local/` evidence, generated keys, trust stores, inventories, playbooks, markers,
test databases, container state, raw logs, caches, or installed packages. Do not push; if a
matched local-source container build later requires remote commits, stop at the normal user-owned
push boundary.
