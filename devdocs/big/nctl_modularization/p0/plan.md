# nctl Modularization Phase 0 Implementation Plan: Remeasure, Map Responsibilities, and Freeze the Seam Decisions

Parent: [roadmap.md](../roadmap.md) — Phase 0.

Status: proposed; read-only audit, baseline-measurement, and documentation-only phase.

## 1. Goal

Phase 0 produces the evidence-backed structural map and the approved seam decisions that Phases 1–5
will execute. No production or test source may change.

The phase must answer:

1. What is the current, remeasured structure of `nctl_core` — files, lines, collected cases, runtime,
   and per-module import fan-in/fan-out — and is the roadmap's baseline still true?
2. For every module over roughly 300 lines and every module named in an audit area: what
   responsibilities does it hold, what are its independent reasons to change, who calls it, and does
   it mix transport, domain, orchestration, or presentation?
3. Which rules are implemented twice across nintent and nctl, how have they already diverged, and
   which side observes each rule at write time versus at actuation time?
4. Who owns the compute contract after this roadmap, by which mechanism, and at what deployment
   cost?
5. What is the exact signature of the action-execution interface, which current action kinds
   implement it, what stays in the executor, and how does the exact-target-set owner survive the
   seam?
6. Which of the declared error types are load-bearing (a named caller behaves differently),
   message-only, or unreachable?
7. Which test modules and which `MANIFEST.md` rows does each proposed move touch, and which
   manifested test IDs would be renamed?
8. What is the behavior-preservation reference: the full root command-matrix result and the
   deterministic-artifact bytes and digests that Phase 5 must reproduce byte-identically?

The observable result is one reproducible structural map in which every audit area carries an
explicit `keep` / `split` / `merge` / `defer` decision with its reason-to-change analysis, and every
later-phase edit has a named owner, a named consumer, and a named proof.

Phase 0 does not move code. It freezes the measurements and decisions needed to move it safely.

## 2. Required outputs

Phase 0 produces:

1. this implementation plan;
2. one private evidence directory under `.local/nctl-modularization/p0/<UTC timestamp>/`;
3. an exact repository, installed-package, migration, and environment manifest;
4. remeasured structure: tracked source and test files and lines per package, collected cases,
   suite runtime, slowest tests, skips;
5. a per-module import graph with fan-in, fan-out, layer assignment, and layering violations;
6. a module responsibility map covering every module over roughly 300 lines and every module named
   in an audit area;
7. a cross-repository duplication inventory, the compute contract at minimum;
8. the compute-contract owner decision with the deployment consequence of every rejected candidate;
9. the action-execution interface specification;
10. the complete error-type classification;
11. the required-search classification, including tests that assert module paths, imports, or symbol
    placement;
12. a proposed-move-to-test-module-to-`MANIFEST.md`-row impact map, with every manifested ID that
    would be renamed marked;
13. the baseline root command-matrix result and the deterministic-artifact byte/digest baseline;
14. one `report<N>.md` per step under `devdocs/big/nctl_modularization/p0/`; and
15. `devdocs/big/nctl_modularization/p0/report.md` with a final state of `complete`,
    `partially complete`, or `blocked`.

Only these tracked files may change during Phase 0:

- this plan;
- `devdocs/big/nctl_modularization/p0/report<N>.md`; and
- `devdocs/big/nctl_modularization/p0/report.md`.

One exception is authorized and required if it triggers: if the audit contradicts the parent
roadmap, amend `devdocs/big/nctl_modularization/roadmap.md` explicitly in the same step that found
the contradiction, and record the amendment in that step's report. Do not silently carry a corrected
fact only in the Phase 0 report. Section 4.2 already lists one such candidate.

All collection scripts, raw logs, import-graph dumps, timing data, artifact bytes, and classification
tables remain private under `.local/nctl-modularization/p0/`. No production source, test source,
fixture, golden file, dependency, lock file, component documentation, seed, generated inventory, or
submodule pointer may change.

## 3. Authority and safety boundary

### 3.1 Allowed actions

Phase 0 may:

- read Git revisions, status, diffs, source, tests, fixtures, goldens, documentation, and
  configuration structure in all six repositories;
- inspect installed package metadata, container health, image identity, and applied migration state;
- run every ordinary offline suite and every gate in the root command matrix, including both
  Nautobot runtime modes and the OpenSSH, Ansible, and privileged-helper conformance gates;
- run the measurement entry point `./devtests/test_strategy/measure_test_strategy.py --runtime`;
- create private AST, import-graph, measurement, and classification helpers under the phase evidence
  directory;
- run read-only `nctl` commands against the local Nautobot — `status`, `drift`, `drift --json`,
  `ops list`, `ops show` — and read-only GraphQL query documents;
- render deterministic artifacts into a phase-owned temporary directory to capture the byte/digest
  baseline;
- read desired/actual row counts and schema identity;
- record sanitized private evidence and the tracked documents listed in Section 2; and
- remove only the exact disposable resources created by this phase.

GraphQL queries use HTTP `POST`; that transport is allowed only for a query document containing no
mutation.

### 3.2 Prohibited actions

Phase 0 must not:

- edit, move, rename, split, merge, or delete any production or test module, fixture, or golden file;
- change production code to make measurement, collection, or import-graph extraction easier;
- add a dependency, tracked test plugin, lint rule, or type-checker gate;
- run `nctl reconcile --yes`, `nctl apply`, a lifecycle or Braindump write, SSH enrollment to a real
  node, an Ansible playbook against real nodes, nodeutils collection against real nodes, ingest, a
  Nautobot Job apply, or any Proxmox operation;
- create, update, link, unlink, retire, or delete a live desired or actual row;
- seed a desired compute row or make compute actionable in any way;
- write into `ansible_agdev/inventories/generated/`, `nctl.toml`, desired YAML, or any tracked
  artifact path — every render in this phase targets a phase-owned temporary directory;
- rebuild, restart, migrate, or replace the live Nautobot web, worker, or scheduler containers;
- commit or push a submodule, or move a submodule pointer;
- read or copy `.local/secrets`, authorization headers, private keys, raw public-key blobs, Braindump
  bodies, Alignment Review summaries, or ObjectChange payloads into evidence; or
