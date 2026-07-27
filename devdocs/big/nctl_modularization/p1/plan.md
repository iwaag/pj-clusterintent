# nctl Modularization Phase 1 Implementation Plan: Resolve the Duplicated Compute Contract

Parent: [roadmap.md](../roadmap.md) — Phase 1. Predecessor: [p0/report.md](../p0/report.md).

Status: proposed; cross-repository source change with exactly one coordinated scratch-stack
deployment.

## 1. Goal

Phase 1 gives the compute contract one semantic owner and an executable mechanism that fails when
nintent and nctl disagree about it.

The phase must answer, and prove:

1. Which compute rules are actually implemented on both sides — including the two that Phase 0's
   inventory recorded as one-sided and this plan's search shows are not?
2. For every symbol in the duplicated set: does it belong to the shared contract, to nintent only,
   or to nctl only, and why?
3. What exactly does "exactly one implementation" mean for two repositories that must not share a
   runtime package, and where is that stated so a later agent cannot reinterpret it?
4. Does the conformance mechanism actually fail on an injected divergence — in nctl's direction, in
   nintent's direction, and against a hand-edited fixture?
5. Does compute remain inert, and does every currently emitted `DesiredSourceIssue` code, path, and
   message stay byte-identical?
6. What is the matched revision tuple after the coordinated nintent push and image rebuild, and was
   the resolved commit verified from the build rather than assumed?

The observable result is:

```text
current
  nintent/nautobot_intent_catalog/compute_contract.py (292 lines)
  + a near-identical re-implementation inside nctl sources/desired.py, carrying a comment that
    says "any future contract change must be applied to both"
  + the compute NIC/primary-endpoint contract implemented a second time in nintent models.py
  + the realized-link/source pairing rule implemented three times
  + two spellings of the actionable-lifecycle predicate
  + two independently maintained test surfaces that can both stay green while disagreeing

to
  one owner module in nintent that defines every shared compute rule
  + a fixture generated from that owner, committed once, consumed by an ordinary nctl test
  + a superproject gate that fails when the committed fixture is stale against the checked-out owner
  + one spelling of the actionable-lifecycle predicate
  + nctl-retained checks that are individually justified as current-read safety, not as ownership
  + identical envelope codes, identical source-issue messages, and compute still inert
```

Phase 1 does not move the compute block out of `sources/desired.py`. That relocation is Phase 2
work (roadmap Phase 2, item 1). Phase 1 decides what survives; Phase 2 decides where it lives.
Doing both at once would mix a cross-repository semantic change with a module split and make a
failing gate ambiguous.

## 2. Required outputs

Phase 1 produces:

1. this implementation plan;
2. one private evidence directory under `.local/nctl-modularization/p1/<UTC timestamp>/`;
3. a frozen rule-by-rule disposition table covering every symbol in the duplicated set, with
   `shared` / `nintent_only` / `nctl_only` and the reason;
4. corrections to the Phase 0 duplication inventory and, if it is contradicted, to
   [`roadmap.md`](../roadmap.md), made in the same step that finds the contradiction;
5. the owner implementation in `nintent/nautobot_intent_catalog/compute_contract.py`;
6. the conformance case set and fixture generator owned by nintent;
7. the generated fixture committed once, in `nctl/tests/fixtures/compute_conformance.json`;
8. the consuming nctl ordinary test and the superproject freshness gate;
9. injected-divergence evidence for all three failure directions;
10. behavior-preservation evidence: unchanged source-issue codes/paths/messages, unchanged envelope
    codes, unchanged deterministic artifacts, compute still inert;
11. the matched revision tuple with build-log, `build_info.json`, and image-label proof of the
    resolved nintent commit;
12. one `report<N>.md` per step under `devdocs/big/nctl_modularization/p1/`; and
13. `devdocs/big/nctl_modularization/p1/report.md` with a final state of `complete`,
    `partially complete`, `implemented, not deployed`, or `blocked`.

Tracked files Phase 1 may change:

- `devdocs/big/nctl_modularization/p1/plan.md`, `report<N>.md`, `report.md`;
- `devdocs/big/nctl_modularization/roadmap.md` and `devdocs/big/nctl_modularization/p0/*.md`, only
  to correct a fact this phase disproves;
- `nintent/nautobot_intent_catalog/compute_contract.py`, `models.py`, the new
  `compute_conformance.py`, their tests, and `nintent/README_DEV.md`;
- `nctl/src/nctl_core/sources/desired.py`, `nctl/tests/test_sources_desired.py`,
  `nctl/tests/test_compute_actuation_inert.py`, the new `nctl/tests/test_compute_conformance.py`,
  and the new `nctl/tests/fixtures/compute_conformance.json`;
- `devtests/test_strategy/generate_compute_conformance.py`,
  `devtests/test_strategy/test_compute_conformance.py`, `devtests/test_strategy/MANIFEST.md`,
  `devtests/test_strategy/README.md`; and
- `README_DEV.md` (command matrix row) and `devenv/nautobot/Dockerfile` (`NINTENT_COMMIT` only).

Nothing else. In particular: no drift, planner, reconcile, production, dnsmasq, SSH, Ansible, or
CLI module changes; no nintent migration; no new runtime dependency in either repository.

## 3. Authority and safety boundary

### 3.1 Allowed actions

Phase 1 may:

- read and edit the tracked files listed in Section 2;
- run every ordinary offline suite and every gate in the root command matrix;
- run read-only `nctl` commands against the local Nautobot — `status`, `drift`, `drift --json`,
  `ops list`, `ops show` — and read-only GraphQL query documents;
- render deterministic artifacts into a phase-owned temporary directory for the byte comparison
  against the Phase 0 baseline;
