# nctl Modularization Phase 2 Implementation Plan: Separate Transport from Domain in the Source and Braindump Layers

Parent: [roadmap.md](../roadmap.md) — Phase 2. Predecessor: [p1/report.md](../p1/report.md).

Status: proposed; nctl-only source restructuring with no cross-repository change and no deployment.

## 1. Goal

Phase 2 makes every GraphQL and REST module in nctl translate protocol into domain types and
protocol errors into domain errors, and nothing else. Domain policy that currently lives inside a
row decoder or a protocol client moves to a named domain owner; presentation that currently lives
inside an operations module moves to the existing `*_render.py` convention; and the error taxonomy
is reduced to the types a caller actually distinguishes.

The phase must answer, and prove:

1. Where exactly does the compute contract, the compute collection assembly, and the source-issue
   classification live after the move, and does the new owner import no HTTP client, CLI, or
   Nautobot runtime — proven by an executable check rather than by inspection?
2. Which symbols in `sources/actual.py` decide *meaning* rather than *shape*, and which of them
   still have a consumer at all?
3. What are the three independent reasons to change inside `braindump.py`, and does the split
   preserve the confirmation boundary, the non-executable prose boundary, and the user-prose /
   AI-prose distinction — positively re-proven, not preserved by inspection?
4. Which of the 58 recorded error types survive, which fold, and what is the exact caller that
   distinguishes each survivor?
5. Is every `DesiredSourceIssue` code, path, scope, severity, message, evidence key, and
   blocked-consumer value byte-identical to the Phase 1 baseline, and is every envelope error code
   and exit-code mapping unchanged?
6. Do the deterministic artifacts, the compute conformance fixture, and every manifest row survive
   the move untouched?

The observable result is:

```text
current
  sources/desired.py (1,228 lines) mixing one pinned GraphQL query, row decoding, the fixture-bound
    compute contract, compute collection assembly, and the source-issue policy
  + sources/actual.py exporting two composition-policy helpers, one of which has no consumer at all
  + braindump.py (858 lines) mixing REST write transport, HTTP status translation, operation
    semantics, envelope construction, and seven near-identical error-to-envelope blocks
  + nautobot.py repeating one httpx-to-domain error translation seven times
  + 58 recorded error types, 29 of them pure code+message constructors, 7 of them wrongly recorded
    as unreachable

to
  a pure nctl_core/compute package that owns the compute contract, the compute row models, and the
    source-issue policy, and imports no HTTP client
  + sources/desired.py reduced to query, decoding, and typed model construction
  + sources/actual.py reduced to allowlisted fact decoding
  + braindump split into REST transport, operation semantics, and envelope/text presentation, with
    one error-to-envelope translation
  + every retained error type naming the caller that distinguishes it, with every envelope code,
    message, and detail payload unchanged
  + identical source issues, identical artifacts, identical fixture, identical manifest coverage
```

Phase 2 does not touch `production/composer.py`, `production/contract.py`, the reconcile executor,
the drift evaluators, or the dnsmasq family beyond the audit findings recorded in Section 4.3.
Those are roadmap Phases 3 and 4.

## 2. Required outputs

Phase 2 produces:

1. this implementation plan;
2. one private evidence directory under `.local/nctl-modularization/p2/<UTC timestamp>/`;
3. a frozen symbol-level disposition table for every symbol leaving `sources/desired.py`,
   `sources/actual.py`, and `braindump.py`, with its destination module, layer, and reason;
4. a re-verified error disposition table covering all 58 rows of the Phase 0 taxonomy, each marked
   `retain` or `fold` with the rule that decided it and the caller that distinguishes each survivor;
5. corrections to the Phase 0 evidence and, where contradicted, to [`roadmap.md`](../roadmap.md),
   committed in the step that finds the contradiction;
6. the new `nctl_core/compute` package and the reduced `sources/desired.py`;
7. the reduced `sources/actual.py` and the relocated or deleted actual-fact policy, with its proof;
8. the braindump transport / operations / presentation split with one error-to-envelope translation;
9. an executable module-boundary test proving the pure domain modules import no HTTP client, CLI, or
   Nautobot client;
10. behavior-preservation evidence: identical source-issue surface against the Phase 1 corpus,
    identical envelope error codes and exit-code mapping, identical deterministic artifacts,
    byte-identical compute conformance fixture, compute still inert;
11. before/after measurements using the Phase 0 method: files, lines, fan-in/fan-out, collected
    cases, runtime, slowest tests;
12. one `report<N>.md` per step under `devdocs/big/nctl_modularization/p2/`; and
13. `devdocs/big/nctl_modularization/p2/report.md` with a final state of `complete`,
    `partially complete`, or `blocked`.

Tracked files Phase 2 may change:

- `devdocs/big/nctl_modularization/p2/plan.md`, `report<N>.md`, `report.md`;
- `devdocs/big/nctl_modularization/roadmap.md` and `devdocs/big/nctl_modularization/p0/*.md`, only
  to correct a fact this phase disproves;
- under `nctl/src/nctl_core/`: the new `compute/` package, `sources/desired.py`,
  `sources/actual.py`, `braindump.py`, the new braindump transport/presentation modules,
  `nautobot.py`, `jobs.py`, `config.py`, `session.py`, `lifecycle.py`, `repo_versions.py`,
  `production/derivation.py`, `cli/main.py`, and the import lines of any module that referenced a
  moved symbol;
- under `nctl/tests/`: the test modules that follow the moved ownership, plus the new
  module-boundary test;
- `nctl/README.md` (the compute-ownership note's paths only — the full responsibility map is Phase
  5);
- `devtests/test_strategy/MANIFEST.md`, only if a manifested test ID moves; and
- `README_DEV.md`, only if a gate's command or prerequisite changes.

Nothing else. In particular: no nintent, nauto, nodeutils, or ansible_agdev change; no change to
`nctl/tests/fixtures/compute_conformance.json`; no reconcile, drift, dnsmasq, production
composition, SSH, or Ansible logic change; no new runtime dependency.

## 3. Authority and safety boundary

### 3.1 Allowed actions

Phase 2 may:

- read and edit the tracked files listed in Section 2;
- run every ordinary offline suite and every gate in the root command matrix, including the Nautobot
  runtime gate in both `--keepdb` and `--clean` modes against the local scratch stack;