- weaken strict SSH verification, exact target scoping, Ansible override rejection, plan/apply
  separation, desired-MAC fail-closed behavior, or the non-executable prose boundary.

The presence of a token file may be checked by metadata only. Its contents must never be opened or
printed.

### 3.3 Stop conditions

Stop the affected step, preserve evidence, and do not repair source during this phase when:

- any command mutates live desired state, actual state, a real node, or Proxmox;
- the exact live-versus-disposable target of a gate cannot be distinguished;
- a gate reveals a production defect;
- a revision in any of the six repositories moves while a derived inventory is being built
  (Section 4.3);
- a required decision — the compute-contract owner, the action interface, an error-type
  classification — cannot be made without inventing user intent or changing supported behavior; or
- the baseline command matrix fails in a way that makes "identical meaning" in Phase 5
  unverifiable.

A production defect becomes a named Phase 0 finding and a Phase 1–4 gap. Its correction requires a
separate bounded plan, not an in-phase fix.

A failing baseline gate does not automatically block Phase 0. It must be recorded as a
pre-existing failure with its exact command and output location, so Phase 5 compares against the
truthful baseline rather than an idealized one.

## 4. Governing inputs and planning-time orientation

### 4.1 Required reading before Step 0

- root [`README.md`](../../../../README.md);
- root [`README_DEV.md`](../../../../README_DEV.md) — the command matrix, the completion-language
  rules, and the "every operational value needs one owner" lesson;
- [`.local/localenv_memo.md`](../../../../.local/localenv_memo.md) — environment classes, the
  nintent GitHub-install update flow, and the secrets boundary;
- [`devdocs/vision/refactor/vision.md`](../../../vision/refactor/vision.md), especially item 4;
- the parent [`roadmap.md`](../roadmap.md);
- [`devdocs/big/core_reconcile/roadmap.md`](../../core_reconcile/roadmap.md) and its Phase 4 reports
  — the reconcile executor's original contract;
- [`devdocs/big/braindump/roadmap.md`](../../braindump/roadmap.md) and its final phase report — the
  prose-authority and confirmation boundaries;
- [`devdocs/big/remove_unused_surfaces/roadmap.md`](../../remove_unused_surfaces/roadmap.md) and its
  final phase report — which surfaces are gone and must not return as internal abstractions;
- [`devdocs/big/interface_contract/roadmap.md`](../../interface_contract/roadmap.md) and
  [`p4/report.md`](../../interface_contract/p4/report.md) — the canonical GraphQL read plus narrow
  REST mutation plus read-only UI contract;
- [`devdocs/big/test_strategy/roadmap.md`](../../test_strategy/roadmap.md) and
  [`p4/report.md`](../../test_strategy/p4/report.md) — the risk tiers and the frozen baseline tuple;
- [`devtests/test_strategy/MANIFEST.md`](../../../../devtests/test_strategy/MANIFEST.md) — the
  current statement of what is proven and by which test ID;
- [`devdocs/big/vm/roadmap.md`](../../vm/roadmap.md), [`p3/plan.md`](../../vm/p3/plan.md), and the
  latest report under [`devdocs/big/vm/p3/`](../../vm/p3/) — currently `report3.7.md`;
- [`nctl/docs/compatibility.md`](../../../../nctl/docs/compatibility.md) — which fields are
  consumer contracts and that internal module layout is explicitly outside that policy; and
- [`nctl/README.md`](../../../../nctl/README.md), including the `Layout` stub and the
  `Adding a comparator` section.

Later reports supersede earlier planning snapshots. Historical plans and reports are evidence, not
active consumers; do not rewrite them.

### 4.2 Planning-time observations to re-verify or correct

Observed on 2026-07-27 while this plan was authored. Every number below is orientation only and must
be recaptured by the step that owns it. Three items are candidate roadmap corrections.

Revision tuple (all clean):

| Repository | Planning-time revision |
|---|---|
| superproject | `46ff7c17bc80b6701e4e82be403f25f345e3d887` |
| `nctl` | `55f1a4bad9baffc998203a5003eee1cbcc005462` |
| `nintent` | `055496d3e28d2ea6536f660a3ae352b8594279f3` |
| `nauto` | `6dab422a725a2e2e4e24e98079e992d1111c0ef1` |
| `nodeutils` | `775ed7fad5110a96186a737147b87d3bf450ced2` |
| `ansible_agdev` | `66b31c89986d1b2ecfa187a72209d8bd96838fd4` |

The submodule tuple is identical to the roadmap's baseline; the superproject has advanced by the
commit that added `roadmap.md`. Tracked `nctl` source totals 17,783 lines and tracked tests 19,685
lines, matching the roadmap table.

Candidate roadmap correction 1 — `PROVENANCE_*` is not nintent-only. The roadmap states nintent
"additionally owns the `PROVENANCE_*` constants." Both sides declare all four:
`nintent/nautobot_intent_catalog/compute_contract.py:41-44` and
`nctl/src/nctl_core/sources/desired.py:537-540`. If Step 5 confirms this, amend the roadmap's
"Confirmed duplication" section and move `PROVENANCE_*` from the divergence list to the duplication
list. Phase 1's work item 3 must be amended in the same edit.

Candidate roadmap correction 2 — the nctl-only compute surface is larger than the roadmap lists.
Beyond `validate_compute_lifecycle`, `validate_instance_kind`, `validate_power_state`,
`_validate_source`, and `_validate_link_source_xnor`, nctl also declares
`select_compute_primary_endpoint`, `effective_compute_defaults`, `_canonical_mac_or_none`,
`_endpoint_has_usable_ip`, `_endpoint_has_usable_address_contract`, and the
`COMPUTE_PRIMARY_ENDPOINT_MISSING` / `COMPUTE_PRIMARY_ENDPOINT_AMBIGUOUS` issue codes. These are the
selection and effective-value machinery that `_build_compute_collections` uses, and they are the
part most likely to be domain-owned rather than contract-owned. Step 5 must classify each; Step 6's
decision must state where each lands.