- commit in `nintent`, `nctl`, and the superproject;
- after the Section 3.4 approval: bump `NINTENT_COMMIT` in `devenv/nautobot/Dockerfile`, run
  `docker compose build --no-cache`, and restart the local scratch Nautobot web, worker, and
  scheduler containers;
- temporarily inject a divergence into a working-tree copy for the Step 6 proof, provided it is
  reverted in the same step and never committed; and
- remove only the exact disposable resources this phase created.

### 3.2 Prohibited actions

Phase 1 must not:

- push any submodule or move a submodule pointer without the user doing it (Section 3.4);
- add a shared Python package, a new wire field, a nintent migration, a runtime import from nintent
  into nctl, or any runtime dependency;
- add a compatibility shim, dual reader, feature flag, or version branch so nctl tolerates both an
  old and a new nintent (roadmap governing decision 6);
- change any envelope field, envelope error code, event field, artifact field, drift code, exit
  code, CLI flag, or `DesiredSourceIssue` code, path, or message;
- seed a desired or actual compute row, add a compute drift comparator, planner action, reconciler,
  or actuator, or otherwise make compute non-inert;
- run `nctl reconcile --yes`, `nctl apply`, a lifecycle or Braindump write, SSH enrollment to a real
  node, an Ansible playbook against real nodes, nodeutils collection against real nodes, ingest, a
  Nautobot Job apply, or any Proxmox operation;
- write into `ansible_agdev/inventories/generated/`, `nctl.toml`, or any tracked artifact path;
- bump `NAUTO_COMMIT`, change `nauto/seed/intent_sources.yaml`, or otherwise alter what the image
  bakes in besides the nintent revision;
- read or copy `.local/secrets`, authorization headers, private keys, raw public-key blobs,
  Braindump bodies, Alignment Review summaries, or ObjectChange payloads into evidence; or
- weaken strict SSH verification, exact target scoping, Ansible override rejection, plan/apply
  separation, desired-MAC fail-closed behavior, or the non-executable prose boundary.

### 3.3 Stop conditions

Stop the affected step, preserve evidence, and ask rather than widening authority when:

- a disposition cannot be decided without inventing user intent or changing supported behavior;
- preserving a `DesiredSourceIssue` code, path, or message and adopting the single owner turn out to
  be mutually exclusive;
- the injected-divergence proof does not fail in all three directions;
- the rebuild resolves a nintent commit different from the one requested, or `build_info.json` and
  the image label disagree;
- the Nautobot runtime gate fails after the rebuild in a way that is not explained by the Phase 1
  diff; or
- any revision in the six repositories moves mid-phase (Section 4.4).

A rebuild that succeeds but whose resolved commit cannot be proven from the build output is a stop
condition, not a warning. The known caching hazard is that `docker compose build` can silently reuse
a layer holding an older nintent.

### 3.4 Approval gates

Two actions in this phase require an explicit user decision before they run:

1. **nintent push.** Pushing is user-owned. Step 9 stops after committing in nintent, states the
   exact commit and what it contains, and asks the user to push. No local workaround for an
   unpushed commit is permitted — the image installs from GitHub by commit.
2. **Image rebuild and scratch-stack restart.** `docker compose build --no-cache` plus restart of
   the local Nautobot web, worker, and scheduler containers is a scratch-environment mutation, but
   it replaces the running image and is hard to observe halfway. Ask before running it, in the same
   message that reports the pushed commit.

Everything before Step 9 is local, reversible, and needs no approval. If the user declines either
gate, Phase 1 finishes as `implemented, not deployed` with the exact remaining commands recorded —
not as `blocked`.

## 4. Governing inputs and planning-time findings

### 4.1 Required reading before Step 0

- root [`README.md`](../../../../README.md) and [`README_DEV.md`](../../../../README_DEV.md);
- [`.local/localenv_memo.md`](../../../../.local/localenv_memo.md), especially the nintent update
  flow and the scratch-environment classification;
- [`roadmap.md`](../roadmap.md), governing decisions 2, 5, and 6 in full;
- [`p0/report.md`](../p0/report.md) and `p0/report5.md`, `report6.md`, `report9.md`, `report10.md`;
- the private Phase 0 evidence: `contract-decision.md`, `duplication-inventory.tsv`,
  `module-responsibilities.tsv`, `manifest-impact.tsv`, `artifact-baseline.tsv`,
  `baseline-gates.tsv` under `.local/nctl-modularization/p0/20260727T141512Z/`;
- [`devtests/test_strategy/MANIFEST.md`](../../../../devtests/test_strategy/MANIFEST.md);
- [`nctl/docs/compatibility.md`](../../../../nctl/docs/compatibility.md); and
- the VM roadmap's latest Phase 3 report, to confirm compute is still unseeded.

### 4.2 Frozen inputs from Phase 0

These are decided and must not be re-litigated:

- **Owner:** nintent owns compute-contract semantics.
- **Mechanism:** fixtures generated from the owner, consumed by the non-owner in an ordinary test.
- **Rejected:** shared wire contract (needs nintent schema expansion and probably a migration);
  shared Python package (couples the GitHub-installed Nautobot image to nctl's local uv
  environment); nctl as primary owner.
- **Surviving predicate name:** `is_actionable_lifecycle`. `is_actionable_compute_lifecycle`
  disappears.
- **Deployment consequence accepted:** nintent commit, user push, `--no-cache` rebuild, build-log
  revision verification, runtime-gate rerun.

### 4.3 Planning-time findings that correct Phase 0

Phase 0's `duplication-inventory.tsv` is wrong in one row, silent about two more rules, and its
manifest recount is off by one. Step 1 must re-verify each of the four findings below against the
frozen tuple and record the correction; the roadmap and the Phase 0 evidence are amended in that
same step.

