# nctl Modularization Phase 5 Implementation Plan: Document, Remeasure, and Report

Parent: [roadmap.md](../roadmap.md) — Phase 5. Predecessor: [p4](../p4/) (`report.md` + `reportex.md`).

Status: proposed. Local, offline, nctl-only, plus tracked documentation. This is the roadmap's final
phase: it closes the remaining Phase 3/4 residuals, writes the documentation the next agent reads,
and proves the whole initiative against the Phase 0 baseline.

## 1. Goal

```text
current
  nctl/README.md "Layout" is a 2-line stub ("all business logic lives here")
  + "Adding a comparator" exists; "Adding a reconciler" does not, though Phase 3 built the seam
  + the module admission rules live only in this roadmap
  + drift/evaluation.py is still 1,036 lines holding node + endpoint evaluation and their
    candidate/ranking rules (Phase 4 residual)
  + no end-to-end proof that the post-refactor kernel equals the Phase 0 baseline

to
  a responsibility map covering every package and every module over ~300 lines
  + both extension seams documented and equally answerable
  + module admission rules recorded where a future change will find them
  + one owner per resource evaluator
  + the full root command matrix green, every MANIFEST row resolving, artifacts byte-identical to
    the Phase 0 baseline, and one final report with the definition-of-done verdict
```

## 2. Inherited state

Planning-time tuple, all six worktrees clean: superproject `79137c4`, nctl `b5b4a44`, nintent
`4f46bc8`, nauto `6dab422`, nodeutils `775ed7f`, ansible_agdev `66b31c8`. nctl ordinary collects
**974**. Phase 0 baseline evidence is `.local/nctl-modularization/p0/20260727T141512Z/`
(`artifact-baseline.tsv`, `artifact-sha256.txt`, `collect_step3.py`, `layer-violations.tsv`).

Open residuals Phase 5 inherits and must close or explicitly record:

| # | Residual | Source |
|---|---|---|
| R1 | node and endpoint evaluation, plus `_rank_node_candidates` / `_node_candidate_score` / `_matching_ip_candidates` / `_interface_candidates_for_endpoint` / `_primary_mac_candidate*`, still live in `drift/evaluation.py` (1,036 lines) | `p4/reportex.md` "Remaining active work" 1 |
| R2 | inventory-composition coordination versus host-assembly helpers in `production/composer.py` (612 lines) undecided | `p4/reportex.md` 2 |
| R3 | Phase 4 baselines and gates not re-run after the `reportex.md` moves | `p4/reportex.md` 3 |
| R4 | the IPAM action-result matrix and direct action-boundary evidence cases still sit in `tests/test_reconcile_executor.py` (2,318 lines) rather than with the handlers that own them | `p3/report8.md`, restated in `p4/plan.md` §2 |

R3 is absorbed by Step 5. R1 is required by the roadmap's definition of done ("drift orchestration is
separate from per-resource evaluation") and is Step 1. R2 and R4 are closed in Step 1 **or** recorded
as deliberate keeps with their reason — absence of a finding is a finding.

Phase 4 has no `report.md` with a final status. Phase 5 does not rewrite it; the Phase 5 report
states the final disposition of every Phase 4 residual.

## 3. Scope

### In scope

`drift/evaluation.py`, `drift/evaluation_snapshot.py` and any new evaluator/rule modules;
`production/composer.py`; the affected `nctl/tests/` modules; `nctl/README.md`;
`devtests/test_strategy/MANIFEST.md`; `README_DEV.md` if a gate's command or prerequisite changes;
`devdocs/big/nctl_modularization/p5/`; and `devdocs/big/nctl_modularization/roadmap.md` only to
correct a fact this phase disproves.

### Hard rules

Everything else is the implementer's call. These four are not:

1. **No observable change.** Envelope fields and error codes, event names and fields, artifact paths
   and fields, drift codes, target statuses, exit codes, CLI flags, command names, and deterministic
   artifact bytes/digests stay identical to the Step 0 capture (declared generation-id/timestamp
   fields excluded). A changed digest is a defect, not an update.
2. **No compute activation.** No comparator, planner action, reconciler, actuator, or seeded compute
   row. Documenting a registration point must not create a stub or empty registration.
3. **No cross-repository or deployment action.** No nintent/nauto/nodeutils/ansible_agdev source
   change, no image rebuild, no submodule push, no submodule-pointer move by the agent (user-owned).
4. **No live actuation.** No `reconcile --yes`, Job apply, SSH enrollment or Ansible run against real
   nodes, nodeutils collection from real nodes, ingest, or Proxmox operation. Read-only `nctl`
   commands, plan-mode `nctl reconcile`, and both runtime-gate modes against the local scratch stack
   are fine.

### Discretion

Module names and granularity, documentation wording and section placement, the order of Steps 1–4,
and whether to combine steps into one commit are the implementer's call. A proposed split may be
dropped if Step 1 refutes its reason to change — record the keep and its reason. New modules satisfy
the roadmap's module admission rules.