- run read-only `nctl` commands against the local Nautobot — `status`, `drift`, `drift --json`,
  `render dnsmasq`, `render hosts-intent`, `render production` into a phase-owned temporary
  directory, `ops list`, `ops show`;
- restart the local scratch Nautobot web, worker, and scheduler containers if the runtime gate needs
  a healthy stack;
- commit in `nctl` and the superproject; and
- remove only the exact disposable resources this phase created.

### 3.2 Prohibited actions

Phase 2 must not:

- push any submodule or move a submodule pointer without the user doing it;
- change `nintent`, rebuild the Nautobot image, or bump `NINTENT_COMMIT` / `NAUTO_COMMIT`;
- regenerate, hand-edit, or move `nctl/tests/fixtures/compute_conformance.json`;
- change any envelope field, envelope error code, event field, artifact field, drift code, exit
  code, CLI flag, command name, or `DesiredSourceIssue` code, path, scope, severity, message,
  evidence key, or `blocked_consumers` value;
- change the exit-code classification in `cli/main.py` (`BRAINDUMP_USAGE_CODES` and every other
  usage/failure mapping) beyond adjusting an import;
- introduce a plugin system, provider abstraction, generic event bus, DI container, or any interface
  with fewer than two current implementations;
- add a compatibility alias, re-export shim, dual reader, or deprecated import path for a moved
  symbol (`README_DEV.md`, breaking-change phase);
- seed a desired or actual compute row, add a compute comparator, planner action, reconciler, or
  actuator, or otherwise make compute non-inert;
- run `nctl reconcile --yes`, `nctl apply`, a lifecycle or Braindump write against the live
  Nautobot, SSH enrollment to a real node, an Ansible playbook against real nodes, nodeutils
  collection against real nodes, ingest, a Nautobot Job apply, or any Proxmox operation;
- write into `ansible_agdev/inventories/generated/`, `nctl.toml`, or any tracked artifact path;
- read or copy `.local/secrets`, authorization headers, private keys, raw public-key blobs,
  Braindump bodies, Alignment Review summaries, or ObjectChange payloads into evidence; or
- weaken strict SSH verification, exact target scoping, Ansible override rejection, plan/apply
  separation, desired-MAC fail-closed behavior, or the non-executable prose boundary.

### 3.3 Stop conditions

Stop the affected step, preserve evidence, and ask rather than widening authority when:

- preserving a `DesiredSourceIssue` value, an envelope error code, or an exit-code mapping and
  completing a move turn out to be mutually exclusive;
- a deterministic artifact's bytes or digest differ from the Phase 1 baseline for any reason other
  than a declared generated-at / generation-ID / observation-timestamp field;
- the compute conformance fixture would have to change to keep a gate green;
- a boundary that Section 5.7 lists as "must be re-proven" has no test that exercises it at its
  normative layer, so the proof would have to be substituted with a narrower one;
- an error type classified `fold` turns out to have a caller that distinguishes it by type;
- the Nautobot runtime gate fails in a way not explained by the Phase 2 diff; or
- any revision in the six repositories moves mid-phase (Section 4.4).

A green suite after a move is never by itself the proof that a boundary held; Section 5.7 names the
specific test for each boundary.

### 3.4 Approval gates

Phase 2 has **no approval gate**. Every action is local, reversible, and inside the scratch
classification: there is no nintent change, no push, no image rebuild, and no live mutation. The
Nautobot runtime gate's `--clean` mode recreates and destroys only the named `test_nautobot`
database, which `.local/localenv_memo.md` and `README_DEV.md` classify as reusable scratch state.

If a stop condition fires, report it and ask; do not convert it into an approval request for a
broader authority.

## 4. Governing inputs and planning-time findings

### 4.1 Required reading before Step 0

- root [`README.md`](../../../../README.md) and [`README_DEV.md`](../../../../README_DEV.md),
  especially the command matrix, lesson 6 (fail closed but truthfully), and lesson 9 (completion
  language);
- [`.local/localenv_memo.md`](../../../../.local/localenv_memo.md) — scratch classification and the
  nintent update flow that Phase 2 must *not* trigger;
- [`roadmap.md`](../roadmap.md), governing decisions 1, 3, 4, and 5 in full, plus the module
  admission rules;
- [`p0/report.md`](../p0/report.md) with `report3.md` (import graph), `report4.md` (responsibility
  map), and `report8.md` (error taxonomy);
- [`p1/report.md`](../p1/report.md) and `p1/report5.md`, `report7.md` — what the compute consumer
  now is and what Phase 2 inherits;
- the private Phase 0 evidence: `module-responsibilities.tsv`, `module-coupling.tsv`,
  `import-edges.tsv`, `layer-violations.tsv`, `error-taxonomy.tsv`, `move-impact.tsv`,
  `manifest-impact.tsv`, `structure-asserting-tests.tsv`, `artifact-baseline.tsv`, and
  `collect_step3.py` under `.local/nctl-modularization/p0/20260727T141512Z/`;
- the private Phase 1 evidence: `source-issue-baseline.tsv`, `source-issue-after.tsv`, and
  `step7/capture_source_issues.py` under `.local/nctl-modularization/p1/<timestamp>/`;
- [`devtests/test_strategy/MANIFEST.md`](../../../../devtests/test_strategy/MANIFEST.md); and
- [`nctl/docs/compatibility.md`](../../../../nctl/docs/compatibility.md) — internal module layout is
  explicitly outside the current-consumer policy; written fields are inside it.

### 4.2 Frozen inputs from earlier phases

These are decided and must not be re-litigated:

- **Compute contract owner:** nintent. nctl's retained read-time validation is fixture-bound and its
  semantics are pinned by `nctl/tests/test_compute_conformance.py` against the committed fixture.
  Phase 2 moves that code; it must not change one pinned value.
- **Source-issue classification is domain policy**, not desired-GraphQL transport (Phase 0 ambiguity
  resolution 6).
- **Braindump splits three ways** — transport client, operation service, text renderer (Phase 0
  responsibility map).
- **`sources/actual.py` and `sources/braindump.py` are transport keeps** — Phase 2 confirms them and
  moves out only what decides meaning.
- **No interface without two current implementations** (governing decision 4). Braindump has exactly
  one REST client and one renderer; the split is by module, not by protocol or abstract base class.
- **Error codes, not Python types, are the CLI-visible contract.** Folding preserves codes.