1. **The compute primary-endpoint contract is duplicated, not nctl-only.**
   `duplication-inventory.tsv` records `compute_primary_endpoint` as `nintent_impl: absent`,
   `proposed_owner: nctl`. It is not absent. `nintent/nautobot_intent_catalog/models.py` contains
   `_endpoint_has_usable_ip`, `_endpoint_has_usable_address_contract`, and inside
   `validate_compute_instance_topology` the same candidate filter (`endpoint_type == "primary"`,
   truthy `mac_address`, non-blank `mdns_name`, usable address contract) and the same two outcome
   strings `compute_primary_endpoint_missing` / `compute_primary_endpoint_ambiguous` that
   `nctl/src/nctl_core/sources/desired.py` implements in `select_compute_primary_endpoint`. This is
   the same rule written twice.
2. **The realized-link/source pairing rule is implemented three times.** nintent enforces
   `bool(link) != bool(source)` inline in `DesiredComputePlatform.clean()` and again in
   `DesiredComputeInstance.clean()`; nctl implements it as `_validate_link_source_xnor`. The
   `("derived", "override")` vocabulary is an inline literal in nintent's two field definitions and
   a named `SOURCE_CHOICES` constant in nctl.
3. **Desired-MAC uniqueness is one rule enforced at two different layers, not duplicated code.**
   nintent enforces it with the `nic_unique_desired_mac_address` DB constraint; nctl enforces it at
   snapshot scope in `_validate_endpoint_macs`. Record it as a deliberate two-layer enforcement and
   retain both. It is not a Phase 1 deletion candidate.
4. **`MANIFEST.md` has 26 behavior rows, not 27.** `p0/report10.md` recounted 27 and amended the
   Phase 0 plan accordingly; that recount included the table header. Step 1 re-counts and corrects
   the Phase 0 report so Phase 5's "every row resolves" check starts from a true number.

Two further planning-time facts constrain Step 9:

5. **The running image is already behind local nintent.** The image installs nintent
   `e8732f17ae35d8c72d4d593e8d7311bd234fc0bf`; local nintent HEAD is
   `055496d3e28d2ea6536f660a3ae352b8594279f3`. The nine intervening commits touch only
   `README_DEV.md` and files under `nautobot_intent_catalog/tests/` — no runtime code. The Phase 1
   rebuild therefore lands both that test-only delta and the Phase 1 change; Step 9 must re-verify
   the "test-only" claim against the frozen tuple rather than trusting this paragraph, and the
   report must state that the rebuild crossed more than the Phase 1 commit.
6. **The Dockerfile already verifies the resolved commit, and bakes nauto's seed from the working
   tree.** `devenv/nautobot/Dockerfile` fails the build if pip resolves a commit other than
   `NINTENT_COMMIT`, and writes `/opt/nautobot/build_info.json` plus two image labels. It also
   `COPY`s `nauto/seed/intent_sources.yaml` from the checkout, not from the pinned `NAUTO_COMMIT`.
   That file is currently byte-identical between `1c78af8bdbfc69cafdc293b4082f866de9f271b0` and
   nauto HEAD; Step 9 must re-verify that before rebuilding, because a difference would silently
   change the image's intent sources under cover of a nintent bump. The Dockerfile comment naming
   `interface_contract/p4/plan.md` as the freezing authority is updated to name this plan.

### 4.4 Collision and sequencing rule

`vm_first_realization` is not written and must not start. VM Phase 3 Steps 9–12 must not seed
compute while Phase 1 runs. Recapture the six-repository revision tuple at the start and end of
every long-running gate and around the rebuild. If a component revision moves: finish or terminate
the current command safely, identify whether it affects the disposition table, the fixture, or the
artifact comparison, mark the affected evidence stale, and restart that collection against one new
frozen tuple.

The fixture is the collision-sensitive artifact: it must be generated from one nintent revision, and
that revision must be the one that is pushed and installed.

## 5. The contract decision made concrete

### 5.1 What "exactly one implementation" means here

The roadmap's Phase 1 exit criterion says "exactly one implementation of each shared compute rule
exists". Read alone, that is unachievable under the selected mechanism: nctl cannot import nintent,
so nctl must hold executable code for any rule it applies at read time. Governing decision 2 is the
controlling text and resolves it:

> Where nintent and nctl both implement the same rule, exactly one becomes the semantic owner. The
> other becomes a consumer that either calls the owner or **is proven conformant by generated
> fixtures**. Two independently maintained implementations of one contract are a defect.

Phase 1 therefore delivers **exactly one independently maintained implementation**. nctl's retained
code is fixture-bound: it cannot change semantics without failing an ordinary gate, and it cannot
stay unchanged when the owner changes without failing the freshness gate. The report must state this
interpretation explicitly and must not claim a literal single copy of every function.

The alternative that would satisfy the literal wording — deleting nctl's read-time validation
entirely — is rejected here because it changes behavior: the `DesiredSourceIssue` rows that
`nctl drift --json` emits for a malformed compute row would disappear. Phase 1 is behavior-
preserving. Record this rejection with its reason.

### 5.2 Rule-by-rule disposition

Step 1 freezes this table into `disposition.tsv`. The values below are the plan's proposal; a
disposition may only change with a recorded reason.