## 4. Planning-time findings

Verified against the Section 2 tuple. Step 1 re-verifies and records confirmed/refuted.

1. **`drift/evaluation.py` still holds two evaluators plus their private rules.**
   `evaluate_node_intent` :117 and `evaluate_endpoint_intent` :231 changed for different resource
   reasons; the node-only ranking rules (`_rank_node_candidates` :529, `_node_candidate_score` :561)
   and the endpoint-only candidate rules (`_matching_ip_candidates` :744,
   `_interface_candidates_for_endpoint` :757, `_interface_facts` :794, `_primary_mac_candidate` :804,
   `_primary_mac_candidate_from_facts` :822, `_interface_sort_key` :1031) are pure and independently
   consumed. `evaluate_service_intent` already moved to `drift/service_evaluation.py`, and
   `drift/ip_ranges.py`, `drift/gap_status.py`, `drift/interfaces.py` already exist as pure owners.
   **Proposal:** `drift/node_evaluation.py` and `drift/endpoint_evaluation.py` mirroring
   `service_evaluation.py`, with the pure candidate/ranking rules moved to the existing pure modules
   or to one new one. `drift/evaluation.py` then keeps only the shared result types and fact
   extraction, or disappears. `tests/test_drift_evaluation.py` (726 lines) follows the subject.
2. **21 modules exceed 300 lines** and need a responsibility-map row: `drift/evaluation.py` 1036,
   `reconcile/executor.py` 826, `production/contract.py` 711, `dnsmasq.py` 691, `cli/main.py` 680,
   `production/composer.py` 612, `ssh_enroll.py` 591, `sources/actual.py` 568, `sources/desired.py`
   480, `dnsmasq_apply.py` 430, `production/derivation.py` 420, `compute/contract.py` 392,
   `drift/comparators.py` 391, `observation.py` 380, `braindump.py` 369, `hosts_intent.py` 323,
   `jobs.py` 320, `reconcile/planner.py` 309, `reconcile/ledger.py` 304, `reconcile/ssh_preflight.py`
   303, `drift/evaluation_snapshot.py` 301. Step 1's split changes this list; the map is written
   against the post-Step-1 tree.
3. **`nctl/README.md` "Layout" is `README.md:6-16`** and says only that all business logic lives in
   `src/nctl_core/` plus the compute-contract ownership note (which is correct and stays).
   "Adding a comparator" is `README.md:524-540`; "Conventions" is `:511`. There is no "Adding a
   reconciler" section, although `reconcile/actions/` with `contract.py`/`dispatch.py` and one
   handler per reconciler id has existed since Phase 3.
4. **`MANIFEST.md` has 27 rows.** The `deterministic-rendering` row already points at
   `nctl_core.canonical` (Phase 4, Step 6). Step 5 re-resolves every row rather than trusting it.
5. **Seven packages need a map entry**, not just modules: `cli/`, `compute/`, `drift/`,
   `production/`, `reconcile/`, `reconcile/actions/`, `sources/`, plus the top-level
   transport/render/evidence modules.

## 5. Steps

Each step ends with one `report<N>.md` and one commit. A failing gate stops the step rather than
starting the next one.

### Step 0 — Freeze and baseline

1. Confirm six clean worktrees; record the tuple and the installed image nintent revision.
2. Confirm zero desired compute platform and instance rows.
3. Reproduce nctl ordinary (**974**) and compute conformance.
4. Run the Phase 0 measurement method (`collect_step3.py`) into `*-before.tsv`.
5. Capture the deterministic artifacts (`render dnsmasq`, `render hosts-intent`, `render production`
   into a phase-owned temp dir), `nctl drift --json`, `nctl status`, and a plan-mode
   `nctl reconcile --json`, and diff them against
   `.local/nctl-modularization/p0/20260727T141512Z/artifact-baseline.tsv` now, before any edit. A
   difference here is inherited and must be explained before Step 1 starts.

### Step 1 — Close the inherited residuals

Apply finding 1 (R1). Decide R2 and R4: split if there is an independent reason to change, otherwise
record the keep with its reason. Tests move with their subject; no assertion is deleted, weakened, or
merged. Extend `tests/test_module_boundaries.py` to any new pure module. Update `MANIFEST.md` in the
same commit as any moved owning test ID.

Gate: nctl ordinary; `run_comparators` output for a fixed snapshot identical to Step 0; new pure
modules import only read-models and stdlib.

### Step 2 — Responsibility map in `nctl/README.md`

Replace the "Layout" stub with a map covering each package (finding 5) and each module over ~300
lines (finding 2, recomputed after Step 1): what it owns, what it may import, what it must not. Keep
the existing compute-ownership paragraph. Layer vocabulary is transport / domain / orchestration /
presentation, as used by the roadmap and `tests/test_module_boundaries.py`. Every path named must
exist — verify by script, not by eye.

### Step 3 — Document both extension seams

