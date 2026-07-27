# Test Strategy Phase 4 Implementation Plan: Standardize Commands, Verify Isolation, and Report the Final Strategy

Parent: [roadmap.md](../roadmap.md) — Phase 4.

Depends on: [Phase 0 final report](../p0/report.md), [Phase 1 final report](../p1/report.md),
[Phase 2 final report](../p2/report.md), and [Phase 3 final report](../p3/report.md), all with
status **`complete`**.

Status: **`not started`**. This phase documents, reruns, audits, and reports. It does not authorize
a production/external mutation, compute realization, schema deployment, scratch-stack redeploy, or
any change to supported cluster behavior. It is the final phase of this roadmap.

## 1. Goal

Make the retained tiers reproducible for a future developer or agent who has never read a phase
report.

```text
maintained gates whose commands live in phase prose
  + a private Phase 0 manifest that only this initiative's authors can find
  + a Nautobot runtime gate reconstructed by hand from Step 4/5 narrative
  + measurements recorded once, in a private directory, with no committed method
  + skips, prerequisites, and expected-environment tiers documented per component at best

to
  one tracked command matrix in README_DEV with prerequisites, expected skips, and cleanup
  + one tracked transition/mutation manifest linking every supported behavior to a passing test
  + one maintained, re-runnable Nautobot runtime gate with a scratch-reusing and a clean mode
  + one committed measurement method producing the Phase 0/Phase 4 before/after comparison
  + a truthful final report on what got smaller, simpler, stronger, or was deferred
```

Phase 4 adds documentation, reproducibility, and audit evidence. It does not add new Tier A
coverage; a gap found here is recorded and either fixed within an already-decided contract or
truthfully deferred.

## 2. Authoritative handoff and current baseline

The governing contracts are the parent roadmap, [`README_DEV.md`](../../../../README_DEV.md), and
`.local/localenv_memo.md`. The private manifests remain the inventory baseline:

```text
.local/test-strategy/p0/20260726T034839Z/   transition-manifest.tsv, risk-register.tsv,
                                            test-ownership.tsv, fixture-ownership.tsv,
                                            external-boundaries.tsv, measurements.tsv,
                                            static-tests.tsv, collected-cases.tsv,
                                            runtime-summary.tsv, skips-xfails.tsv,
                                            reference-classification.tsv, commands.jsonl
.local/test-strategy/p1/, p2/, p3/          per-phase dispositions, results, and cleanup audits
```

At plan-writing time the clean revision tuple is:

| Repository | Revision |
|---|---|
| superproject | `5f71e2ebeb1a698339c05470b25444ead8917634` |
| `nctl` | `87f1737e3a1de24217a916d28d46f85adf16aee2` |
| `nintent` | `6a4b2afc891b9404c9cbdc09e4c4d6c1e8379711` |
| `nauto` | `e1f350c8cadf53077e232e9f90fd91cc704457b9` |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` |
| `ansible_agdev` | `da0dffe6bc0124bfb2dbbc8125660e4740bcaaa9` |

Step 0 must recapture this tuple and classify any delta rather than assuming it is unchanged.
Preserve pre-existing user changes; do not clean, reset, stash, or overwrite a dirty worktree.

### 2.1 Inherited state this phase must not weaken

- Phase 0: 23 cataloged transition risks, tier assignments for every active test, and the resolved
  compatibility decision now expressed in [`nctl/docs/compatibility.md`](../../../../nctl/docs/compatibility.md).
- Phase 1: removal-owned nintent assertions consolidated into canonical model/API/UI owners; five
  nctl modules renamed by lasting risk.
- Phase 2: Tier B/C dispositions frozen; the `ansible_agdev` helper allowlist became a diagnostic
  contract table; every remaining group has an explicit retain reason.
- Phase 3: maintained OpenSSH and Ansible loopback gates under
  [`devtests/test_strategy/`](../../../../devtests/test_strategy/); the exact-local-source Nautobot
  App runtime gate; the real-HTTP DesiredNode link transition with truthful post-PATCH failure
  evidence; nauto real-ORM ingest cases in `nauto/tests_runtime/`; the nodeutils-to-nauto-to-nctl
  observation traversal; prose-authority, desired-MAC, and compute-inert boundaries.

The last recorded passing state is: nctl 967, nodeutils 54, nauto 110, `ansible_agdev` helper 4,
OpenSSH gate 2, Ansible gate 1, exact-local-source Nautobot App runtime 290.

### 2.2 Gaps this phase must close

| Gap | Current state | Required Phase 4 result |
|---|---|---|
| command matrix | test commands are split across `nctl/README.md`, `nintent/README_DEV.md`, `devtests/test_strategy/README.md`, and phase reports; root `README_DEV.md` has none | one tracked matrix in root `README_DEV.md` with prerequisites, expected skips, evidence location, and cleanup, linked from component docs |
| Nautobot runtime gate | reproducible only by re-reading Phase 3 Step 4/5/6/7 prose (`/tmp/p3-*` copies, `PYTHONPATH`, copied HTTP dependency) | one maintained, parameterized command/script with a scratch-reusing `--keepdb` mode and a clean database reconstruction mode |
| measurement method | Phase 0 recorded results and a `commands.jsonl` trace but no committed script | one committed measurement entry point producing the same fields, run once for the Phase 4 "after" column |
| transition manifest visibility | `transition-manifest.tsv` is private to `.local/` | one tracked, sanitized manifest naming each transition, its tier, its owning test ID, and its environment |
| historical-only active names | `nintent/nautobot_intent_catalog/tests/test_p3_node_link_http.py` names a phase, not a risk | renamed by lasting risk with collected IDs proven still represented, or an explicit recorded reason to keep |
| skip/xfail accounting | the nintent fast suite skips Nautobot-only cases; no tracked statement of which tier owns them | every skip/xfail names an optional environment tier or an open defect, and no required Tier A gate can skip silently |

## 3. Scope

### 3.1 In scope

- Author the repository-wide test command matrix and tier/admission documentation.
- Convert the Phase 3 Nautobot runtime procedure into a maintained gate with a documented clean
  reconstruction mode.
- Commit a minimal measurement entry point and produce the before/after comparison.
- Publish a sanitized transition/mutation/read-only/manual/inert manifest with per-row proof IDs.
- Rename historical-only active test names when the move improves ownership.
- Audit skips, xfails, orphan fixtures, obsolete compatibility claims, removed-surface references,
  public-network calls, secret literals, and undocumented commands.
- Run the ordinary suites, the external-tool gates against installed versions, and one clean
  Nautobot database gate.
- Audit fixture-owned state, ports, processes, databases, rows, and files before and after.
- Produce step reports and one truthful final Phase 4 report plus the roadmap-level closure
  statement.

### 3.2 Out of scope

- Production/external cluster SSH, Ansible, Job apply, nodeutils collection, ingest, Nautobot
  writes, or Proxmox actions.
- Rebuilding, redeploying, or resetting the persistent scratch Nautobot/Postgres/Redis stack, and
  the GitHub-image nintent deployment flow.
- New Tier A coverage, new external gates, or new consolidation work beyond a bounded correction.
- Changing desired, actual, drift, planner, actuation, or evidence semantics.
- Deleting a test to improve a measurement.
- Public CI, a generic test framework, coverage gates, property-testing dependencies, or a new
  external service.
- Compute seeding, compute drift/action, guest creation, or provider abstractions.
- Pushing any repository; commits stay local and pushes remain user-owned.

## 4. Documentation design

### 4.1 Where each fact lives

| Fact | Owner |
|---|---|
| tier definitions, test admission rules, command matrix, prerequisites, expected skips | root `README_DEV.md` |
| transition/mutation manifest with per-row proof test IDs and environment | tracked `devtests/test_strategy/MANIFEST.md` |
| conformance gate usage, prerequisites, fixture ownership, cleanup | `devtests/test_strategy/README.md` |
| component fast-suite command and component-specific prerequisites | each component's `README.md`/`README_DEV.md`, linking up to the root matrix |
| durable evidence/consumer contracts | `nctl/docs/compatibility.md` (unchanged unless a claim is stale) |
| raw results, fingerprints, leak audits | `.local/test-strategy/p4/<UTC timestamp>/` only |

Documentation must not duplicate the matrix in more than one authoritative place. Component docs
link to the root matrix; they do not restate it.

### 4.2 Command matrix shape

The matrix must have one row per gate with these columns:

```text
gate | working directory | command | tier owned | prerequisites | expected skips |
runtime signal | evidence location | cleanup / ownership | required or optional
```

It must cover at least:

1. fast per-component commands (nctl, nintent Django-free, nauto, nodeutils, `ansible_agdev`
   helper);
2. the full ordinary offline suite for each component;
3. the scratch-reusing Nautobot runtime gate (`--keepdb`, named `test_nautobot`);
4. the clean Nautobot database reconstruction gate used for migration and final verification;
5. the OpenSSH conformance gate;
6. the Ansible conformance gate;
7. the nodeutils privileged-helper integration gate;
8. the measurement entry point; and
9. any separately approved production/external acceptance command, marked as requiring explicit
   user approval and out of ordinary use.

Every command must be stated with its documented working directory and must not depend on a bare
`pytest` invocation at the superproject root discovering several submodules. The repository has no
root pytest configuration; the matrix must therefore always give an explicit project and path.

### 4.3 Manifest shape

`devtests/test_strategy/MANIFEST.md` records one row per supported behavior:

```text
id | kind (automatic transition | explicit mutation | read-only deterministic |
manual safe stop | unsupported/inert) | tier | owning test ID(s) | environment/gate |
positive evidence asserted | notes
```

It contains synthetic identifiers, test IDs, tool names, and schema/version facts only. It must not
contain tokens, real host names, live inventory, key material, or private prose.

## 5. Work plan

### Step 0 — Freeze revisions, prerequisites, and the undocumented-command inventory

1. Create `.local/test-strategy/p4/<UTC timestamp>/` with directory mode `0700` and files mode
   `0600`.
2. Record root/submodule revisions, branches, dirty state, ahead/behind state, and tracked test
   digests.
3. Record Python, uv, pytest, git, Docker, Docker Compose, Nautobot, Django, PostgreSQL, Redis,
   OpenSSH, and Ansible versions as actually installed now; do not copy Phase 0's table forward.
4. Confirm the three persistent scratch Nautobot containers and the external Postgres/Redis
   prerequisites without reading secret values.
5. Capture before-state manifests: fixture-owned processes, loopback ports, Docker
   containers/networks/volumes, the presence or absence of `test_nautobot`, and tracked/untracked
   files.
6. Build an inventory of every test command currently reachable from a document or a phase report,
   marked `documented_and_current`, `documented_but_stale`, or `prose_only`. This inventory is the
   input to Steps 1 and 3.
7. Copy the Phase 0 transition manifest and Phase 1/2/3 dispositions into a Phase 4 work queue and
   resolve every renamed test ID to its current owner.

Gate: the frozen tuple, installed versions, scratch prerequisites, before-state fingerprints, and
the list of prose-only commands are recorded, and nothing has been modified.

### Step 1 — Make the Nautobot runtime gate maintained and re-runnable

1. Convert the Phase 3 procedure into one tracked entry point under `devtests/test_strategy/`
   (a script or a documented single command) that:
   - resolves exact local `nintent`, `nauto`, `nctl`, and `nodeutils` source rather than the
     installed scratch package, and fails loudly if resolution does not match the checkout;
   - stages source and any missing pure-Python runtime dependency into test-owned paths;
   - uses the named `test_nautobot` database and a test-only token and loopback URL, never the
     root `nctl.toml`, `.local/secrets`, or an inherited `NAUTOBOT_TOKEN`;
   - supports a scratch-reusing mode (`--keepdb`) and a clean reconstruction mode that recreates
     the test database and runs migrations plus `makemigrations --check --dry-run`;
   - accepts an optional test label so a single case can be run during iteration; and
   - removes every staged path by exact path on both success and failure.
2. Print and record the resolved `module.__file__`, source revision, and tracked-file digest for
   each staged component so a stale installed package cannot satisfy the gate.
3. Run the entry point in scratch-reusing mode and confirm the same case count as Phase 3's last
   recorded run, or explain the delta.
4. Do not restart, rebuild, redeploy, or reconfigure the persistent scratch stack. Recreating the
   named `test_nautobot` database is test-owned and allowed; record it.
5. Record the exact command, prerequisites, runtime, and cleanup for the Step 3 matrix.

Gate: a fresh agent can run the Nautobot runtime gate from one documented command in both modes,
exact-source resolution is proven, and no staged path or scratch mutation survives the run.

### Step 2 — Retire historical-only names, audit skips, and run the required searches

1. Rename `nintent/nautobot_intent_catalog/tests/test_p3_node_link_http.py` and any other
   surviving historical-only active name to a risk/domain name. Before committing, record the
   collected test IDs before and after and prove every case is still represented. If a rename would
   break a documented gate command, update that command in the same step.
2. Review every skip and xfail across all suites. Each must name an optional environment tier or an
   open defect. Record the expected skip count per suite for the matrix. No required Tier A gate
   may skip in the environment where it is required; a skip found there is a finding, not a pass.
3. Run the roadmap's required searches over active code, tests, fixtures, configuration, and
   current documentation, plus:
   - obsolete compatibility or deprecation claims;
   - orphan fixtures, helpers, and test-only dependencies;
   - public-network calls from any ordinary test;
   - secret literals, tokens, real host names, live inventory paths, and private prose in tracked
     tests, fixtures, and reports; and
   - test commands that appear in documentation but do not run.
4. Classify every match as retained contract, external boundary, negative absence proof,
   migration/history, or defect. A match count is not a deletion instruction.
5. Fix only what is bounded and already decided by the roadmap: a stale documented command, an
   orphan fixture with no consumer, a misfiled skip reason, or a historical name. Anything larger
   is recorded as a finding for the final report.

Gate: no active test name describes a phase instead of a risk without a recorded reason, every skip
has an owner, and the searches produce a classified result with no unexplained orphan or secret.

### Step 3 — Write the command matrix and tier/admission documentation

1. Add to root `README_DEV.md`:
   - the three risk tiers and what evidence each requires;
   - the test admission rules from the roadmap, stated as a review checklist;
   - the full command matrix in the Section 4.2 shape; and
   - the environment-class rule (persistent scratch, test-owned, production/external) as it applies
     to running tests.
2. Add or update links from `nctl/README.md`, `nintent/README_DEV.md`, `nauto/README_DEV.md`,
   `nodeutils/README.md`, and `ansible_agdev/README.md` to the root matrix. Keep the component
   fast command in place; remove or correct any component instruction the matrix supersedes.
3. Update `devtests/test_strategy/README.md` to cover the Nautobot runtime gate added in Step 1
   alongside the OpenSSH and Ansible gates, with prerequisites, fixture ownership, and cleanup.
4. State explicitly, in the matrix, which gates are required before claiming a cross-component
   change complete and which are optional environment tiers.
5. Execute every command in the matrix exactly as written, from the documented working directory,
   in a shell that does not inherit phase-specific environment variables. A command that does not
   run as written is corrected here, not annotated.

Gate: every documented command was executed as written and passed or produced its documented
expected skip; no gate exists only in a phase report.

### Step 4 — Publish the transition and mutation manifest

1. Generate `devtests/test_strategy/MANIFEST.md` from the Phase 4 work queue in the Section 4.3
   shape.
2. For every row, name the current owning test ID and the gate that runs it, and state the positive
   evidence it asserts (planned action, preflight, write, observation, denial, or tool invocation).
3. Mark each row `automatic transition`, `explicit mutation`, `read-only deterministic operation`,
   `manual safe stop`, or `unsupported/inert`, matching the roadmap's required distinction.
4. Run each named test ID at least once during Step 5 and record the result against its row. A row
   with no passing proof is a visible gap, not an omission.
5. Confirm the compute-inert row still states that it holds until a bounded first-realization
   roadmap explicitly supersedes it.
6. Verify no row contains a secret, live identifier, or private prose.

Gate: every supported behavior in the manifest resolves to a current test ID and a runnable gate,
and every gap is visible.

### Step 5 — Final measurement rerun with the Phase 0 method

Run this step only after Steps 1-4 have frozen the test set.

1. Commit a minimal measurement entry point that reproduces the Phase 0 fields: tracked test files,
   statically declared test functions/methods, collected cases, tracked test and non-test Python
   lines by component, and the source-to-test ratio.
2. Run it and record the "after" column. Use the same definitions Phase 0 used; if a definition must
   change, state the change and report both readings.
3. Record component runtime and the slowest tests per component using the same
   `--durations` / verbosity settings as Phase 0.
4. Record the skip/xfail totals from Step 2 and the transition-coverage totals from Step 4.
5. Produce the before/after table with an explanation for every material delta: tests deleted with
   removed behavior, tests consolidated by failure mode, tests added to close a Tier A gap, and
   tests renamed.
6. Do not present a lower count as the success criterion. If the case count rose, name the Tier A
   gap it closed and the duplication that was removed elsewhere.

Gate: the after-measurement is reproducible from a committed command, and every delta from Phase 0
has a stated cause.

### Step 6 — Full verification and isolation/cleanup audit

1. Run the five ordinary component suites from their documented working directories.
2. Run the OpenSSH, Ansible, and nodeutils privileged-helper gates against the installed tool
   versions recorded in Step 0.
3. Run the Nautobot runtime gate once in scratch-reusing mode and once in clean reconstruction
   mode. The clean run is the milestone gate; record its migration check result.
4. Run repeated or alternate-order suites only for a named flake or order-dependence risk carried
   from an earlier phase or observed in this one.
5. Compare before/after state:
   - fixture-owned processes and loopback ports;
   - temporary keys, stores, inventories, playbooks, markers, staged source copies, and event
     artifacts;
   - the named test database and any synthetic row fingerprints;
   - persistent scratch containers, networks, and volumes; and
   - tracked and untracked files.
6. Remove only exact fixture-owned state. The persistent scratch stack is a declared prerequisite,
   not a leak.
7. Re-run a failed cleanup gate after bounded repair at the smallest owned boundary. Stop only when
   the target is unresolved, external, production, irreversible, or outside scope.
8. Confirm no test contacted the public internet, weakened a policy, or wrote outside its declared
   boundary.

Gate: every required gate passes from its documented command, all fixture-owned state is accounted
for, and no production/external mutation occurred.

### Step 7 — Final report and roadmap closure

1. Write `devdocs/big/test_strategy/p4/report.md` with:
   - the exact final revision tuple and worktree state;
   - every command run and its result;
   - the before/after measurement table with explanations;
   - the skip/xfail accounting;
   - the manifest coverage summary and any visible gap;
   - findings, bounded corrections, and deviations; and
   - a status of `complete`, `partially complete`, `implemented, not deployed`, or `blocked` under
     `README_DEV.md` completion language.
2. State the roadmap-level outcome against the roadmap's definition of done, item by item. Any
   omitted, substituted, or deferred proof prevents an unqualified `complete`.
3. Record explicitly that `nctl_modularization` may now proceed, or name what still blocks it.
4. Leave any user-owned push, submodule pointer update beyond reviewed commits, or live deployment
   to the user.

Gate: the report is truthful, every roadmap definition-of-done item has a verdict, and no claim
rests on historical one-off evidence.

## 6. Required private evidence

Store sensitive or verbose evidence only under:

```text
.local/test-strategy/p4/<UTC timestamp>/
  README.txt
  revisions-start.tsv
  revisions-end.tsv
  tools.tsv
  scratch-state-before.tsv
  scratch-state-after.tsv
  command-inventory.tsv
  matrix-execution.tsv
  runtime-gate-result.tsv
  source-resolution.tsv
  rename-id-map.tsv
  skips-xfails.tsv
  searches.tsv
  measurements-after.tsv
  runtime-summary.tsv
  manifest-verification.tsv
  cleanup.tsv
  findings.tsv
  commands.jsonl