| Symbol / rule | Today | Disposition | Reason |
|---|---|---|---|
| `PROVIDER_TYPE_*`, `CONFIG_SCHEMA_VERSION_V1`, `INSTANCE_KIND_*`, `POWER_STATE_*`, `LIFECYCLE_*` | both | shared, owner constants | one closed vocabulary; both sides read it |
| `COMPUTE_LIFECYCLE_CHOICES` (nctl) | nctl only, as a tuple | shared; add `LIFECYCLE_CHOICES` to the owner | nintent has the members but no tuple; the tuple is the vocabulary |
| `VCPUS_*`, `MEMORY_MB_*`, `ROOT_DISK_GB_*`, `VMID_*` | both | shared, owner constants | one bound set |
| `PROVENANCE_*` (4) | both | shared, owner constants | Phase 0 corrected the roadmap on this; they are duplicated |
| `_PLATFORM_CONFIG_KEYS`, `_INSTANCE_CONFIG_KEYS` | both | shared, owner-private | pinned indirectly by unknown-key cases |
| `ComputeContractError` | both | shared code/path/message contract; each side keeps its own class | nctl cannot import the class; the fixture pins `code`, `path`, and `str(exc)` |
| `validate_provider_type`, `validate_config_schema_version`, `validate_platform_config`, `validate_instance_config`, `validate_vmid`, `_validate_bounded_int`, `validate_vcpus`, `validate_memory_mb`, `validate_root_disk_gb`, `_require_json_object`, `_require_non_empty_string` | both | shared; owner defines, nctl is fixture-bound | near-identical today and already drifting in wording |
| `normalize_mac_address` | both | shared; owner defines | canonicalization feeds a fail-closed path on both sides |
| `effective_lifecycle`, `effective_value`, `effective_single_source_value` | both | shared; owner defines | effective values are contract semantics |
| `is_actionable_lifecycle` / `is_actionable_compute_lifecycle` | both, two names | shared; one name `is_actionable_lifecycle` | Phase 0 decision; the second spelling is deleted |
| `validate_compute_lifecycle`, `validate_instance_kind`, `validate_power_state` | nctl only | shared; move the definition to the owner | Phase 0 classified these as contract candidates; nintent already enforces the same vocabularies through Django `choices`, and `validate_instance_config` already inlines the `invalid_instance_kind` check |
| `_validate_source`, `SOURCE_CHOICES` | nctl only as named symbols; nintent inline | shared; owner gains `LINK_SOURCE_CHOICES` and `validate_link_source` | the vocabulary is contract, written three times today |
| `_validate_link_source_xnor` | nctl; nintent twice inline | shared decision, per-side presentation | owner gains `link_source_pairing_is_valid(link_present, source)`; nintent's two `clean()` blocks keep their existing Django field messages, nctl keeps its `link_source_mismatch` error — one rule, three call sites, no message change |
| `_endpoint_has_usable_ip` | both | shared; owner defines `endpoint_has_usable_ip` | pure address predicate; nintent's non-compute `_endpoint_is_usable_local` becomes a consumer of it |
| `_endpoint_has_usable_address_contract` | both | shared; owner defines `endpoint_satisfies_compute_address_contract` | identical rule, identical branches |
| `select_compute_primary_endpoint` + `COMPUTE_PRIMARY_ENDPOINT_MISSING` / `_AMBIGUOUS` | both (nintent inline in `validate_compute_instance_topology`) | shared; owner defines the duck-typed selector and both codes | Section 4.3 finding 1; nintent's call site appends the same two strings it does today |
| `effective_compute_defaults` (nctl) | nctl only | nctl only | nctl-side representation of resolved defaults; never persisted; no nintent equivalent |
| `_resolve_compute_effective_value` (nintent) | nintent only | nintent only | thin owner consumer bound to Django objects |
| storage/bridge "unresolved" completeness check | nintent only | nintent only | write-time completeness; nctl does not act on compute and adding it would emit new source issues |
| `_canonical_mac_or_none` (nctl) | nctl only | nctl only | transport tolerance: `_build_endpoint` must never raise on a bad MAC; the malformed value is separately reported |
| `_build_compute_collections` source-issue policy (duplicate slug, missing control node, one instance per node, dependency-blocked) | nctl only as code | nctl only | nintent enforces the equivalents with DB constraints and relations; the snapshot-scope classification has no nintent counterpart to unify with. Phase 2 relocates it |
| `_validate_endpoint_macs` duplicate-MAC detection | nctl only as code | nctl only | Section 4.3 finding 3: two enforcement layers for one rule; both retained |
| `validate_compute_instance_topology` (nintent) | nintent only | nintent only | Django write-boundary orchestration; it becomes a consumer of the owner's selector |

### 5.3 nctl's retained checks, individually justified

Roadmap Phase 1 item 1 requires each retained nctl check to be justified. The justification is the
same in shape for all of them and must be recorded per check, not once:

- nctl reads desired state over GraphQL from a Nautobot that may be **stale** relative to the
  contract nctl was built against, or **wrong** — a hand-edited row, a partially applied migration,
  a Job that wrote through a path that skipped `full_clean()`, or a compromised read.
- Every retained check converts such a row into a `DesiredSourceIssue` and excludes it from the
  typed collections, instead of letting it reach drift, planning, or actuation.
- Each check therefore has a named consumer behavior: exclusion from `compute_platforms` /
  `compute_instances`, plus a visible issue in the `drift` envelope.

Checks with no such consequence must not be retained. Step 5 must name, for every retained
validator, the exclusion or issue it produces. Any validator that produces neither is a Phase 1
deletion candidate and must be recorded as such rather than kept "for symmetry".

### 5.4 The conformance mechanism

Three artifacts and two gates. The fixture is committed **once**, in the consumer.

**Owner: `nintent/nautobot_intent_catalog/compute_conformance.py`** (Django-free).

- `CONFORMANCE_SCHEMA = "compute-conformance/v1"`.
- `CASES` — an ordered tuple of `{"id": str, "rule": str, "input": <JSON>}`. Inputs are JSON only:
  scalars, objects, and, for the endpoint rules, lists of endpoint attribute objects. No Python
  objects, no timestamps, no paths, no environment values.