Candidate roadmap correction 3 — executor dispatch is not purely `action_kind`-shaped. There is
exactly one `action_kind` equality branch, `reconcile/executor.py:888`
(`action.action_kind == "dnsmasq_config"`). The remaining dispatch runs through
`_BOOTSTRAP_LEDGER_RECONCILERS = frozenset({"observe_node", "link_actual_node", "reconcile_ipam"})`
at `reconcile/executor.py:74`, which keys on **reconciler id**, not action kind, plus a phase
grouping inside the round loop. Separately, the executor mints `action_kind="render"` records at
`reconcile/executor.py:675`, `686`, `700`, `714`, and `731` for production-inventory regeneration —
a kind that `reconcile/reconcilers.py` does not register. Step 7's interface design must cover all
three dispatch mechanisms, not only the single `action_kind` branch, and must decide whether
`render` becomes a registered reconciler or stays an executor-owned record.

Registered reconcilers and their kinds, from `reconcile/reconcilers.py`:

| Reconciler id | `action_kind` | `mutates` | `requires_observation` |
|---|---|---|---|
| `observe_node` | `observation` | yes | no |
| `link_actual_node` | `ledger_patch` | yes | no |
| `reconcile_ipam` | `job` | yes | no |
| `service_profile` | `playbook` | yes | yes |
| `dnsmasq_config` | `dnsmasq_config` | yes | yes |
| `new_node_baseline` | `playbook` | yes | no |

Error-count discrepancy to resolve with AST, not grep. A `^class .*Error` search over `nctl/src/`
returns 57, matching the roadmap total. The same search returns 18 matches inside `braindump.py`,
while the roadmap says "19 `BraindumpError` subclasses." Step 8 must count with Python AST,
distinguish base classes from subclasses, and include error classes whose names do not end in
`Error`. Report the authoritative number and amend the roadmap if it differs.

Consumers of the nintent contract, for Step 6's blast-radius analysis:
`nintent/nautobot_intent_catalog/models.py`, `loaders.py`, `tables.py`, `views.py`, plus
`tests/test_compute_contract.py` and `tests/test_loaders.py`.

`MANIFEST.md` currently holds 26 behavior rows. Five of them name
`nctl/tests/test_reconcile_executor.py` — the module Phase 3 work item 6 splits:

| Manifest id | Owning test ID |
|---|---|
| `reconcile-dry-plan` | `test_reconcile_executor.py::test_dry_plan_reports_ssh_preflight_without_blocking` |
| `partial-ipam-progress` | `test_reconcile_executor.py::test_reconcile_ipam_partial_conflict_is_not_reported_as_success` |
| `dnsmasq-convergence` | `test_reconcile_executor.py::test_real_multi_round_dnsmasq_content_convergence` |
| `non-dhcp-ipam-convergence` | `test_reconcile_executor.py::test_real_multi_round_ipam_convergence_for_non_dhcp_endpoint` |
| `forced-observation-refresh` | `test_reconcile_executor.py` (module-level, no test ID) |

`forced-observation-refresh` names a module with no test ID. Step 10 must record that as a
pre-existing manifest weakness: a module-level row cannot detect a renamed test. Recommend the
precise ID for Phase 3 to write, but do not edit `MANIFEST.md` in Phase 0.

Other manifest rows pointing at nctl modules that later phases touch:
`reconcile-host-scope` → `test_dnsmasq_apply.py`, `unmanaged-no-delete` → `test_reconcile_planner.py`,
`compute-inert` → `test_compute_actuation_inert.py`, `desired-mac-safe-stop` →
`test_dnsmasq_render.py`, `deterministic-rendering` → `test_production_contract.py`,
`graphql-rest-decoding` → `test_nautobot.py`, `cli-presentation-approval` → `test_cli_surface.py`,
`credential-security` → `test_cli_session.py`, `operation-evidence-reader` →
`test_operations_index.py`.

`nctl/README.md`'s `Layout` section is two bullets at lines 6–9; `Adding a comparator` begins at
line 517. Both are Phase 5 targets.

### 4.3 Collision and sequencing rule

`remove_unused_surfaces`, `interface_contract`, and `test_strategy` are complete prerequisites.
`vm_first_realization` is not written and must not start during this roadmap.

VM Phase 3 Steps 9–12 have no completion report and desired compute rows remain unseeded. VM work
must not seed compute or add compute actuation while Phase 0 runs. At the start and end of every
long-running gate, recapture the six-repository revision tuple. If any component revision moves:

1. finish or terminate the current command safely;
2. identify the changed files and whether they affect the structural map, the duplication inventory,
   the error classification, the manifest impact map, or the artifact baseline;
3. mark every derived inventory stale;
4. restart the affected collection against one new frozen tuple; and
5. record the abandoned tuple without mixing its measurements into the final baseline.

The artifact byte/digest baseline (Step 11) is the most collision-sensitive output: it must be
captured from one tuple, and that tuple must be the one Phase 5 diffs against.

## 5. Evidence layout and schemas

Create the evidence root with mode `0700` and default file mode `0600`, using a UTC timestamp in the
directory name. At minimum, retain:

```text
.local/nctl-modularization/p0/<timestamp>/
  README.txt
  commands.jsonl
  revisions-start.tsv
  revisions-end.tsv
  environment.tsv
  installed-components.tsv
  migrations.txt
  compute-row-counts.tsv
  source-files.tsv
  test-files.tsv
  package-totals.tsv
  collected-cases.tsv
  runtime-summary.tsv
  slowest-tests.tsv
  skips-xfails.tsv
  import-edges.tsv
  module-coupling.tsv
  layer-violations.tsv
  module-responsibilities.tsv
  duplication-inventory.tsv
  contract-decision.md
  action-interface.md
  error-taxonomy.tsv
  search-classification.tsv
  move-impact.tsv
  manifest-impact.tsv
  baseline-gates.tsv
  artifact-baseline.tsv
  artifacts/
  findings.tsv
  logs/
```

`commands.jsonl` records timestamp, working directory, sanitized argument vector, exit code,
duration, and output-file digest. It must not record inherited environment values, tokens, headers,
or live payload bodies.