```

Retained logs may contain synthetic IDs, methods, paths, statuses, public fingerprints, tool
versions, schema versions, digests, test IDs, counts, and timings. They must not contain tokens,
authorization headers, raw or private SSH keys, live inventory, real managed-store contents,
Braindump bodies, Alignment Review summaries, raw ObjectChange payloads, or unrestricted provider
payloads.

## 7. Verification commands

The final authoritative list is the matrix produced in Step 3. The starting set is:

```bash
cd nctl && uv run pytest -q --durations=20
cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests
cd nauto && python3 -m unittest discover -s tests
cd nodeutils && uv run pytest -q --durations=20
cd ansible_agdev && python3 -m unittest discover -s roles/nodeutils_pvesh_helper/tests
uv run --project nctl pytest -q devtests/test_strategy/test_openssh_conformance.py
uv run --project nctl pytest -q devtests/test_strategy/test_ansible_conformance.py
cd nodeutils && uv run pytest -q tests/test_pvesh_helper_integration.py
```

The exact-local-source Nautobot runtime gate command is finalized in Step 1 and must appear in the
matrix in both scratch-reusing and clean reconstruction form. Do not copy an obsolete historical
`docker exec` line into the maintained documentation.

Run focused/changed commands first during iteration. The clean Nautobot gate and the complete
ordinary suite run at Step 6 final integration.

## 8. Defect handling and stop conditions

If a gate exposes a defect:

1. retain the failing reproducer and sanitized evidence;
2. name the violated authority, trust, scope, mutation, freshness, evidence, or documentation
   contract;
3. make a bounded fix only when the roadmap already determines the correct behavior;
4. rerun the highest practical gate, not only the new focused test; and
5. record the correction separately from the original failure.

Stop the affected workstream and request a decision when:

- a documented gate cannot be made to run without changing supported behavior;
- exact local source cannot be distinguished from an installed package;
- a required Tier A proof turns out to be missing rather than merely undocumented;
- a correction would change desired/actual/API/action/evidence semantics or add a compatibility
  shim;
- an operation could reach a real inventory, host, Proxmox API, external service, or unknown
  database;
- the persistent scratch stack would need a rebuild, redeploy, or reset;
- cleanup ownership is unresolved; or
- a secret, private prose body, raw key, or external payload would enter tracked evidence.

Do not mark the phase blocked for a stale `test_nautobot` database, an occupied loopback port, a
leftover fixture process, a missing temporary file, or another recoverable owned scratch defect.
Repair or recreate the smallest affected boundary and rerun.

## 9. Exit criteria

Phase 4 is complete only if:

- root `README_DEV.md` contains one command matrix covering fast, ordinary, Nautobot
  scratch-reusing, Nautobot clean reconstruction, OpenSSH, Ansible, helper, measurement, and
  approval-gated production/external commands, each with working directory, prerequisites, expected
  skips, evidence location, and cleanup;
- every matrix command was executed as written from its documented directory and passed or produced
  its documented expected skip;
- no command relies on a bare superproject `pytest` discovering several submodules;
- the exact-local-source Nautobot runtime gate runs from one maintained command in both
  scratch-reusing and clean modes, proves source resolution, and cleans up staged paths;
- `devtests/test_strategy/MANIFEST.md` maps every automatic transition, explicit mutation,
  read-only operation, manual safe stop, and inert path to a current passing test and gate, with
  gaps visible;
- every skip and xfail names an optional environment tier or an open defect, and no required Tier A
  proof skipped silently;
- the required searches are classified with no unexplained orphan fixture, obsolete compatibility
  claim, historical-only active name, public-network call, or secret literal;
- before/after files, cases, lines, runtime, slowest tests, skips, and transition coverage are
  recorded with the same method and every delta is explained;
- fixture-owned processes, ports, rows, databases, and files are removed or rolled back while the
  declared persistent scratch stack is left intact and running;
- no production/external mutation, scratch redeploy, compute action, or public-network call
  occurred;
- component docs link to the matrix without contradicting it; and
- `devdocs/big/test_strategy/p4/report.md` truthfully states its status and gives a verdict on every
  roadmap definition-of-done item.

An empty result, an undocumented prerequisite, or a command that only worked in a phase author's
shell is an unexercised path, not a pass.

## 10. Expected tracked changes

Expected tracked changes are limited to:

- root `README_DEV.md` tier, admission, and command-matrix sections;
- `devtests/test_strategy/` runtime-gate entry point, `MANIFEST.md`, measurement entry point, and
  `README.md` updates;
- component `README`/`README_DEV` links and corrections to superseded test instructions;
- test renames and bounded orphan/skip corrections from Step 2;
- this plan and the Phase 4 step reports and final report; and
- submodule pointers for reviewed commits.

Do not track `.local/` evidence, staged source copies, generated keys, trust stores, inventories,
playbooks, markers, test databases, container state, raw logs, caches, or installed packages. Do not
push; if a reviewed submodule commit later needs to be published, stop at the normal user-owned push
boundary.