- `build_fixture() -> dict` — **executes the owner** over every case and records what the owner
  actually did:
  - success: `{"ok": <JSON-encodable result>}`;
  - failure: `{"error": {"code": ..., "path": ..., "str": str(exc)}}`.
  It also emits a `constants` block read from the owner's module attributes.
- `dumps_fixture() -> str` — deterministic serialization: declaration order preserved, two-space
  indent, `ensure_ascii=False`, trailing newline. Two calls in one process and two calls in
  different processes must produce identical bytes.

The expected values are never hand-written. They are the owner's observed behavior. The owner's
behavior itself is asserted by `nintent/nautobot_intent_catalog/tests/test_compute_contract.py`,
which is extended in Step 2 for the newly owned symbols. This is what makes the fixture a
conformance mechanism rather than a copy: nobody types an expectation twice.

**Owner-side test: `nintent/nautobot_intent_catalog/tests/test_compute_conformance.py`**
(Django-free, runs in the nintent fast gate).

- every public symbol of `compute_contract.py` appears in at least one case, so adding a rule
  without a case fails;
- every constant in the `constants` block resolves to a live owner attribute;
- `dumps_fixture()` is byte-stable across two invocations.

**Generator: `devtests/test_strategy/generate_compute_conformance.py`** (superproject).

Imports `compute_conformance` from the sibling nintent checkout, writes `dumps_fixture()` to
`nctl/tests/fixtures/compute_conformance.json`, and prints the source nintent revision to stdout
(not into the file — the file must stay revision-independent so an unrelated commit does not churn
it).

**Freshness gate: `devtests/test_strategy/test_compute_conformance.py`** (superproject, pytest).

Regenerates in memory from the checked-out nintent and asserts byte-equality with the committed
nctl fixture. This is the gate that fails when the owner changes and the fixture was not
regenerated, and when the fixture is edited by hand.

**Consumer test: `nctl/tests/test_compute_conformance.py`** (nctl ordinary suite).

- loads the committed fixture — no network, no sibling path, no superproject dependency;
- dispatches each case through an explicit `rule -> nctl callable` table and asserts the recorded
  outcome exactly, including `code`, `path`, and `str(exc)` for error cases;
- asserts the `constants` block equals nctl's constants;
- asserts the fixture's rule set covers every public compute-contract symbol nctl exposes, so an
  nctl-only semantic symbol fails the gate instead of drifting quietly;
- for endpoint rules, constructs real `DesiredEndpoint` instances from the case attributes. Fields
  the rule does not read are filled from a placeholder defined in the test file, never in the
  fixture.

Why `str(exc)` is pinned and not only `code`: `DesiredSourceIssue.message` carries `str(exc)` and is
visible in `nctl drift --json`. Pinning the rendered string both proves conformance at the highest
fidelity available and enforces Phase 1's behavior-preservation requirement. A deliberate future
wording change becomes a coordinated matched-version change, which is exactly what governing
decision 6 requires.

**Why the fixture lives in nctl and not in nintent.** nctl's ordinary suite must run from the nctl
checkout alone; it is its own repository. Committing the fixture in nintent as well would recreate
the duplication in data form. The superproject is the only place where both revisions are pinned
simultaneously, so it owns the freshness check.

### 5.5 Behavior that must not change

- every `DesiredSourceIssue` `code`, `path`, `severity`, `scope`, `message`, `evidence` key, and
  `blocked_consumers` value currently produced for any input;
- every envelope error code, every drift code, every exit code;
- compute inertness: zero drift findings, zero plan actions, zero actuation for valid compute rows;
- `nctl drift`, `nctl render dnsmasq`, `nctl render hosts-intent`, `nctl render production` output
  bytes and digests, against the Phase 0 `artifact-baseline.tsv`;
- nintent write-path validation outcomes: the same field errors, in the same fields, with the same
  strings, for model `clean()`, forms, REST, and the YAML loader; and
- the exact set of 14 expected skips in the nintent Django-free gate, plus the 290 runtime cases in
  both Nautobot runtime modes, unless a new test legitimately adds to a count — in which case state
  the new number and what it is.

## 6. Evidence layout

Create `.local/nctl-modularization/p1/<UTC timestamp>/` with mode `0700`, files `0600`:

```text
README.txt
commands.jsonl
revisions-start.tsv
revisions-end.tsv
revisions-matched.tsv
disposition.tsv
p0-corrections.md
owner-diff.txt
consumer-diff.txt
fixture-sha256.txt
divergence-proof.md
gate-results.tsv
source-issue-baseline.tsv
source-issue-after.tsv
artifact-compare.tsv
build-log.txt
build-info.json
logs/
```

`commands.jsonl` records timestamp, working directory, sanitized argument vector, exit code,
duration, and output-file digest. No inherited environment values, tokens, headers, or payload
bodies. `build-log.txt` is retained because the resolved-commit line is the deployment proof; scan
it for credentials before retaining and redact if the base image echoes any.

## 7. Implementation procedure

Each step ends with its own `report<N>.md` and one commit. Steps 0–8 are local and reversible.
Step 9 contains both approval gates.

### Step 0 — Freeze the tuple and create private evidence

1. Re-read every governing input in Section 4.1.
2. Confirm all six repositories are clean; preserve any user changes rather than cleaning them.
3. Record HEAD, branch, upstream relation, submodule pointer, and porcelain status into
   `revisions-start.tsv`.
4. Record the installed nintent commit in the running image, the applied migration state, and the
   desired compute platform/instance row counts — all must still be zero.
5. Create the evidence tree and initialize `commands.jsonl`.
6. Re-run the two gates Phase 1 will most often repeat, to confirm the Phase 0 baseline still holds
   here: nctl ordinary (967 expected) and the nintent Django-free gate (227 with 14 skips).