### 5.1 Module responsibility schema

`module-responsibilities.tsv` has one row per audited module:

| Column | Meaning |
|---|---|
| `module` | repository-relative path |
| `lines` | tracked line count |
| `layer` | `transport`, `domain`, `orchestration`, `presentation`, or `mixed` |
| `responsibilities` | enumerated, one per distinct value/contract/decision owned |
| `reasons_to_change` | the independent triggers that would force an edit |
| `consumers` | importing modules and external callers |
| `imports_out` | modules it imports within `nctl_core` |
| `imports_in` | modules that import it |
| `downward_imports` | imports that cross a layer boundary the wrong way, or `none` |
| `owns_operational_value` | the value/target set/route/identity/lifecycle decision it owns |
| `decision` | `keep`, `split`, `merge`, or `defer` |
| `split_boundary` | for `split`: the exact proposed boundary and each side's owner |
| `would_have_prevented` | what would have gone wrong had they already been separate |
| `phase` | owning phase, 1–5 |
| `admission_check` | which of the roadmap's seven module admission rules each proposed module meets |

A `split` row is invalid unless `reasons_to_change` lists at least two independent reasons,
`split_boundary` names each side's owner and consumers, and `would_have_prevented` is a concrete
statement rather than "clearer code." A `keep` row for a module over 1,200 lines is a legitimate
outcome and must state the single reason to change.

### 5.2 Duplication inventory schema

`duplication-inventory.tsv` has one row per rule implemented on both sides:

| Column | Meaning |
|---|---|
| `rule_id` | stable name for the rule |
| `nintent_impl` | file, symbol, lines, or `absent` |
| `nctl_impl` | file, symbol, lines, or `absent` |
| `textual_identity` | `identical`, `near_identical`, `diverged`, or `one_side_only` |
| `divergence` | the exact behavioral difference, or `none` |
| `nintent_tests` | owning test IDs |
| `nctl_tests` | owning test IDs |
| `observation_time` | `write_time`, `actuation_time`, or `both` |
| `enforcement_need` | why each side needs to observe it, if it does |
| `proposed_owner` | `nintent`, `nctl`, `shared`, or `split_by_time` |
| `mechanism` | `call_owner`, `generated_fixture`, `wire_contract`, or `retained_safety_check` |
| `reason` | evidence for the assignment |

A retained nctl check must be individually justified against a specific threat — a stale read, a
compromised read, or a value that only exists at actuation time. "Defensive" is not a justification.

### 5.3 Error taxonomy schema

`error-taxonomy.tsv` has one row per declared error class in `nctl/src/`:

| Column | Meaning |
|---|---|
| `error_class` | fully qualified name |
| `module`, `line` | declaration site |
| `base` | immediate base class |
| `raise_sites` | files and lines that raise it |
| `catch_sites` | files and lines that catch it specifically |
| `distinguishing_caller` | the caller that behaves differently, or `none` |
| `distinct_behavior` | exactly what that caller does differently |
| `envelope_code` | the envelope error code it produces, or `none` |
| `classification` | `load_bearing`, `message_only`, or `unreachable` |
| `fold_target` | for `message_only`: the retained type and stable code it folds into |
| `phase` | owning phase |

A type caught only by a bare `except SomeBaseError` is `message_only` unless its message is itself a
consumer contract. A type whose envelope code is visible to a CLI or agent consumer keeps that code
regardless of classification: folding the class must not change the emitted code.

### 5.4 Move-impact and manifest-impact schemas

`move-impact.tsv` maps each proposed move to its test surface:

| Column | Meaning |
|---|---|
| `move_id` | stable id for the proposed move |
| `phase` | owning phase |
| `source` | current module/symbol |
| `target` | proposed module/symbol |
| `test_modules` | test modules that exercise the moved code |
| `test_ids_renamed` | test IDs that the move would rename, or `none` |
| `manifest_rows` | affected `MANIFEST.md` ids, or `none` |
| `gate` | the gate that must rerun in the same commit |
| `structure_asserting_tests` | tests that assert a module path, import, or symbol placement |

`manifest-impact.tsv` inverts it: one row per manifest id, listing every proposed move that touches
its owning test, the phase, whether the ID is renamed, and the gate to rerun. Every one of the 26
rows must appear, including rows no move touches — an untouched row is a finding.

### 5.5 Completeness checks

Private validation scripts must fail unless:

- every tracked `nctl_core` module over 300 lines and every module named in an audit area has a
  responsibility row;
- every audit area from the roadmap's "Required audit areas" table has at least one row with a
  `keep`/`split`/`merge`/`defer` decision, including areas whose finding is "no change needed";
- every one of the roadmap's seven "Known ambiguities" has a recorded resolution;
- every `split` row satisfies Section 5.1's validity rule;
- every declared error class appears in `error-taxonomy.tsv` with a classification, and every
  `load_bearing` row names a distinguishing caller;
- every duplication row names both implementations, their tests, and a proposed owner and mechanism;
- every proposed move appears in `move-impact.tsv`, and every renamed manifested ID appears in
  `manifest-impact.tsv`;
- every one of the 26 manifest rows appears in `manifest-impact.tsv`;
- every required-search term is classified with no unclassified active match;
- every measurement names the exact file list and command digest that produced it; and
- the tracked-file digest set is identical at start and end.

## 6. Audit vocabulary and decision rules

### 6.1 Layers

Exactly four, per the roadmap:

- `transport` — translates protocol into domain types and protocol errors into domain errors;
  contains no domain policy;
- `domain` — pure rules; imports no CLI, HTTP client, Nautobot runtime, Ansible execution,
  subprocess, or filesystem-writing module;
- `orchestration` — sequences work, records evidence, decides terminal state; depends on interfaces,
  not on the feature modules that implement them;
- `presentation` — renders a completed envelope and decides nothing.

`mixed` is a valid current assignment and is itself a finding. A module is only `domain` if the
import check proves it — not because its name suggests it.

### 6.2 Decisions