### 4.3 Planning-time findings

Each finding below was derived at planning time from the frozen tuple in Section 4.4. Step 1 must
re-verify every one against the checkout and record the result; a refuted finding is recorded as
refuted and the plan's proposal for it is withdrawn in that step's report.

1. **`DesiredSourceIssue` has no envelope consumer today.** `source_issues` is produced in
   `sources/desired.py`, carried on `DesiredSnapshot`, and read by nothing in `src/` — no drift
   envelope, no renderer, no CLI surface. The Phase 1 plan's Section 5.4 rationale ("`message` is
   visible in `nctl drift --json`") does not match the current code. The consequence is not that
   messages may change — they are fixture- and test-pinned and Section 5.7 forbids changing them —
   but that the preservation proof is a **snapshot-level capture**, not an envelope diff, and that
   the source-issue policy's only current consumer boundary is exclusion from
   `compute_platforms` / `compute_instances`. Step 1 re-runs the search across `src/` and
   `devtests/` and records the correction in `p1-corrections.md`.
2. **No error class in the Phase 0 taxonomy is actually unreachable.** All seven `unreachable` rows
   are artifacts of the AST heuristic, which counted only literal `raise X(...)` statements:
   - `BraindumpValidationFailedError`, `BraindumpWriteRejectedError`, `ReviewWriteRejectedError` are
     constructed by the `_write_error` / `_review_write_error` factories and raised at the call
     site; three tests in `tests/test_braindump.py` assert them;
   - `ProxmoxFactsReadError` and `ProxmoxObservationError` are pydantic `BaseModel` records in the
     actual snapshot, not exceptions at all;
   - `InventoryTrustError` is *returned as a value* by `inventory_trust`; and
   - `Envelope` is not an error.
   Phase 2 therefore deletes **no** error type as unreachable. Step 1 corrects the classification
   column in the Phase 0 taxonomy.
3. **The only caller that distinguishes a Braindump error distinguishes it by code.**
   `cli/main.py` maps `BRAINDUMP_USAGE_CODES` (eight codes) to `EXIT_USAGE` and everything else to
   `EXIT_FAILURE`; `reconcile/executor.py` reads `getattr(exc, "code", ...)`. No `except`
   clause anywhere names a `BraindumpError`, `LifecycleError`, or `SessionError` subclass. Folding a
   subclass into a code-carrying factory therefore preserves every distinction a consumer can make.
4. **The Phase 0 phase assignments for the production package contradict the roadmap.**
   `module-responsibilities.tsv` marks `production/composer.py`, `production/contract.py`, and
   `production/adapter.py` as phase 2, and `move-impact.tsv` carries a `p2-production-contract` row;
   the roadmap assigns production composition, route resolution, and the validation-versus-digest
   question to Phase 4 item 5. The roadmap governs. Phase 2 does not split either module; Step 1
   corrects the phase column and the move-impact row ID.
5. **`sources/actual.py` exports two pieces of composition policy, and one of them is dead.**
   - `actual_type_problem` decides whether a realized object is *eligible for actual-backed
     composition* — meaning, not shape. Its only consumer is `production/derivation.py`, which is
     also one of the ten recorded layer violations.
   - `missing_required_facts` and `REQUIRED_FACT_BY_CONSUMER` have **no consumer in `src/` at all**.
     The `missing_observed_system` / `missing_mac_address` / `missing_network_interface` skip codes
     they would produce are produced independently by `production/derivation.py:173`,
     `production/composer.py:673`, and `dnsmasq.py:224`, and classified by
     `reconcile/classify.py`. Only `tests/test_sources_actual.py` and two stale docstrings reference
     them.
   Proposal: move `actual_type_problem` beside its single consumer and delete the orphaned helper
   with its test, after Step 4 proves both statements against the checkout.
6. **`dnsmasq.py` contains a second MAC normalization.** `dnsmasq.py::_normalize_mac` is a lenient,
   never-raising normalization used for both desired and observed MACs, independent of the
   fixture-bound `normalize_mac_address`. This is a real duplication, but unifying it would change
   deterministic dnsmasq bytes and touch the `desired-mac-safe-stop` fail-closed path, and the
   dnsmasq family is roadmap Phase 4 item 7. Phase 2 records it in the duplication findings and
   changes nothing in `dnsmasq*.py`.
7. **The compute conformance consumer reads private names through the module object.**
   `tests/test_compute_conformance.py` dispatches with `getattr(desired, rule)` and names
   `_endpoint_has_usable_ip`, `_endpoint_has_usable_address_contract`, and `_validate_source`
   explicitly. The move must carry this consumer: the fixture's `rule` keys are generated by nintent
   and must not change, so only the nctl-side module reference and dispatch table may change, and
   the fixture file must stay byte-identical.

### 4.4 Frozen tuple, collision, and sequencing rule

Planning-time tuple, all six worktrees clean: superproject
`602c4cd09bfe33aaee7f4029bfa16d76864b5d90`, nctl `077ee9c1b2d9da8870f172de2ef172f792a40cd5`,
nintent `84ac0b125c996bcc9c821252c34e84ca967c64f0` (also the installed image revision), nauto
`6dab422a725a2e2e4e24e98079e992d1111c0ef1`, nodeutils `775ed7fad5110a96186a737147b87d3bf450ced2`,
ansible_agdev `66b31c89986d1b2ecfa187a72209d8bd96838fd4`.

`vm_first_realization` is not written and must not start. VM Phase 3 Steps 9–12 must not seed
compute while Phase 2 runs — a seeded compute row would change the source-issue capture and the
inertness proof. Recapture the tuple at the start and end of the phase and around the runtime gate.
If a component revision moves: finish or terminate the current command safely, mark the affected
capture stale, and recollect it against one new frozen tuple.

## 5. The Phase 2 design made concrete

### 5.1 Target module map