Gate: one clean frozen tuple, compute still unseeded, both fast baselines reproduce Phase 0's
numbers or the difference is explained.

### Step 1 — Verify and freeze the disposition table

1. Re-derive the duplicated set by symbol-level comparison of
   `nintent/nautobot_intent_catalog/compute_contract.py`, the compute block of
   `nctl/src/nctl_core/sources/desired.py`, and — this is what Phase 0 missed —
   `nintent/nautobot_intent_catalog/models.py`.
2. Confirm or refute each Section 4.3 finding against the frozen tuple. Confirmed findings are
   written into `p0-corrections.md`, and the affected Phase 0 evidence row and any roadmap sentence
   are amended in this step's commit.
3. Run the roadmap's required searches restricted to the compute terms — `compute_contract`,
   `ComputeContractError`, `validate_provider_type`, `validate_instance_config`,
   `normalize_mac_address`, `effective_lifecycle`, `is_actionable_lifecycle`,
   `is_actionable_compute_lifecycle`, `PROVENANCE_` — across active source, tests, fixtures,
   configuration, and current documentation in all six repositories. Classify each match; a match is
   never deletion permission.
4. Write `disposition.tsv` with one row per symbol: `symbol`, `nintent_site`, `nctl_site`,
   `disposition`, `reason`, `consumer_behavior`, `fixture_rule`, `phase1_action`.
5. For every `nctl_only` row, record the Section 5.3 justification: the exclusion or issue it
   produces. Mark any that produces neither.

Gate: every symbol in the duplicated set has a disposition with a reason; Phase 0 corrections are
committed; no symbol is left unclassified.

### Step 2 — Extend the owner

In `nintent` only. No nctl change, no fixture yet.

1. Add to `compute_contract.py`: `LIFECYCLE_CHOICES`, `LINK_SOURCE_CHOICES`,
   `validate_compute_lifecycle`, `validate_instance_kind`, `validate_power_state`,
   `validate_link_source`, `link_source_pairing_is_valid`, `endpoint_has_usable_ip`,
   `endpoint_satisfies_compute_address_contract`, `select_compute_primary_endpoint`,
   `COMPUTE_PRIMARY_ENDPOINT_MISSING`, `COMPUTE_PRIMARY_ENDPOINT_AMBIGUOUS`. Definitions are
   transcribed from whichever side is currently the superset — for the endpoint predicates that is
   nintent's `str(...)`-normalizing variant, which must be verified to produce identical results for
   nctl's pydantic `DesiredEndpoint` before it is adopted.
2. Update the module docstring: it now owns the compute NIC/primary-endpoint contract and the
   realized-link/source vocabulary, not only platform/instance intent.
3. Rewire in-nintent duplicates to the owner, each an exact-behavior refactor:
   - `validate_instance_config` calls `validate_instance_kind` instead of inlining the check
     (verify the code, path, and message are identical first);
   - `models.py` imports `endpoint_has_usable_ip` and `endpoint_satisfies_compute_address_contract`
     and deletes its private copies; `_endpoint_is_usable_local` keeps its current behavior on top
     of the imported predicate;
   - `validate_compute_instance_topology` calls `select_compute_primary_endpoint` and appends the
     returned code, preserving the existing `problems` strings and their order relative to the
     storage/bridge problems;
   - both `clean()` methods call `link_source_pairing_is_valid` and keep their existing Django field
     error strings verbatim.
4. Do **not** rewire model field `choices` to raise `ComputeContractError`. Django `choices` is
   framework enforcement at the write boundary; the owner validator is the vocabulary definition.
   Both derive from one constants tuple, so there is one vocabulary and two enforcement layers.
   Record that as a deliberate decision.
5. Extend `tests/test_compute_contract.py` with hand-written expectations for every newly owned
   symbol, including both primary-endpoint outcome codes and the pairing rule.
6. Run the nintent Django-free gate. Skips must remain 14; state the new case count.

Gate: nintent's suite passes; no nintent write-path message, field, or code changed; the diff is
recorded in `owner-diff.txt`.

### Step 3 — Build the case set and generator

In `nintent` only.

1. Write `compute_conformance.py` per Section 5.4. Cases must cover, at minimum, for each rule: the
   accepted normalization, each rejection code, the boundary values of every bound (min, min−1, max,
   max+1), `None`, empty string, wrong type, and `True`/`False` where a bool would otherwise pass an
   `int` check. For `effective_lifecycle`, all 25 ordered pairs. For `select_compute_primary_endpoint`,
   zero, one, and two candidates plus one case per disqualifying attribute.
2. Write `tests/test_compute_conformance.py` with the three owner-side assertions in Section 5.4.
3. Run the nintent Django-free gate.

Gate: every public owner symbol is covered by at least one case; the fixture serialization is
byte-stable; the case set contains no expectation typed by hand.

### Step 4 — Generate and commit the fixture; add the freshness gate

In the superproject.

1. Write `devtests/test_strategy/generate_compute_conformance.py` and run it. Record the fixture
   digest in `fixture-sha256.txt`.
2. Write `devtests/test_strategy/test_compute_conformance.py` and run it; it must pass against the
   just-generated fixture.
3. Add the gate to the `README_DEV.md` command matrix: working directory superproject root, command
   `uv run --project nctl pytest -q devtests/test_strategy/test_compute_conformance.py`, tier "A
   contract ownership", prerequisite "sibling nintent checkout", no expected skips, required when
   the compute contract changes on either side. Add the corresponding entry to
   `devtests/test_strategy/README.md`.
4. Commit the fixture in `nctl` and the generator/gate/matrix changes in the superproject.

Gate: the fixture exists exactly once in tracked source; the freshness gate passes; the command
matrix documents the new gate and its prerequisite.

### Step 5 — Bind the consumer

In `nctl` only.