- `keep` — one reason to change; leave it alone. Required for any module whose only defect is size.
- `split` — two or more independent reasons to change, with the Section 5.1 evidence.
- `merge` — two modules share one reason to change, one consumer set, and one risk profile.
- `defer` — a real boundary exists but its second implementation is not yet present, or the change
  belongs to `vm_first_realization`.

Line count, readability, and "it would be more testable" never authorize a `split` on their own.
The last is admissible only when it names a specific external boundary that cannot currently be
exercised at its normative layer.

### 6.3 Reference classifications

Every required-search match is exactly one of:

- `retained_contract` — a current public or consumer-visible contract;
- `duplicated_implementation` — the same rule implemented more than once;
- `layering_violation` — an import or policy on the wrong side of a layer boundary;
- `historical_comment` — a comment or docstring describing a past phase;
- `structure_assertion` — a test asserting a module path, import, or symbol placement; or
- `orphan` — no current consumer.

Matches are classification input, not instructions. A match is never deletion permission.

### 6.4 Interface admission

An interface is admissible only with at least two current implementations, or one current
implementation plus a second named in an approved roadmap. For the action-execution seam the current
implementations are the registered reconcilers in Section 4.2; the named second consumer is the
compute actuator in `vm_first_realization`. Record that justification explicitly — it is the only
thing separating this seam from the provider abstraction the roadmap forbids.

## 7. Implementation procedure

Each step ends with its own `report<N>.md` and one commit. Steps 0–12 are read-only with respect to
source; none requires user approval, because no step runs a live mutation. If any step discovers
that a required measurement cannot be taken without a mutation, stop and ask rather than widening
the authority.

### Step 0 — Freeze the tuple and create private evidence

1. Re-read every governing input in Section 4.1.
2. Confirm the superproject and five submodules have no unexpected dirty or untracked changes.
   Preserve any user changes; never clean or reset them.
3. Record exact HEAD, branch, upstream relation, submodule pointer, and porcelain status for all six
   repositories into `revisions-start.tsv`.
4. Record OS, architecture, Python, uv, pytest, unittest/Django, Git, Docker, OpenSSH, and Ansible
   versions used by the gates.
5. Create the evidence tree and initialize `commands.jsonl`.
6. Record a digest of every tracked source and test file in `nctl` and `nintent`, so Phase 0 can
   prove nothing changed.

Gate: one clean, immutable revision tuple and one private evidence root are recorded; unexpected
user changes are reported, not discarded.

### Step 1 — Reconstruct installed, migration, and VM state

Using read-only inspection, record:

1. live Nautobot version and the health and image identity of web, worker, and scheduler;
2. the installed nintent revision in each of the three processes, and whether it matches the local
   `nintent` worktree revision;
3. applied nintent migrations, confirming `0016_remove_reconciliation_dashboard_surfaces` is the
   head;
4. read-only counts for `DesiredComputePlatform` and `DesiredComputeInstance`, to state truthfully
   whether compute remains unseeded;
5. whether VM Phase 3 state has moved past `report3.7.md`; and
6. any mixed-process or repository/deployment mismatch.

If the installed nintent revision differs from the local worktree, record it as a Phase 1 input: the
matched-version rollout in Phase 1 starts from the installed revision, not the local one.

Gate: repository and installed tuples are distinguishable, migration head is explicit, and the
report can state truthfully that compute is unseeded and inert.

### Step 2 — Remeasure structure and suite baseline

Record into `source-files.tsv`, `test-files.tsv`, `package-totals.tsv`, `collected-cases.tsv`,
`runtime-summary.tsv`, `slowest-tests.tsv`, and `skips-xfails.tsv`:

1. tracked source files and lines per `nctl_core` package and per module;
2. tracked test files and lines;
3. collected cases from `uv run pytest --collect-only -q` in `nctl`;
4. runtime and the twenty slowest tests from `uv run pytest -q --durations=20`;
5. skips and xfails with reasons; and
6. the same file/line measurement for `nintent`'s `compute_contract.py` and its direct consumers.

Line counts use Git-tracked Python files and one frozen classification rule. Record the exact file
lists and command digests, not only totals. Compare against the roadmap table and record every
difference, including "identical."

Gate: every roadmap baseline number is either confirmed or corrected with its measurement method.

### Step 3 — Build the import graph and find layering violations

1. Extract every intra-`nctl_core` import edge with Python AST, recording module, imported module,
   imported symbols, and whether the import is module-level or deferred inside a function.
2. Compute fan-in and fan-out per module into `module-coupling.tsv`.
3. Assign each module a provisional layer per Section 6.1.
4. Record into `layer-violations.tsv` every case where:
   - a candidate `domain` module imports CLI, HTTP client, Nautobot runtime, Ansible execution,
     `subprocess`, or a filesystem-writing module;
   - an orchestration module imports a feature module in order to perform an action;
   - a transport module contains or calls domain policy; or
   - a presentation module makes a decision.
5. Enumerate the executor's imports exactly and classify each as needed-for-orchestration,
   needed-for-action-execution, or needed-for-evidence. The roadmap says twenty concrete feature
   modules; report the measured number and the classification.
6. Record every deferred/in-function import, since those often hide a cycle the seam must not
   recreate.

Gate: the import graph is complete and reproducible; every violation names both sides and the rule
it breaks.

### Step 4 — Build the module responsibility map

Populate `module-responsibilities.tsv` for every module over roughly 300 lines and every module
named in the roadmap's audit-areas table. At minimum:
`reconcile/executor.py`, `drift/evaluation.py`, `sources/desired.py`, `braindump.py`,
`production/composer.py`, `production/contract.py`, `dnsmasq.py`, `cli/main.py`,
`sources/actual.py`, `ssh_enroll.py`, `dnsmasq_apply.py`, `production/derivation.py`,
`drift/comparators.py`, `observation.py`, `hosts_intent.py`, `jobs.py`, `reconcile/planner.py`,
`drift/evaluation_snapshot.py`, `reconcile/ledger.py`, `reconcile/ssh_preflight.py`,
`drift/registry.py`, `reconcile/registry.py`, `reconcile/reconcilers.py`, `reconcile/classify.py`,
`drift/engine.py`, `drift/model.py`, `reconcile/model.py`, `output.py`, `dnsmasq_render.py`,
`dnsmasq_query.py`, `production/adapter.py`, `production/profiles.py`, `sources/braindump.py`,
`inventory_trust.py`, and every `*_render.py`.