| Module | State | Layer | Owns | May import | Must not import |
|---|---|---|---|---|---|
| `compute/model.py` | new | domain | `DesiredComputePlatform`, `DesiredComputeInstance`, `DesiredSourceIssue` | pydantic, stdlib | anything else in `nctl_core` |
| `compute/contract.py` | new | domain | the fixture-bound compute rules: vocabularies, bounds, `ComputeContractError`, validators, `normalize_mac_address`, effective values, `is_actionable_lifecycle`, endpoint predicates, `select_compute_primary_endpoint`, `effective_compute_defaults` | stdlib, pydantic, `compute.model` | any transport, CLI, or orchestration module |
| `compute/collection.py` | new | domain | compute collection assembly and the whole source-issue policy: per-row parsing, duplicate slug, missing control node, one-instance-per-node, dependency blocking, endpoint completeness, desired-MAC malformed/duplicate detection | `compute.model`, `compute.contract` | any transport, CLI, or orchestration module |
| `sources/desired.py` | reduced | transport | `DESIRED_QUERY`, `fetch_desired_snapshot`, the node/endpoint/range/service/placement/dependency models, the `_build_*` row decoders, `DesiredSnapshot`, and the decode-time MAC tolerance wrapper | `nautobot`, `compute.*` | nothing new |
| `sources/actual.py` | reduced | transport | allowlisted actual-fact decoding, Proxmox fact records, actual row decoding | `nautobot` | any domain policy owner |
| `production/derivation.py` | extended | domain | effective operational values **and** the realized-type eligibility rule | `sources.actual` types | — |
| `braindump_client.py` | new | transport | the two REST collection paths, the six write calls, and HTTP-status-to-error translation | `nautobot`, `braindump_errors` | operations, presentation |
| `braindump_errors.py` | new | domain vocabulary | `BraindumpError` and one code-carrying factory per retained code | `nautobot.NautobotError` | operations, transport, presentation |
| `braindump.py` | reduced | operations | input resolution and validation, list/show/create/update/review/delete semantics, the confirmation boundary, record mapping | `sources.braindump`, `braindump_client`, `braindump_errors` | CLI, presentation |
| `braindump_render.py` | new | presentation | `_client_from_config`, the seven `build_braindump_*` envelope builders behind one error translation, the seven `render_*_text` functions | `braindump`, `output`, `config` | transport |
| `sources/braindump.py` | unchanged | transport | GraphQL diary reads | `nautobot` | — |
| `nautobot.py` | deduplicated | transport | HTTP verbs, auth translation, GraphQL error translation, `ping` | httpx, pydantic | any domain module |
| `jobs.py` | audited | transport | Nautobot Job protocol | `nautobot`, `artifacts`, `events` | any domain module |

Every new module satisfies the roadmap's module admission rules; Step 1 records the check per
module, including its consumers and its independent reason to change.

### 5.2 Why the desired models stay where they are

The obvious alternative — extracting every `Desired*` pydantic model into its own module so the
compute domain can import them — is **rejected**, for two reasons that Step 1 must record:

1. The models and the row decoders have one reason to change, not two: a nintent desired-schema
   change alters the query, the decoder, and the model together. Roadmap governing decision 1 says
   responsibility, not line count, authorizes a split.
2. It would rewrite the import line of roughly 30 source and test modules for no ownership gain.

Instead the dependency runs the admissible direction: `sources/desired.py` (transport) imports the
compute domain package, never the reverse. `compute/collection.py` needs the *shape* of decoded
nodes and endpoints, not their module: it takes them as parameters and reads attributes, with the
type names imported under `typing.TYPE_CHECKING` only, so the domain package pulls in no HTTP client
at runtime. Section 5.6's boundary test is the executable proof of that claim, not the annotation
style.