1. Rename `is_actionable_compute_lifecycle` to `is_actionable_lifecycle` at its definition and both
   call sites; no second spelling survives.
2. Replace the comment block above the compute section of `sources/desired.py`. It currently
   instructs the reader to keep both copies identical by hand. The replacement states: nintent owns
   these semantics; this code is bound to `tests/fixtures/compute_conformance.json`; changing it
   without the owner fails `tests/test_compute_conformance.py`; changing the owner without
   regenerating fails the superproject gate.
3. Delete any nctl symbol Step 1 classified as producing neither an exclusion nor an issue.
4. Add `tests/test_compute_conformance.py` per Section 5.4.
5. Reconcile `tests/test_sources_desired.py`: delete only assertions that are now exact duplicates
   of a conformance case — a pure input→output or input→code restatement of one rule. Retain every
   test that asserts a *snapshot-level* consequence: row isolation, exclusion from collections,
   `blocked_consumers`, scope, duplicate handling, endpoint-completeness blocking. If in doubt,
   retain. Record every deleted assertion and the conformance case that now owns it.
6. Run the nctl ordinary gate.

Gate: nctl ordinary passes; the conformance test passes; no test was deleted without a named
conformance case taking its place; the deleted-assertion list is in the step report.

### Step 6 — Prove the gate fails on divergence

Three injections, each applied to the working tree only, each reverted before the next, none
committed. Record command, expected failure, observed failure, and revert proof in
`divergence-proof.md`.

1. **Consumer divergence.** Change one nctl bound or one error code — for example `VMID_MIN` to
   `101`. `nctl/tests/test_compute_conformance.py` must fail, naming the case. Revert; rerun to
   green.
2. **Owner divergence.** Change one nintent normalization — for example make
   `normalize_mac_address` return upper case. `devtests/test_strategy/test_compute_conformance.py`
   must fail on byte inequality. Then regenerate the fixture and confirm the nctl conformance test
   fails, proving the divergence propagates to a consumer gate rather than passing on both sides.
   Revert both; rerun to green.
3. **Hand-edited fixture.** Change one expected value in the committed fixture. The superproject
   gate must fail. Revert; rerun to green.

Gate: all three fail as predicted and all three revert clean; `git status` is clean in all six
repositories at the end of the step.

### Step 7 — Re-prove behavior preservation and inertness

1. Run `nctl/tests/test_compute_actuation_inert.py::test_valid_compute_collections_produce_no_drift_and_no_plan_actions`
   and name it in the report — the `compute-inert` manifest row is the inertness proof, and a
   passing full suite is not a substitute.
2. Capture the source-issue surface before and after: for a fixed set of malformed compute and
   endpoint rows, record every emitted `code`, `path`, `scope`, `severity`, `message`,
   `blocked_consumers`, and `evidence` key into `source-issue-baseline.tsv` /
   `source-issue-after.tsv` and diff them. The diff must be empty.
3. Render the deterministic artifacts into a phase-owned temporary directory and compare bytes and
   digests against the Phase 0 `artifact-baseline.tsv`. Record the comparison in
   `artifact-compare.tsv`. A changed digest is a defect, not an update.
4. Run a read-only `nctl drift --json` against the local Nautobot and confirm `source_issues` is
   unchanged in shape and content.
5. Run the full local matrix: nctl ordinary, nintent Django-free, nauto ordinary, nodeutils
   ordinary, Ansible helper, OpenSSH conformance, Ansible conformance, privileged-helper
   integration, and the new compute-conformance gate. Record into `gate-results.tsv`.

Gate: inertness named and passing, source-issue diff empty, artifacts byte-identical, every local
gate green or its failure recorded as pre-existing with the Phase 0 evidence that shows it.

### Step 8 — Manifest and documentation

1. Add one `MANIFEST.md` row: `compute-contract-single-owner`, kind "contract ownership", tier A,
   owning test IDs `devtests/test_strategy/test_compute_conformance.py` and
   `nctl/tests/test_compute_conformance.py`, gate "compute conformance / nctl ordinary", positive
   evidence "generated fixture matches the checked-out owner and the consumer replays it", notes
   "fails on an injected divergence in either direction".
2. Verify every existing manifest row still resolves to an existing, passing test. Phase 1 renames
   no manifested test ID; if Step 5 forced one, update the row in the same commit and rerun its
   gate.
3. Update `nintent/README_DEV.md` to state that `compute_contract.py` is the semantic owner and that
   `compute_conformance.py` publishes the fixture consumed by nctl.
4. Add a short ownership note to `nctl/README.md` pointing at the conformance test. The full
   responsibility map is Phase 5 work; do not write it here.

Gate: all 27 manifest rows (26 existing plus the new one) resolve to an existing passing test; both
READMEs name the owner and the mechanism.

### Step 9 — Coordinated deployment (two approval gates)

1. Commit in `nintent`. State the commit SHA and its contents.
2. Re-verify Section 4.3 finding 5: list the commits between the installed
   `e8732f17ae35d8c72d4d593e8d7311bd234fc0bf` and the new commit, and confirm from the diff which
   touch runtime code. Record the list.
3. Re-verify Section 4.3 finding 6: confirm `nauto/seed/intent_sources.yaml` is byte-identical
   between `NAUTO_COMMIT` and the nauto checkout. If it is not, stop — a nintent rebuild must not
   silently change the image's intent sources.
4. **Approval gate 1.** Ask the user to push nintent. Do not push. Do not proceed until the push is
   confirmed and the remote commit is verified.
5. Update `devenv/nautobot/Dockerfile`: `NINTENT_COMMIT` only, plus the comment now naming this plan
   as the freezing authority. Leave `NAUTO_COMMIT` alone.