Then resolve each of the roadmap's seven known ambiguities explicitly:

1. can `reconcile/reconcilers.py`, `reconcile/classify.py`, and `reconcile/registry.py` own action
   execution, or must execution stay in the executor behind an explicit interface;
2. is `production/contract.py`'s validation schema one responsibility with its canonical-JSON and
   digest utilities, or two, given the digest is an externally consumed artifact contract;
3. do `dnsmasq.py`, `dnsmasq_render.py`, `dnsmasq_query.py`, and `dnsmasq_apply.py` already have
   clean ownership, or do they duplicate skip and finding policy;
4. do `drift/evaluation.py` and `drift/evaluation_snapshot.py` split along a real boundary;
5. which error types have a caller that behaves differently (deferred to Step 8, cross-referenced
   here);
6. is the compute source-issue policy in `sources/desired.py` transport, domain, or a third thing
   belonging beside the drift evaluators; and
7. does any test module name encode implementation structure rather than a contract (deferred to
   Step 9, cross-referenced here).

Record "no finding" as a finding where it applies — for example if `production/derivation.py` has
exactly one reason to change, say so and mark it `keep`.

Gate: every audited module has a decision with its reason-to-change analysis; every known ambiguity
has a recorded resolution; every `split` satisfies Section 5.1.

### Step 5 — Build the cross-repository duplication inventory

1. Diff `nintent/nautobot_intent_catalog/compute_contract.py` against the compute block of
   `nctl/src/nctl_core/sources/desired.py` symbol by symbol, recording textual identity and every
   behavioral divergence.
2. Classify the nctl-only surface from Section 4.2 into contract rules, domain selection rules, and
   transport helpers.
3. Search both repositories for any other rule implemented on both sides — start with
   `nintent/nautobot_intent_catalog/intent_contract.py`, `loaders.py`, `importers.py`, `names.py`,
   and nauto's ingest policy against their nctl counterparts.
4. For each rule, record whether it is observed at write time (nintent Job/model validation), at
   actuation time (nctl read/plan/actuate), or both, and why each side needs to observe it.
5. Record both sides' owning tests: `nintent/.../tests/test_compute_contract.py`,
   `tests/test_loaders.py`, `nctl/tests/test_sources_desired.py`,
   `nctl/tests/test_compute_actuation_inert.py`, and any others found.
6. If the inventory contradicts the roadmap's "Confirmed duplication" section, amend the roadmap in
   this step.

Gate: every duplicated rule has both implementations, both test sets, its divergence, and its
observation time recorded; no rule is assumed identical without a diff.

### Step 6 — Decide the compute-contract owner and mechanism

Evaluate all four candidates the roadmap permits, and record for each: total ownership complexity,
deployment complexity, what fails when the two sides disagree, and what it costs to change the
contract afterwards.

| Candidate | Must be evaluated against |
|---|---|
| nintent-owned with generated conformance fixtures | fixtures must be generated from the owner and consumed by nctl in an ordinary test; no hand-copied fixture counts |
| a small shared wire contract | what nintent must additionally write, and whether it needs a migration |
| a new shared Python package | the real deployment coupling: nintent installs into the Nautobot image from GitHub, nctl is a local `uv` project; this candidate starts at a disadvantage |
| nctl reduced to transport parsing plus actuation-time safety checks | each retained check must be individually justified against a stale or compromised read |

Then write `contract-decision.md` containing:

1. the selected owner and mechanism, with why it produces less total ownership and deployment
   complexity than each rejected candidate;
2. the disposition of every symbol in the duplication inventory — moved, retained with
   justification, or deleted;
3. the single surviving name for the actionable-lifecycle predicate (`is_actionable_lifecycle` versus
   `is_actionable_compute_lifecycle`) and which spelling disappears;
4. the disposition of `PROVENANCE_*`, the nctl-only validators, and the nctl-only selection and
   effective-value machinery;
5. exactly how the conformance gate fails on an injected divergence, and which command runs it;
6. whether nintent must change and therefore whether Phase 1 requires commit, user-owned push,
   `docker compose build --no-cache`, a build-log commit verification, and a Nautobot runtime gate
   rerun; and
7. how compute inertness is preserved across the change.

The decision is a Phase 0 output, not a Phase 1 discovery. Phase 1 implements it without
re-deciding.

Gate: one owner and one mechanism are selected; every rejected candidate has a recorded deployment
consequence; every duplicated symbol has a disposition; the conformance failure mode is specified.

### Step 7 — Specify the action-execution interface

Write `action-interface.md` containing:

1. the exact signature — parameter names and types, return type, and raised error types — expressed
   against the current `ReconcileAction`, `ActionResult`, and executor context;
2. which current action kinds implement it, using the Section 4.2 table, plus an explicit decision
   for the executor-minted `render` kind;
3. how the three current dispatch mechanisms are replaced: the `action_kind == "dnsmasq_config"`
   branch, the `_BOOTSTRAP_LEDGER_RECONCILERS` reconciler-id set, and the round-loop phase grouping;
4. what the executor keeps — round sequencing, evidence, terminal state, lock, operation log — and
   what it must stop importing;
5. how `reconcile/registry.py` remains the sole owner of reconciler identity and DAG ordering, and
   how registration cannot affect behavior or ordering;
6. how the exact target set stays single-owned across the seam: name the one owner and trace it
   through planning, SSH scan, inventory validation, Ansible `--limit`, action result, and
   post-actuation observation, and state which existing test proves each hop;
7. how the SSH preflight boundary, partial-progress evidence, and `mutated=true` semantics survive
   the move, with the named test for each; and
8. the interface-admission justification from Section 6.4.

Explicitly state what this interface is not: no plugin discovery, no provider abstraction, no
registry of registries, no dependency-injection container.

Gate: the signature is concrete enough to implement without further design; every current action kind
has an implementer; the target-set and evidence contracts have a named preservation proof.