`DesiredSourceIssue` moves into `compute/model.py` because every current producer is a
compute-contract check (the compute rows themselves, and the desired-MAC checks that use the
compute contract's `normalize_mac_address`). If a non-compute producer ever appears, that is the
moment to promote the type to a snapshot-level module — Phase 2 does not pre-create one.

### 5.3 What `sources/desired.py` keeps, and why the retained tolerance stays in transport

After the move `sources/desired.py` holds: the pinned query, `fetch_desired_snapshot`, the typed
models for nodes/endpoints/ranges/overrides/placements/services/dependencies, `DesiredSnapshot`, the
`_build_*` decoders, and `_canonical_mac_or_none`.

That last one stays in transport deliberately: its whole purpose is decode-time tolerance — the
endpoint row must never fail to decode because of a bad MAC, while the malformed raw value is
reported separately by the domain check. It is not a contract rule (Phase 1 classified it
`nctl_only`, and the fixture does not pin it), so it belongs with the decoder that needs it, calling
`compute.contract.normalize_mac_address`.

The module docstring is rewritten: it currently describes VM Phase 3 Step 5 and states that compute
logic is "ported here". After Phase 2 it must state what the module owns now — a transport
boundary — and where the compute semantics live. Roadmap "Delete" item: comments describing a
historical phase rather than the current contract.

### 5.4 The Braindump split

Three independent reasons to change, which is what authorizes the split:

| Boundary | Changes when | Consumers |
|---|---|---|
| `braindump_client.py` | the REST collection paths, payload shape, or HTTP status semantics change | operations only |
| `braindump.py` | the command's semantics change — what is valid input, what counts as confirmed, what "replace a review" means | presentation, tests |
| `braindump_render.py` | the envelope schema or the human text output changes | `cli/main.py` |

What would have gone wrong if they had already been separate: the seven `build_*` functions each
repeat client construction, a `BraindumpError` branch, a `NautobotError` branch, and a `finally:
client.close()`. That is one translation policy written seven times; a new command copies the block
again, and a change to error translation has to be made seven times consistently. Phase 2 replaces
it with one helper that takes the schema name, the empty data model, and the operation callable.

`create_or_replace_review`'s race recovery (POST → 400 → refetch → PATCH) stays in **operations**,
not in the client: deciding that a 400 means "another writer won the uniqueness race" is semantics,
not protocol. The client only maps status codes to error codes.

The renderers move unchanged. `AUTHORSHIP_VALUES`, the schema-name constants, and the record models
stay with operations, because the CLI's `AuthorshipChoice` enum and the envelope schemas are
semantics the operations layer owns.

### 5.5 The error taxonomy applied

Three rules decide every one of the 58 rows. Step 1 records the rule that decided each row.

- **E1 — retain** when any of: a caller distinguishes the type in an `except` clause or an
  `isinstance` check; the type is the single error boundary of a module or public operation (its
  base); it carries a structured attribute a caller reads; or it expresses a fail-closed
  truthfulness distinction of the kind `README_DEV.md` lesson 6 requires — absent versus
  unreadable/corrupt versus rejected, for a durable or security-relevant artifact.
- **E2 — fold** when the type's entire content is a fixed `code` plus a message template plus a
  `detail` payload. It becomes a module-level factory function returning the retained base, with the
  code string, the rendered message, and the detail dictionary preserved **verbatim**.
- **E3 — never delete.** Finding 4.3.2 established that no type is unreachable. No envelope error
  code changes; no code disappears from any envelope.

Proposed application, to be confirmed in Step 1:

| Module | Retain (E1) | Fold (E2) |
|---|---|---|
| `braindump*` | `BraindumpError` (caught in seven places, carries `code`/`detail`) | all 17 subclasses |
| `lifecycle.py` | `LifecycleError` (caught, carries `code`/`detail`) | 4 subclasses |
| `session.py` | `SessionError` (caught, carries `code`/`detail`) | 2 subclasses |
| `config.py` | `ConfigError`, **and** `ConfigNotFoundError` / `ConfigInvalidError` under E1's truthfulness clause — missing config and unparsable config are the same class of distinction as missing versus corrupt SSH store, and neither carries a code that would survive a fold | none |
| `nautobot.py` | `NautobotError`, `NautobotConnectionError` (distinguished by `status.py`), `NautobotGraphQLError` (carries `.errors`) | `NautobotAuthError` only if Step 1 confirms no caller and no test distinguishes it; otherwise retained with its distinguishing consumer named |
| `jobs.py` | `NautobotJobError` — module boundary type, carries the `code` the executor reads | none |
| `repo_versions.py` | `RepoVersionError` — module boundary type; the Phase 0 fold target `ValueError` would erase a module's error identity for no caller benefit. Recorded as a taxonomy correction | none |
| `sources/desired.py` → `compute/contract.py` | `ComputeContractError` — fixture-pinned `code`, `path`, and `str(exc)` | none |
| everything Phase 0 assigned to phase 3 | untouched by Phase 2 | — |

Tests that currently assert a folded type with `pytest.raises(SubclassError)` become
`pytest.raises(BaseError)` plus an explicit `exc.code == "..."` assertion. That is a strictly
stronger assertion, since the code is the consumer contract and the class is not.

### 5.6 The module-boundary proof

The roadmap's definition of done requires "pure domain modules import no CLI, HTTP, Nautobot
runtime, Ansible execution, or subprocess". Phase 2 makes that executable rather than asserted:
`nctl/tests/test_module_boundaries.py` imports each pure domain module in a fresh subprocess and
asserts that `httpx`, `typer`, `nctl_core.nautobot`, and `nctl_core.cli` are absent from
`sys.modules` afterwards.

It covers `nctl_core.compute.model`, `nctl_core.compute.contract`, and `nctl_core.compute.collection`
in Phase 2. It is admissible because it has three current subjects and a named consumer need, and
because Phase 4 extends it to the drift evaluators. It is a test, not a framework: it adds no
runtime abstraction.

### 5.7 Behavior that must not change, and the named proof for each

| Behavior | Named proof |
|---|---|
| every `DesiredSourceIssue` code, path, scope, severity, message, evidence key, `blocked_consumers` | the Phase 1 corpus replayed through `step7/capture_source_issues.py`, diffed against `source-issue-after.tsv`; the diff must be empty |
| compute contract semantics | `nctl/tests/test_compute_conformance.py::test_compute_contract_fixture_replays_exactly` still passes against a **byte-identical** fixture, and the superproject freshness gate still passes |
| compute inertness | `nctl/tests/test_compute_actuation_inert.py::test_valid_compute_collections_produce_no_drift_and_no_plan_actions`, named in the report |
| desired-MAC fail-closed behavior and recovery | `nctl/tests/test_dnsmasq_render.py::test_desired_mac_mismatch_then_resolved_round_trip` (`desired-mac-safe-stop`) |
| Braindump confirmation boundary | the `*_confirmation_mismatch_fails_closed` cases in `tests/test_braindump.py` for create, update, review, delete, and review-delete — each re-run and named |
| user-prose versus AI-prose distinction | `tests/test_braindump.py::test_validate_authorship_*` plus the CLI enum case in `tests/test_cli_braindump.py::test_create_invalid_authorship_choice_is_usage_exit` |
| non-executable prose boundary | `nintent/.../test_desired_node_link_http.py::DesiredNodeLinkRealHttpTests::test_authorized_prose_writes_do_not_change_real_drift_or_plan` (`prose-authority`) in the Nautobot runtime gate — the manifested owner, run in both modes |
| destructive-confirmation boundary | `tests/test_cli_braindump.py` delete/review-delete prompt, `--json` requires `--yes`, decline, and EOF cases |
| exit-code mapping | `tests/test_cli_braindump.py` usage-versus-failure cases, with `BRAINDUMP_USAGE_CODES` unchanged |
| GraphQL/REST decoding | `nctl/tests/test_nautobot.py::test_graphql_returns_data` (`graphql-rest-decoding`) |
| deterministic artifacts | `render dnsmasq`, `render hosts-intent`, `render production` bytes and digests compared with the Phase 0 `artifact-baseline.tsv`, excluding only the declared generated-at / generation-ID / observation-timestamp fields Phase 1 already declared |
| post-mutation evidence and real-HTTP transitions | the Nautobot runtime gate in both modes |
| operation evidence readability | `nctl/tests/test_operations_index.py::test_list_operations_over_real_phase4_layout` |

## 6. Evidence layout

Create `.local/nctl-modularization/p2/<UTC timestamp>/` with mode `0700`, files `0600`:

```text
README.txt
commands.jsonl
revisions-start.tsv
revisions-end.tsv
symbol-disposition.tsv
error-disposition.tsv
policy-in-transport.tsv
duplication-findings.tsv
p0-corrections.md
p1-corrections.md
import-edges-before.tsv
import-edges-after.tsv
module-coupling-before.tsv
module-coupling-after.tsv
package-totals-before.tsv
package-totals-after.tsv
source-issue-before.tsv
source-issue-after.tsv
artifact-compare.tsv
envelope-codes-before.tsv
envelope-codes-after.tsv
gate-results.tsv
logs/
```

`commands.jsonl` records timestamp, working directory, sanitized argument vector, exit code,
duration, and output digest. No inherited environment values, tokens, headers, or payload bodies. No
Braindump body, Alignment Review summary, or private prose enters any file — the Braindump evidence
is schema and code level only.

## 7. Implementation procedure

Each step ends with its own `report<N>.md` and exactly one commit. Every step is local and
reversible; a failing gate stops the step rather than starting the next one.

### Step 0 — Freeze the tuple, reproduce the baselines

1. Re-read every governing input in Section 4.1.
2. Confirm all six repositories are clean; preserve any user change rather than cleaning it. Record
   HEAD, branch, upstream relation, submodule pointer, and porcelain status into
   `revisions-start.tsv`.
3. Confirm compute is still unseeded (zero desired compute platform and instance rows) and that the
   installed nintent revision still matches the local nintent HEAD.
4. Reproduce the Phase 1 exit numbers: nctl ordinary (968 expected), the compute-conformance
   freshness gate, and the fixture digest. Any difference stops the step.
5. Re-run the Phase 0 measurement method with `collect_step3.py`: package totals, tracked file and
   line counts, import edges, and fan-in/fan-out, into the `*-before.tsv` files.
6. Capture the source-issue surface with the Phase 1 corpus and script into `source-issue-before.tsv`,
   and confirm it equals Phase 1's `source-issue-after.tsv`.
7. Capture the deterministic artifacts into a phase-owned temporary directory and confirm they still
   match the Phase 0 `artifact-baseline.tsv` under the Phase 1 exclusion rule.
8. Capture the full set of envelope error codes reachable from `src/` into
   `envelope-codes-before.tsv` — this is the table Step 6 must reproduce exactly.

Gate: one clean frozen tuple, compute unseeded, all Phase 1 numbers reproduced, and every baseline
captured before any edit.

### Step 1 — Audit, verify the findings, and freeze the dispositions

No production or test code changes in this step except the corrections it commits to Phase 0
evidence and the roadmap.

1. Verify each Section 4.3 finding against the checkout. Record confirmed/refuted with the evidence
   for each into `p0-corrections.md` and `p1-corrections.md`.
2. Write `symbol-disposition.tsv`: one row per symbol leaving `sources/desired.py`,
   `sources/actual.py`, or `braindump.py`, with `symbol`, `current_module`, `target_module`,
   `layer`, `reason_to_change`, `consumers`, `fixture_bound`, `test_owner`, and `step`.
3. Write `error-disposition.tsv`: all 58 Phase 0 rows re-verified, each with `retain`/`fold`, the
   rule (E1/E2/E3) that decided it, the exact distinguishing caller for every retained type, the
   preserved code, and the tests that name it.
4. Write `policy-in-transport.tsv` for `sources/actual.py`, `sources/braindump.py`, `nautobot.py`,
   and `jobs.py`: every symbol that decides meaning rather than shape, its consumers, and its
   disposition. Absence of a finding is recorded as a finding.
5. Write `duplication-findings.tsv`: the `dnsmasq.py::_normalize_mac` duplication and anything else
   the audit finds, each with its disposition and the phase that owns it. Phase 2 changes none of
   them.
6. Run the roadmap's required searches restricted to this phase's surface — `DesiredSourceIssue`,
   `class .*Error`, `Envelope[`, `from nctl_core`, `import nctl_core`, `phase`, `legacy`,
   `fallback`, `shim`, `TODO` — across active source, tests, fixtures, configuration, and current
   documentation. Classify each match; a match is never deletion permission.
7. Record the module admission check for each new module in Section 5.1, and record the Section 5.2
   rejection with its reason.
8. List every test module that will move or be renamed, and cross-check it against
   `MANIFEST.md`. Phase 2 expects to rename **no** manifested test ID; if one is unavoidable, the
   row is updated in the same commit as the rename and its gate re-run.

Gate: every symbol leaving a module has a destination and a reason; every error type has a rule and,
if retained, a named distinguishing caller; the Phase 0 phase-column and classification corrections
are committed; no source or test behavior changed.

### Step 2 — Extract the compute contract into a pure package

1. Create `nctl_core/compute/` with `model.py` and `contract.py`, moving the symbols
   `symbol-disposition.tsv` assigns to them. The move is textual: no rule, message, code, bound, or
   vocabulary changes.
2. Make the three private predicates public in their new home
   (`endpoint_has_usable_ip`, `endpoint_satisfies_compute_address_contract`, `validate_link_source`)
   — they are now the domain module's interface to the collection module and the conformance
   consumer. The fixture's `rule` keys are owner-generated and stay exactly as they are.
3. Point `sources/desired.py` at the new package; keep `_canonical_mac_or_none` in transport as
   Section 5.3 requires.
4. Update `tests/test_compute_conformance.py`: the module reference and the dispatch table only. The
   fixture file must not be touched — verify with its digest.
5. Add `tests/test_module_boundaries.py` (Section 5.6) covering `compute.model` and
   `compute.contract`.
6. Run: nctl ordinary, the compute-conformance freshness gate, and the fixture digest check.

Gate: nctl ordinary passes; the conformance consumer passes against an unchanged fixture; the
freshness gate passes; the boundary test proves the new package imports no HTTP client.

### Step 3 — Move the compute collections and the source-issue policy

1. Create `compute/collection.py` with `build_compute_collections` and `validate_endpoint_macs`,
   moving the assembly and the whole source-issue classification. Every issue's code, path, scope,
   severity, message, evidence keys, `blocked_consumers` computation, and ordering is preserved
   textually.
2. Reduce `sources/desired.py` to Section 5.3's contents and rewrite its docstring to state the
   current contract.
3. Extend `tests/test_module_boundaries.py` to `compute.collection`.
4. Split `tests/test_sources_desired.py` along the new ownership: transport decoding cases stay;
   compute collection and source-issue cases move to `tests/test_compute_collection.py`. No
   assertion is deleted, weakened, or merged in this step — this is a move.
5. Re-capture the source-issue surface with the Phase 1 corpus into `source-issue-after.tsv` and
   diff against `source-issue-before.tsv`. The diff must be empty.
6. Run: nctl ordinary, the named `compute-inert` test, and the conformance gates.

Gate: `sources/desired.py` contains no compute rule and no issue classification; the source-issue
diff is empty; the boundary test covers all three compute modules; `compute-inert` is named and
passing.

### Step 4 — Confirm the actual transport boundary

1. Prove or refute finding 4.3.5 against the checkout: enumerate every consumer of
   `actual_type_problem`, `missing_required_facts`, and `REQUIRED_FACT_BY_CONSUMER` in `src/`,
   `tests/`, and `devtests/`.
2. Move `actual_type_problem` beside its single consumer in `production/derivation.py`, with its
   test.
3. If and only if Step 4.1 confirms that `missing_required_facts` and `REQUIRED_FACT_BY_CONSUMER`
   have no `src/` consumer, delete them with their test, recording in the report: the proof of
   non-use, the three retained producers of the same skip codes, and the note that a future roadmap
   needing a per-consumer fact requirement writes it beside the consumer that needs it. If any
   consumer exists, move the pair instead and record that.
4. Confirm the rest of `sources/actual.py` is transport-shaped and record the confirmation — the
   Proxmox fact records and row decoders are shape, not meaning.
5. Update the stale docstrings in `sources/actual.py` and `production/composer.py` that describe the
   old location.
6. Run: nctl ordinary.

Gate: `sources/actual.py` exports no policy that decides meaning; every deletion has a recorded
proof of non-use; the production suites pass unchanged.

### Step 5 — Split Braindump into transport, operations, and presentation

1. Create `braindump_errors.py` with `BraindumpError` and the code-carrying factories (Step 6 folds
   the subclasses; this step may move the existing classes as they are if that keeps the diff
   readable — state which was done).
2. Create `braindump_client.py` with the two collection paths and the six write calls, each mapping
   HTTP status to the existing error code. `_write_error` and `_review_write_error` move here
   unchanged in behavior.
3. Reduce `braindump.py` to operations: input resolution and validation, the six operations, the
   confirmation boundary, the race recovery, and record mapping.
4. Create `braindump_render.py` with `_client_from_config`, the seven `build_*` functions rewritten
   over **one** shared error-to-envelope helper, and the seven `render_*_text` functions moved
   unchanged. The helper must reproduce, for every command, the same envelope schema, the same
   `ok`, the same error `code`, `message`, and `detail`, and the same `client.close()` behavior on
   every path including the token-error path.
5. Update `cli/main.py` imports only. `BRAINDUMP_USAGE_CODES`, the confirmation gate, and every exit
   code stay exactly as they are.
6. Split `tests/test_braindump.py` along the new ownership: transport-status cases to
   `tests/test_braindump_client.py`, operation and confirmation cases stay, envelope/render cases to
   `tests/test_braindump_render.py` if they are currently mixed in. `tests/test_cli_braindump.py`
   keeps its name and its cases.
7. Re-run and name each Section 5.7 Braindump proof: the five confirmation-mismatch cases, the
   authorship cases, the destructive-confirmation cases, and the exit-code cases.
8. Run: nctl ordinary.

Gate: no envelope schema, error code, message, detail, or exit code changed; one error-to-envelope
translation exists; each named Braindump boundary test is re-run and recorded.

### Step 6 — Apply the error taxonomy

1. Fold every type marked `fold` in `error-disposition.tsv` into a factory on its retained base,
   preserving the code string, the rendered message, and the detail payload verbatim.
2. Update the tests that named a folded type to assert the base type plus the exact code.
3. Re-capture the reachable envelope error codes into `envelope-codes-after.tsv` and diff against
   `envelope-codes-before.tsv`. The diff must be empty.
4. Record the final counts: types before, types after, retained, folded, deleted (zero), and the
   distinguishing caller for every survivor.
5. Run: nctl ordinary and the CLI surface tests.

Gate: the envelope-code diff is empty; every retained type names its distinguishing caller; no type
was deleted; every folded code is still produced by the same input.

### Step 7 — Audit and deduplicate the protocol clients

1. Replace the seven identical `except httpx.RequestError -> NautobotConnectionError` blocks in
   `nautobot.py` (`_get`, `rest_get`, `rest_patch`, `rest_post`, `rest_delete`, `rest_download`,
   `graphql`) with one request helper. The message text (`cannot reach {url}: {exc}`), the auth
   handling per verb, and the GraphQL error path stay exactly as they are.
2. Record the `ping` finding: `INTENT_GRAPHQL_TYPES` and the `intent_catalog` / `intent_graphql`
   interpretation are nctl's statement of what it consumes. Decide keep or move with the
   reason-to-change analysis, and record the decision either way — a `keep` is a finding, not a
   silence.
3. Audit `jobs.py` for domain policy and duplicated per-operation translation. `NautobotJobRunner`'s
   status vocabularies, sanitization, and artifact handling are protocol concerns; record the
   confirmation, and record any exception found with its disposition.
4. Run: nctl ordinary and `tests/test_nautobot.py`, naming `graphql-rest-decoding`.

Gate: one error translation per protocol condition in `nautobot.py`; both clients have a recorded
keep/move decision with its reason; no message text changed.

### Step 8 — Re-prove the boundaries and run the full matrix

1. Re-run the source-issue capture and the artifact capture; both diffs must be empty under the
   declared exclusions. Record into `source-issue-after.tsv` and `artifact-compare.tsv`.
2. Verify the compute conformance fixture digest is unchanged from Step 0.
3. Run the complete local matrix and record it into `gate-results.tsv`: nctl ordinary, compute
   conformance, nintent Django-free, nauto ordinary, nodeutils ordinary, Ansible helper, OpenSSH
   conformance, Ansible conformance, privileged-helper integration.
4. Run the Nautobot runtime gate in both `--keepdb` and `--clean` modes. State the case counts
   against Phase 1's 299 and explain any difference by the tests this phase added or moved. Name
   `prose-authority` and `post-mutation-evidence` explicitly as the boundary proofs they carry.
5. Run a read-only `nctl status`, `nctl drift --json`, and `nctl ops list` against the local
   Nautobot and confirm the envelopes are unchanged in shape.

Gate: every gate green or its failure recorded as pre-existing with the Phase 0/1 evidence that
shows it; both runtime modes pass; the named boundary tests are listed with their results.

### Step 9 — Manifest, documentation, and measurement

1. Verify every `MANIFEST.md` row resolves to an existing, passing test. If Phase 2 renamed a
   manifested ID, the row was already updated in that step's commit; confirm it here and re-run its
   gate.
2. Update `nctl/README.md`'s compute-ownership note to the new module paths. Do not write the
   responsibility map — that is Phase 5.
3. Re-run the Phase 0 measurement method into the `*-after.tsv` files: package totals, files, lines,
   import edges, fan-in/fan-out, collected cases, runtime, slowest tests, skips.
4. Record the before/after layering result: the count of recorded layer violations that Phase 2
   removed, the ones it left, and which phase owns each remainder.

Gate: every manifest row resolves; the README paths are correct; before/after measurements use the
same method and every structural change is explained by ownership rather than size.

### Step 10 — Final reconciliation and report

1. Recapture the revision tuple into `revisions-end.tsv` and confirm nothing moved unexpectedly.
2. Run `./devtests/test_strategy/measure_test_strategy.py --runtime` and record the counts.
3. Confirm compute is still unseeded and still inert.
4. Write `report.md`: the tuple, the disposition summaries, the Phase 0/1 corrections, every split
   with its reason-to-change justification, every deletion with its proof of non-use, the named
   boundary proofs with their results, every gate result, every deviation, the measurements, and the
   definition-of-done verdict.
5. State explicitly what Phase 3 inherits: the executor still branches on `action_kind`, the action
   seam specified in `p0` evidence `action-interface.md` is unbuilt, and the error types Phase 0
   assigned to phase 3 (`reconcile/*`, `ssh_*`) are untouched by Phase 2.

Gate: one final report with a precise completion state and no unqualified `complete` if any check
was omitted or substituted.

## 8. Verification matrix

| Area | Required proof |
|---|---|
| transport purity | no row builder and no protocol client contains a domain rule; `policy-in-transport.tsv` records every symbol audited, including the keeps |
| domain purity | `tests/test_module_boundaries.py` proves `compute.model`, `compute.contract`, and `compute.collection` import no `httpx`, `typer`, `nctl_core.nautobot`, or `nctl_core.cli` |
| source-issue preservation | the Phase 1 corpus diff is empty across code, path, scope, severity, message, evidence keys, and `blocked_consumers` |
| compute contract | the committed fixture is byte-identical; the nctl consumer and the superproject freshness gate both pass |
| compute inertness | `compute-inert` named and passing; zero desired compute rows |
| envelope surface | `envelope-codes-before/after.tsv` diff is empty; no envelope field, event field, artifact field, drift code, or exit code changed |
| exit-code mapping | `BRAINDUMP_USAGE_CODES` unchanged; the usage-versus-failure CLI cases re-run and named |
| error taxonomy | every retained type names a caller that distinguishes it; every folded type's code, message, and detail are reproduced verbatim; zero types deleted |
| prose authority | `prose-authority` passes in both Nautobot runtime modes |
| confirmation boundary | the five Braindump confirmation-mismatch cases and the destructive-confirmation cases re-run and named |
| authorship distinction | the authorship validation and CLI enum cases re-run and named |
| deterministic artifacts | dnsmasq, hosts-intent, and production bytes and digests identical to the Phase 0 baseline under the declared exclusions |
| fail-closed MAC behavior | `desired-mac-safe-stop` passes |
| no compatibility artifact | no re-export shim, alias module, dual reader, or deprecated import path was added |
| framework restraint | no interface, plugin system, provider abstraction, event bus, or DI container introduced |
| test identity | every `MANIFEST.md` row resolves to an existing passing test at every commit |
| measurement | before/after files, lines, coupling, cases, runtime, and slowest tests captured with the Phase 0 method |
| scope discipline | `production/composer.py`, `production/contract.py`, the reconcile executor, the drift evaluators, and the dnsmasq family are unchanged except for import lines and stale docstrings |

## 9. Reporting and completion states

One `report<N>.md` per step, one `report.md` for the phase. Raw output stays under `.local/`;
tracked prose carries conclusions, decisions, and gate verdicts only. No Braindump body, Alignment
Review summary, token, or key material appears anywhere.

Use the precise states from `README_DEV.md`:

- `complete` — every exit criterion in Section 10 was exercised and passed;
- `partially complete` — useful work landed and named criteria remain;
- `blocked` — an external condition actually prevents safe progress. A recoverable local
  test-environment defect is not `blocked`.

`implemented, not deployed` does not apply to Phase 2: there is nothing to deploy.

A passing suite is never by itself proof that a boundary held. Name the specific test: the
`compute-inert` case for inertness, `prose-authority` for the prose boundary, the five
confirmation-mismatch cases for the confirmation boundary, the source-issue diff for message
preservation, and the boundary test for domain purity.

## 10. Exit criteria

Phase 2 is `complete` only when:

1. no domain policy remains in a GraphQL row builder, a REST client, or a protocol module, and every
   audited symbol has a recorded disposition — including the keeps;
2. the compute contract, the compute row models, the compute collection assembly, and the
   source-issue classification live in the pure `nctl_core/compute` package, proven by the module
   boundary test to import no HTTP client, CLI, or Nautobot client;
3. `braindump.py` is split into transport, operations, and presentation, with exactly one
   error-to-envelope translation, and each of the three has a recorded independent reason to change;
4. every retained error type names the caller that distinguishes it, every folded type's code,
   message, and detail are reproduced verbatim, and no type was deleted;
5. every envelope error code, envelope field, event field, artifact field, drift code, exit code,
   and CLI flag is unchanged;
6. the `DesiredSourceIssue` surface is byte-identical to the Phase 1 baseline against the same
   corpus;
7. the compute conformance fixture is byte-identical, the nctl consumer test passes, and the
   superproject freshness gate passes;
8. compute remains inert and no compute row, comparator, planner action, reconciler, or actuator was
   added;
9. every deterministic artifact is byte-identical to the Phase 0 baseline under the declared
   exclusions;
10. the nctl ordinary suite, every conformance gate, and the Nautobot runtime gate in both modes
    pass, with case counts stated against Phase 1's numbers;
11. every `MANIFEST.md` row resolves to an existing passing test, and no manifested ID was renamed
    without its row being updated in the same commit;
12. the Phase 0 corrections in Section 4.3 are committed, and any roadmap sentence they contradict is
    amended; and
13. every omitted or substituted proof is visible in the report and prevents an unqualified
    `complete`.

The outcome is not a smaller `sources/desired.py` or a shorter `braindump.py`. The outcome is that
the next agent can change the GraphQL query without touching a contract rule, change a contract rule
without touching a renderer, and add a Braindump operation without copying an error-translation
block for the eighth time.