6. **Approval gate 2.** Ask before rebuilding. Then run `docker compose build --no-cache` from
   `devenv/nautobot`, retaining the full log.
7. Verify the resolved commit three ways: the Dockerfile's own pip `direct_url.json` check passed,
   `/opt/nautobot/build_info.json` reports the expected commit, and the
   `org.clusterintent.nintent-commit` image label matches. All three must agree. A `--no-cache`
   build that reports a different commit is a stop condition.
8. Restart the three Nautobot containers; confirm health and an HTTP response.
9. Run the Nautobot runtime gate in both `--keepdb` and `--clean` modes. State the case counts
   against Phase 0's 290; explain any difference by the new tests this phase added.
10. Record the matched tuple into `revisions-matched.tsv`: superproject, nctl, nintent (local,
    remote, and installed-in-image), nauto, nodeutils, ansible_agdev.

Gate: the installed nintent commit is proven, not assumed; both runtime modes pass; the matched
tuple is recorded. If either approval is declined, stop here and report
`implemented, not deployed` with the exact remaining commands.

### Step 10 — Final reconciliation and report

1. Recapture the revision tuple into `revisions-end.tsv` and confirm nothing moved unexpectedly.
2. Run `./devtests/test_strategy/measure_test_strategy.py --runtime` and record the case counts.
3. Confirm compute is still unseeded and still inert.
4. Write `report.md`: the matched tuple, the disposition table summary, the Phase 0 corrections, the
   conformance mechanism as built, the three divergence proofs, every gate result, every deviation,
   the deleted-assertion list, and the definition-of-done verdict.
5. State explicitly what Phase 2 inherits: the compute block still lives in `sources/desired.py` and
   is now fixture-bound, so Phase 2's move must carry the conformance test's import with it and
   must not change any pinned value.

Gate: one final report with a precise completion state and no unqualified `complete` if any check
was omitted or substituted.

## 8. Verification matrix

| Area | Required proof |
|---|---|
| single ownership | `disposition.tsv` gives every symbol in the duplicated set one owner; no rule is independently maintained on both sides |
| conformance, consumer direction | an injected nctl change fails `nctl/tests/test_compute_conformance.py`, named case recorded |
| conformance, owner direction | an injected nintent change fails `devtests/test_strategy/test_compute_conformance.py`; after regeneration it fails the nctl gate |
| conformance, fixture integrity | a hand-edited fixture fails the superproject gate |
| fixture provenance | the fixture is generated by a script from the owner and exists exactly once in tracked source |
| predicate naming | `is_actionable_compute_lifecycle` appears nowhere in either repository |
| behavior preservation | `DesiredSourceIssue` code/path/scope/severity/message/evidence diff is empty |
| envelope surface | no envelope field, envelope error code, drift code, or exit code changed |
| deterministic artifacts | dnsmasq, hosts-intent, production, and canonical-JSON bytes and digests identical to the Phase 0 baseline |
| compute inertness | `compute-inert` test named and passing; zero desired compute rows |
| nintent write paths | model `clean()`, form, REST, and YAML loader validation produce the same fields, codes, and strings |
| no new coupling | no shared package, no nintent import in nctl, no new runtime dependency, no migration |
| no compatibility artifact | no shim, dual reader, feature flag, or version branch was added |
| deployment | resolved nintent commit proven by the pip check, `build_info.json`, and the image label; both runtime modes pass |
| image side effects | `NAUTO_COMMIT` unchanged and `intent_sources.yaml` byte-identical to the pinned nauto commit |
| test identity | every `MANIFEST.md` row resolves to an existing passing test at every commit |
| documentation | the command matrix, both READMEs, and the manifest name the owner and the mechanism |

## 9. Reporting and completion states

One `report<N>.md` per step, one `report.md` for the phase. Raw output stays under `.local/`; tracked
prose carries conclusions, decisions, and gate verdicts only.

Use the precise states from `README_DEV.md`:

- `complete` — every exit criterion in Section 10 was exercised and passed, including the
  deployment;
- `implemented, not deployed` — everything through Step 8 passed but an approval gate was declined
  or the rebuild has not run;
- `partially complete` — useful work landed and named criteria remain;
- `blocked` — an external condition actually prevents safe progress. A recoverable local test-
  environment defect is not `blocked`.

A passing suite is never by itself proof that a boundary held. Name the specific test: the
`compute-inert` case for inertness, the three divergence proofs for the conformance gate, the
source-issue diff for message preservation.

## 10. Exit criteria

Phase 1 is `complete` only when:

1. every symbol in the duplicated set has a recorded disposition with its reason, and the Phase 0
   inventory corrections are committed;
2. exactly one independently maintained implementation of each shared compute rule exists, with
   Section 5.1's interpretation stated in the report;
3. the conformance mechanism is generated from the owner, committed once, consumed by an ordinary
   nctl test, and freshness-gated at the superproject;
4. all three injected divergences fail their predicted gate and revert clean;
5. `is_actionable_lifecycle` is the only spelling of the predicate in either repository;
6. every retained nctl check names the exclusion or issue it produces;
7. compute remains inert and no compute row, comparator, planner action, reconciler, or actuator was
   added;
8. every `DesiredSourceIssue` code, path, and message, every envelope error code, and every
   deterministic artifact digest is unchanged from the Phase 0 baseline;
9. the nctl ordinary suite, the nintent Django-free gate, the new compute-conformance gate, and the
   Nautobot runtime gate in both modes pass, with case counts stated against Phase 0's numbers;
10. the matched revision tuple is recorded and the installed nintent commit is proven from the build
    rather than assumed; and
11. every omitted or substituted proof is visible in the report and prevents an unqualified
    `complete`.

The outcome is not fewer lines. The outcome is that a future change to a compute rule cannot land on
one side of the repository boundary and stay green on the other.