### Step 8 — Classify the error taxonomy

1. Extract every error class in `nctl/src/` with Python AST, including classes whose names do not end
   in `Error`, and record base classes.
2. For each, find every raise site and every specific catch site — in production code, in the CLI,
   and in tests.
3. Identify the caller that behaves differently, and what it does differently. A caller that only
   formats the message differently is not distinguishing behavior unless that message is a consumer
   contract.
4. Record the envelope error code each type produces, and confirm no fold would change an emitted
   code.
5. Classify each as `load_bearing`, `message_only`, or `unreachable`, and name the fold target for
   every `message_only` type.
6. Preserve, explicitly, the fail-closed distinctions `README_DEV.md` names: missing versus corrupt
   versus unenrolled versus unreachable versus mismatched. Any classification that collapses two of
   those is a defect in the classification.
7. Report the authoritative count and reconcile it with the roadmap's 57 and its
   "19 `BraindumpError` subclasses."

Gate: every error class has a classification; every `load_bearing` type names its distinguishing
caller; every `message_only` type names its fold target and stable code; no envelope code changes.

### Step 9 — Classify every required-search match

Search active source, tests, fixtures, configuration, and current documentation in both repositories
for the roadmap's required-search list:

```text
compute_contract
ComputeContractError
validate_provider_type
validate_instance_config
normalize_mac_address
effective_lifecycle
is_actionable_lifecycle
is_actionable_compute_lifecycle
PROVENANCE_
action_kind
_execute_action
register_reconciler
registered_reconciler_ids
register(
run_comparators
DesiredSourceIssue
class .*Error
Envelope[
import nctl_core
from nctl_core
subprocess
Path(
phase
p4
legacy
fallback
shim
TODO
```

Record repository, file, line, active or historical context, current consumer, and one classification
from Section 6.3. Additionally:

- find every test that asserts a module path, import structure, or symbol placement, since a
  legitimate move breaks it; each must be re-owned or deleted in a later phase with its reason
  recorded; and
- resolve known ambiguity 7 — list every test module whose name encodes implementation structure
  rather than a contract, and propose the contract-named replacement without renaming anything.

Gate: no active match is unclassified; every structure-asserting test is named with its later-phase
disposition.

### Step 10 — Build the move-impact and manifest-impact maps

1. Assemble every proposed move from Steps 4–7 into `move-impact.tsv` with a stable `move_id` and
   owning phase.
2. For each, name the test modules that exercise the moved code, the test IDs the move would rename,
   the affected `MANIFEST.md` ids, and the gate that must rerun in the same commit.
3. Build `manifest-impact.tsv` covering all 26 manifest rows.
4. Flag every manifest row whose owning entry is a module path without a test ID, starting with
   `forced-observation-refresh`, and recommend the precise ID for the owning phase to write.
5. For Phase 3 specifically, record which parts of `tests/test_reconcile_executor.py` (2,355 lines)
   would move where, and mark
   `test_real_multi_round_dnsmasq_content_convergence` and
   `test_real_multi_round_ipam_convergence_for_non_dhcp_endpoint` as tests that must remain single
   tests traversing the real drift engine, planner, and executor.
6. Record which gates each phase must rerun, using the `README_DEV.md` matrix.

Gate: every proposed move maps to its tests and gates; every renamed manifested ID is listed; every
manifest row is accounted for.

### Step 11 — Capture the behavior-preservation baseline

Run the complete root command matrix and record exact results in `baseline-gates.tsv`:

```bash
cd nctl            && uv run pytest -q --durations=20
cd nintent         && python3 -m unittest discover -s nautobot_intent_catalog/tests
cd nauto           && python3 -m unittest discover -s tests
cd nodeutils       && uv run pytest -q --durations=20
cd ansible_agdev   && python3 -m unittest discover -s roles/nodeutils_pvesh_helper/tests
# superproject root
./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb
./devtests/test_strategy/run_nautobot_runtime_gate.sh --clean
uv run --project nctl pytest -q devtests/test_strategy/test_openssh_conformance.py
uv run --project nctl pytest -q devtests/test_strategy/test_ansible_conformance.py
cd nodeutils       && uv run pytest -q tests/test_pvesh_helper_integration.py
# superproject root
./devtests/test_strategy/measure_test_strategy.py --runtime
```

For each gate record command, working directory, exit code, pass/fail/skip/xfail counts, runtime, and
the exact expected-skip count — the nintent Django-free gate expects 14. A gate that skips a
required test is a failure of that gate, not a pass.

Then capture the deterministic-artifact baseline into `artifact-baseline.tsv` and `artifacts/`:

1. render dnsmasq, hosts-intent, and production artifacts into a phase-owned temporary directory —
   never into `ansible_agdev/inventories/generated/`;
2. record each artifact's byte length and SHA-256, and retain the bytes;
3. capture every tracked golden/snapshot file's digest in `nctl/tests/`; and
4. capture the canonical-JSON and digest outputs that `production/contract.py` and `dnsmasq.py` own,
   through their existing tests.

These digests are the reference Phase 4 and Phase 5 must reproduce byte-identically. A changed digest
later in this roadmap is a defect, not an update.

Recapture the revision tuple into `revisions-end.tsv` and verify the tracked-file digests from
Step 0 are unchanged.

Gate: every matrix gate has a recorded result with the same meaning Phase 5 will compare against;
every deterministic artifact has a retained byte/digest baseline; the tuple and digests are
unchanged.

### Step 12 — Reconcile, decide, and write the final report

1. Rerun every completeness validation from Section 5.5.
2. Reconcile the responsibility map, duplication inventory, contract decision, action interface,
   error taxonomy, search classification, and move/manifest impact maps against each other. A module
   proposed for a split must appear in the move map; a moved symbol must appear in the affected
   module's row.
3. Verify every audit area in the roadmap's table has a decision, and that "no finding" areas are
   recorded as such.
4. Confirm no source, test, fixture, golden, dependency, or submodule pointer changed, and that no
   compute row was seeded.
5. Confirm every roadmap amendment made during Phase 0 is committed and reflected in the final
   report.
6. Remove exactly the disposable resources this phase created and prove them absent while the live
   stack is unchanged.