Add "Adding a reconciler" beside "Adding a comparator": the `reconcile/registry.py` identity and DAG
entry, the `reconcile/actions/` handler contract (`ActionContext` in, `ExecutedAction` out), where
the handler is registered in the dispatch table, `phase` and `needs_client`, the fact that
`planner.build_plan` owns the target set and a handler never widens it, and where the error
translation lives. Refresh the comparator section if Step 1 changed a named path. Restate the
compute-evaluator registration point Phase 4 documented in `drift/registry.py` and point at it from
the README. No stub, no placeholder.

### Step 4 — Record the module admission rules

Put the roadmap's seven admission rules and the "responsibility, not line count" test where the next
change will find them — `nctl/README.md` "Conventions" is the recommended home; a `nctl/docs/` page
linked from both READMEs is equally acceptable. State the interface rule (two current
implementations, or one plus a second named in an approved roadmap) and the four-layer dependency
direction.

### Step 5 — Full matrix, manifest, measurements

1. Run the complete root command matrix from `README_DEV.md`: nctl ordinary, compute conformance,
   nintent Django-free, nauto ordinary, nodeutils ordinary, Ansible helper, Nautobot runtime
   `--keepdb` **and** `--clean`, OpenSSH conformance, Ansible conformance, privileged-helper
   integration, and the measurement entry point. Record case counts against Step 0.
2. Run and name individually, not as "the suite passed": `dnsmasq-convergence`,
   `non-dhcp-ipam-convergence`, `reconcile-host-scope`, `reconcile-dry-plan`, `partial-ipam-progress`,
   `forced-observation-refresh`, `desired-mac-safe-stop`, `compute-inert`, `deterministic-rendering`,
   `unmanaged-no-delete`, `operation-evidence-reader`, `post-mutation-evidence`, `prose-authority`.
3. Verify all 27 `MANIFEST.md` rows resolve to an existing test that runs and passes in its named
   gate — resolve each ID mechanically, do not eyeball the table.
4. Re-run the Phase 0 measurement method into `*-after.tsv`. Record which layer violations the
   initiative removed and which remain.
5. Re-capture the Step 0 artifacts and envelopes and diff. All diffs empty under the declared
   exclusions.

### Step 6 — Final report

Write `p5/report.md` covering the whole initiative:

1. the revision tuple and evidence root;
2. every split across Phases 1–5 with its reason to change, and every deliberate keep with its
   reason;
3. the final disposition of R1–R4;
4. before/after measurements with the same method (files, lines, fan-in/fan-out, collected cases,
   runtime, slowest tests, skips);
5. gate results, named boundary proofs, deviations, and every omitted or substituted proof;
6. the definition-of-done verdict against `roadmap.md` §"Definition of done", using precise status
   language; and
7. the handoff to `vm_first_realization`: where a compute evaluator registers
   (`drift/registry.py::register("compute_instance")`), where a compute reconciler registers
   (`reconcile/registry.py` + `reconcile/reconcilers.py`), where an actuator implements the handler
   interface (`reconcile/actions/`), that nintent owns the compute contract and nctl replays its
   generated fixture, and which safety contracts it inherits unchanged (exact target set, SSH
   preflight fail-closed distinctions, plan/apply separation, evidence retention, desired-MAC
   fail-closed, prose boundary).

Also update `devdocs/big/nctl_modularization/roadmap.md` phase list to reflect the final state, and
state whether the roadmap is `complete`.

## 6. Evidence

Private evidence under `.local/nctl-modularization/p5/<UTC timestamp>/`: tuple captures, before/after
measurement TSVs, artifact and envelope baselines with their comparisons, manifest-resolution output,
and gate results. Raw command output stays there; tracked prose carries conclusions only. No token,
key material, or private prose in any file.

## 7. Exit criteria

Phase 5 is `complete` when:

1. drift orchestration contains no per-resource evaluation logic, and R2/R4 are each closed or
   recorded as a keep with its reason;
2. `nctl/README.md` documents every package and every module over ~300 lines with what it owns, may
   import, and must not import, and every named path exists;
3. "Adding a reconciler" and "Adding a comparator" are both answerable from the README, and the
   compute-evaluator registration point is documented without a placeholder;
4. the module admission rules are recorded in the component documentation;
5. the full root command matrix passes, including both runtime-gate modes and all conformance gates,
   with case counts stated;
6. all 27 `MANIFEST.md` rows resolve to an existing passing test in their named gate;
7. every deterministic artifact and envelope is identical to the Step 0 capture and to the Phase 0
   baseline under the declared exclusions, and no envelope field, error code, event, artifact field,
   drift code, target status, exit code, or CLI flag changed;
8. compute remains inert with zero rows;
9. before/after measurements use the Phase 0 method; and
10. `p5/report.md` carries the initiative-wide verdict and the `vm_first_realization` handoff, with
    every omitted or substituted proof visible and preventing an unqualified `complete`.

The outcome is that the next agent can open `nctl/README.md`, find the owner of any contract, target
set, route, identity, or lifecycle decision, and add one compute evaluator, one reconciler, and one
actuator without editing a 1,000-line module.