7. Write one sanitized `report.md`, linking evidence by relative private path description without
   copying secrets or live prose.
8. Assign the final status using Section 9.

Gate: all exit criteria are satisfied or named as blockers; no omitted or substituted check is
hidden.

## 8. Verification matrix

| Area | Phase 0 proof |
|---|---|
| revision | exact clean start/end tuple; tracked source and test digests unchanged |
| installed state | per-process nintent revision, migration head, compute row counts, VM state |
| structure | remeasured files, lines, cases, runtime, slowest tests, skips with exact file lists |
| coupling | complete intra-`nctl_core` import graph with fan-in/fan-out and deferred imports |
| layering | every violation names both sides and the broken rule |
| responsibility | every module over ~300 lines and every audit-area module has a decision plus reason-to-change analysis |
| ambiguities | all seven roadmap known ambiguities resolved |
| absence of finding | every audit area with no change recorded explicitly as `keep` |
| duplication | every duplicated rule diffed, with both test sets and its observation time |
| contract decision | one owner, one mechanism, every rejected candidate's deployment consequence, specified conformance failure mode |
| action interface | concrete signature, every current implementer, target-set and evidence preservation proofs named |
| error taxonomy | every class classified; every `load_bearing` names its distinguishing caller; no envelope code changes |
| fail-closed distinctions | missing/corrupt/unenrolled/unreachable/mismatched remain five distinct types |
| searches | no active match unclassified; every structure-asserting test named |
| test identity | every proposed move mapped to test modules, renamed IDs, manifest rows, and gates |
| manifest coverage | all 26 rows present in the impact map; ID-less rows flagged |
| baseline behavior | every root-matrix gate recorded with counts, runtime, and expected skips |
| deterministic artifacts | retained bytes and digests for dnsmasq, hosts-intent, production, canonical JSON, and every golden |
| isolation | no live mutation, no compute seed, no tracked artifact write, no push |
| restraint | no plugin system, provider abstraction, event bus, or DI container proposed |
| reporting | one `report<N>.md` per step plus one sanitized final report with exact deviations |

## 9. Reporting and completion states

Each step's `report<N>.md` matches the terse, numbers-first style of prior phase reports: the exact
command, the exact count or result, the decision, and any deviation. No prose summaries of work
already visible in the tables.

The final `report.md` must contain:

- execution window and private evidence root;
- exact starting and ending repository and installed tuples;
- environment, migration, and compute-inertness state;
- the remeasured structure table with every difference from the roadmap baseline;
- the coupling and layering findings;
- the responsibility map summary by decision, with every `split` justification;
- the resolution of all seven known ambiguities;
- the duplication inventory summary and the compute-contract decision with rejected candidates;
- the action-interface specification summary;
- the error-taxonomy counts by classification;
- the search classification counts and every structure-asserting test;
- the move and manifest impact summary, including every renamed manifested ID;
- the baseline gate results and the artifact byte/digest baseline location;
- every roadmap amendment made during the phase;
- every failure, omission, substitution, deviation, and concurrent revision change; and
- proof that no source or test file changed.

Use these states:

- `complete` — every audit area has a decision with its reason-to-change analysis; the
  compute-contract owner and mechanism are chosen with their deployment consequence stated; the
  action interface is specified; the error classification is complete; every manifested test ID that
  would move is listed; measurements are reproducible; the baseline matrix and artifact digests are
  captured; and no source or test file changed;
- `partially complete` — the map is useful but one or more audit area, decision, classification, or
  baseline gate remains incomplete; or
- `blocked` — the tuple cannot be frozen, a required decision cannot be made without new authority,
  or the baseline cannot be captured safely.

A pre-existing failing gate does not by itself prevent `complete`, provided it is recorded truthfully
as the baseline and assigned to an owning phase. An undecided audit area, an unclassified error type,
a missing manifest impact row, an uncaptured artifact baseline, a mixed revision tuple, or a changed
source file does prevent `complete`.

Do not describe a partial classification as a decision, and do not describe a passing narrower suite
as a captured gate baseline.

## 10. Exit criteria

Phase 0 is `complete` only when:

- every audit area in the roadmap's table has a `keep`/`split`/`merge`/`defer` decision with its
  reason-to-change analysis, including areas whose finding is "no change needed";
- every module over roughly 300 lines and every audit-area module has a responsibility row with
  layer, consumers, reasons to change, and decision;
- every `split` names two independent reasons to change, each side's owner and consumers, and what
  would have gone wrong had they already been separate;
- all seven known ambiguities are resolved;
- the compute-contract owner and mechanism are selected, with the deployment consequence of every
  rejected candidate and a specified conformance failure mode;
- the action-execution interface has a concrete signature, a complete list of current implementers,
  a decision for the executor-minted `render` kind, and named preservation proofs for the exact
  target set, SSH preflight, partial progress, and `mutated=true` evidence;
- every declared error type is classified, every `load_bearing` type names its distinguishing
  caller, every `message_only` type names its fold target, and the five fail-closed SSH distinctions
  remain distinct;
- every required-search match is classified and every structure-asserting test is named with a
  later-phase disposition;
- every proposed move is mapped to its test modules, renamed test IDs, manifest rows, and gates, and
  all 26 manifest rows appear in the impact map;
- structure measurements are reproducible from retained commands and exact file lists;
- the complete root command matrix is recorded as the behavior-preservation reference, with expected
  skips explicit;
- the deterministic-artifact byte and digest baseline is retained for dnsmasq, hosts-intent,
  production, canonical JSON, and every tracked golden;
- no plugin system, provider abstraction, generic event bus, or DI container is proposed;
- every roadmap contradiction found is amended in the roadmap, not only in the report;
- no source, test, fixture, golden, dependency, or submodule pointer changed, no compute row was
  seeded, and no submodule was pushed; and
- the final revision tuple is consistent with the starting one.

The success criterion is not a proposed file count. It is a frozen, reviewable map in which every
contract, target set, route, identity, and lifecycle decision has one named intended owner, every
proposed move has a named proof, and Phase 1 can begin without re-deciding anything.
