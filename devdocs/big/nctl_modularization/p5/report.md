# nctl Modularization — Final Report (Phase 5 and the whole initiative)

Status: **complete**.

## 1. Revision tuple and evidence

Final tuple before this report commit: superproject `8f36e41`, nctl `1ca0e74`, nintent `4f46bc8`,
nauto `6dab422`, nodeutils `775ed7f`, ansible_agdev `66b31c8`. The installed Nautobot image carries nintent
`84ac0b1` (Phase 1's matched-version rollout), migrations through
`0016_remove_reconciliation_dashboard_surfaces`.

The superproject's `nctl` submodule pointer still records `2592ee1` and is deliberately **not**
advanced to `1ca0e74` by this phase: moving the pointer and pushing submodules are user-owned
(roadmap "Out of scope"). That single pointer move is the only action left before the tree is
internally consistent.

Phase 5 evidence: `.local/nctl-modularization/p5/20260728T073933Z/` (Step 5 execution) and
`…/20260728T000000Z/` (Step 0 freeze). Initiative baseline:
`.local/nctl-modularization/p0/20260727T141512Z/`.

## 2. Every split, and every deliberate keep

### Splits, with the reason to change that authorized each

| Phase | Split | Independent reasons to change |
|---|---|---|
| 1 | compute contract → nintent as sole semantic owner; nctl keeps fixture-bound read-time validation | contract semantics change with the data model; nctl's retained checks change with what a stale or compromised read may do at actuation time |
| 2 | `sources/desired.py` compute block → `nctl_core.compute` (`contract`, `collection`, `model`) | GraphQL selection changes with the API; compute validation changes with the contract |
| 2 | `braindump.py` → transport boundary, operations, error vocabulary, `braindump_render` | REST translation changes with the endpoint; prose authorization changes with the diary contract; rendering changes with presentation |
| 2 | `sources/actual.py` reduced to allowlisted fact decoding | decoding changes with the Proxmox fact shape, not with what the facts mean |
| 3 | action execution → `reconcile/actions/` (`contract`, `dispatch`, and one handler per reconciler id) | round sequencing changes with evidence and terminal-state rules; each handler changes with its own actuation boundary |
| 4 | `drift.ip_ranges`, `drift.gap_status`, `drift.interfaces`, `nctl_core.canonical` | pure deterministic rules with their own consumers, independent of any evaluator |
| 4 | `production.routes`, `production.model`, `production.report` | route selection changes with connection policy; report translation must not be able to affect inventory construction |
| 4 | `drift.service_evaluation` | service evaluation changes for service reasons |
| 5 | `drift.node_evaluation` and `drift.endpoint_evaluation`; `drift.evaluation` reduced to shared result type and vocabulary | node realization/ranking and endpoint IPAM/interface/MAC selection change for different resource reasons and have different consumers |

### Deliberate keeps, with the reason

| Keep | Reason recorded |
|---|---|
| `_regenerate_production_inventory` stays in `reconcile/executor.py` (P3 plan §514) | it mints executor-owned evidence and sequences generations; it is not a registered reconciler, so putting it behind the handler interface would give the interface a member with no reconciler identity |
| `production/composer.py` not split further (R2, P5 Step 1) | one public composition owner; its private host-assembly and document-rendering helpers serve only that flow, so separating them would create a second public coordination boundary with no independently testable contract |
| IPAM action-result matrix stays in `tests/test_reconcile_executor.py` (R4, P5 Step 1) | it tests the executor's conversion of a handler result into round-level success, mutation evidence, and control flow; the IPAM handler owns the raw result but cannot own that executor boundary without duplicating the executor contract |
| dnsmasq module family keeps one skip/finding owner (P4) | the audit found a single owner already; absence of a finding is a finding |
| desired-MAC uniqueness stays two-layer (P1) | nintent owns the database constraint at write time, nctl detects unsafe duplicate rows at read time; that is two enforcement points for one rule, not two implementations |
| `output.py`, both registries, and the model/contract modules untouched | already single-owner seams; the roadmap's own "existing seams worth preserving" list |

## 3. Disposition of the Phase 4 residuals

| # | Residual | Final disposition |
|---|---|---|
| R1 | node/endpoint evaluation and their candidate/ranking rules in `drift/evaluation.py` | **closed** in P5 Step 1; `drift/evaluation.py` fell from 1,036 to 133 lines and holds only the shared `EvaluationResult`, the target/status vocabulary, and generic value helpers |
| R2 | inventory-composition coordination vs host-assembly helpers | **closed as a deliberate keep** with the reason above |
| R3 | Phase 4 baselines and gates not re-run after the `reportex.md` moves | **closed** by P5 Step 5, which re-ran the entire matrix, both runtime modes, and all artifact/envelope comparisons |
| R4 | IPAM action-result matrix location | **closed as a deliberate keep** with the reason above |

Phase 3 never produced a `report.md`, and Phase 4's says "active additional work". Their final
status is stated here: Phase 3's action seam landed and is proven by the five-handler dispatch table
and the exact-target-set proofs; Phase 4's splits landed and its residual list is closed above.

## 4. Before and after, same method

Initiative-wide, `src/nctl_core`:

| measure | roadmap baseline (nctl `55f1a4b`) | final (nctl `1ca0e74`) |
|---|---|---|
| source files | 68 | 95 |
| source lines | 17,783 | 17,228 |
| `reconcile/executor.py` | 1,261 | 826 |
| `drift/evaluation.py` | 1,236 | 133 |
| `sources/desired.py` | 1,231 | 480 |
| `braindump.py` | 858 | 369 |
| modules over 1,200 lines | 3 | **0** |
| `*Error` classes in `src/` | 57 | 34 |
| collected nctl cases | 967 | 976 |
| Nautobot runtime cases | 290 | 299 |

Phase 5's own before/after (Step 0 → Step 5) is in [`report5.md`](report5.md) §4: 93 → 95 modules,
308 → 317 internal import edges, 974 → 976 cases, and `drift/evaluation.py` fan-out 6 → 2 with
fan-in 4 → 6 — the shape of a module that stopped deciding and became shared vocabulary.

Runtime: nctl ordinary 5.8s for 976 cases; Nautobot runtime 46.3s for 299. Slowest nctl cases are
the `test_status.py` connectivity checks at 0.27–0.31s; the slowest case in the whole matrix is the
privileged-helper traversal at 2.19s. Skips: 14, all in nintent Django-free, all documented.

**Layer violations are unchanged at 15 rows, byte-identical to the Phase 0 baseline.** The Phase 0
method's `domain` set is a hard-coded list of six module names, so every module this initiative
created is classified `orchestration` and can never be flagged by it. The number therefore neither
confirms nor refutes improvement, and it is reported as such. The boundary that is actually enforced
is `tests/test_module_boundaries.py`, which does cover the new pure modules.

## 5. Gates, proofs, deviations

The complete root command matrix passed with stated case counts — nctl 976, compute conformance 1,
nintent Django-free 236 (14 skipped), nauto 110, nodeutils 54, Ansible helper 4, Nautobot runtime
`--keepdb` 299 and `--clean` 299, OpenSSH 2, Ansible 1, privileged-helper 1, plus the measurement
entry point. All 27 `MANIFEST.md` rows (28 IDs) were resolved mechanically and each ran and passed
alone. All thirteen named boundary proofs were invoked individually by ID. Details in
[`report5.md`](report5.md).

Deterministic artifacts: `dnsmasq-records.conf` is byte-identical to both the Step 0 capture and the
Phase 0 baseline with no normalization. `hosts_intent.yml`, `hosts-intent-export.json`,
`production.yml`, and the production report diff to empty against both once the declared
generation-id and timestamp exclusions are applied — this is the same qualified form every phase
since Phase 1 has used, and "byte-identical" holds literally only for dnsmasq. All five envelopes
have identical field sets and identical drift-code and target-status vocabularies. Compute remains
inert: zero platform rows, zero instance rows.

### Deviations and corrections made during Phase 5

1. **The runtime gate was repaired before Step 5 could run.** The inherited blocker was not a
   Nautobot migration defect. `run_nautobot_runtime_gate.sh` preserved a half-built `test_nautobot`
   after any interrupted or failed setup, which made every later run stop on an already-existing
   column — at a later column each time — and it exited `0` when a label collected nothing.
   `044b928` drops the database whenever a run does not reach its test body, requires and prints a
   case count, and refuses to start beside another run; `README_DEV.md` records the lesson.
   [`problem.md`](problem.md) carries the full diagnosis and the evidence that the pinned migration
   set builds from empty cleanly.
2. **One `MANIFEST.md` row was wrong.** `observation-freshness` named a class that does not exist;
   the real owner passes and the row is corrected. Only mechanical execution could find this,
   because the nauto suite passes either way.
3. **One README path was stale.** `nctl/README.md` pointed at `devdocs/vision/core_reconcile/`,
   moved to `devdocs/big/core_reconcile/` before this initiative.

### What this verdict does and does not rest on

- The **error-taxonomy** definition-of-done item ("every retained type names a caller that
  distinguishes it") rests on the Phase 0 classification and the Phase 2 fold, both reported
  `complete`. Phase 5 re-counted the classes (57 → 34) but did not re-audit each caller.
- The same **wrapper defect** that blocked Phase 5 also produced Phase 3's `report8.md` stop and
  Phase 4's un-counted "runtime gate recovery" entry. That P4 entry stated no case count, so it
  could not be distinguished from a zero-case pass; Phase 5's 299/299 is the first counted runtime
  evidence for the post-Phase-3 tree. Earlier phases' runtime claims should be read through that.
- The **layer-violation measurement** cannot see modules created after Phase 0, as stated in §4.

## 6. Definition-of-done verdict

Every bullet of the roadmap's "Definition of done" is met:

| requirement | verdict |
|---|---|
| audit areas have keep/split/merge/defer decisions with reasons | met — P0, 6 splits / 27 keeps / 3 defers, seven ambiguities resolved |
| one semantic owner for the compute contract, conformance proven to fail on divergence | met — P1 performed and restored three divergence injections |
| orchestration depends on an action interface; no action-kind branch or feature-module execution import | met — five handlers dispatch by reconciler id; the one retained `production_render` import serves executor-minted evidence, a decision recorded in the P3 plan |
| drift orchestration separate from per-resource evaluation; compute evaluator registration documented without a placeholder | met — P5 Step 1 and `drift/registry.py`, no stub |
| pure domain modules import no CLI, HTTP, Nautobot runtime, Ansible, or subprocess | met — `tests/test_module_boundaries.py`, extended to the new modules |
| transport modules contain no domain policy or duplicated per-operation error translation | met — P2 |
| every retained error type names a distinguishing caller; envelope codes unchanged | met, inherited — see §5 |
| no plugin framework, provider abstraction, event bus, or DI container | met — the seams are a static handler table and two registries |
| commands, envelopes, events, artifacts, drift codes, exit codes unchanged; deterministic artifacts identical to baseline | met, in the qualified form stated in §5 |
| every `MANIFEST.md` row resolves to an existing passing test in its named gate | met — after correcting one row |
| full root command matrix passes, both runtime modes and all conformance gates | met — with stated case counts |
| compute inert; no compute row, evaluator, reconciler, or actuator added | met — zero rows |
| README documents responsibilities and both seams; admission rules recorded | met — verified by script, not by eye |
| before/after measurements same method; structural change explained by ownership | met — with the method limit stated |
| every omitted or substituted proof visible | met — §5 lists all three |

No proof required by the roadmap is currently omitted or substituted: Phase 3's two unreachable
runtime proofs (`post-mutation-evidence`, `prose-authority`) were each run individually in Phase 5
and passed. The initiative is therefore `complete`.

The stated outcome holds: `reconcile/executor.py`, `drift/evaluation.py`, and `sources/desired.py`
are no longer 1,200-line modules mixing orchestration with domain rules, and a reader can open
`nctl/README.md` and find the owner of any contract, target set, route, identity, or lifecycle
decision.

## 7. Handoff to `vm_first_realization`

- **A compute evaluator registers** at `nctl_core/drift/registry.py` via
  `register("compute_instance")`, documented in `nctl/README.md` "Adding a comparator". It receives
  the explicitly supplied snapshot; it must import only read models and pure drift helpers, and it
  belongs beside `drift/node_evaluation.py` and `drift/endpoint_evaluation.py` as a new
  per-resource evaluator — not inside them.
- **A compute reconciler registers** at `reconcile/registry.py` (identity, `phase`, DAG
  dependencies) plus `reconcile/reconcilers.py`, documented in `nctl/README.md` "Adding a
  reconciler".
- **An actuator implements the handler interface** in `reconcile/actions/`: `ActionContext` in,
  `ExecutedAction` out, registered in the `_HANDLERS` table in `reconcile/actions/dispatch.py`
  with its `phase` and `needs_client`. `planner.build_plan` owns the target set; a handler never
  widens it.
- **nintent owns the compute contract.** nctl replays nintent's generated
  `tests/fixtures/compute_conformance.json`; changing either side means regenerating the fixture and
  running `devtests/test_strategy/test_compute_conformance.py`. nctl never imports nintent at
  runtime, and any nintent change needs a user-owned push plus a `--no-cache` image rebuild with the
  resolved commit verified in the build log.
- **Safety contracts inherited unchanged:** the exact target set through planning, scan, inventory
  validation, Ansible `--limit`, action result, and post-actuation observation; SSH preflight
  fail-closed distinctions between missing, corrupt, unenrolled, unreachable, and mismatched;
  plan/apply separation and its approval boundary; evidence retention including `mutated=true` after
  a successful side effect with a later failure; desired-MAC fail-closed behavior and its
  deterministic recovery; and the non-executable prose boundary.
- **Compute inertness is manifested** (`compute-inert`, `nctl/tests/test_compute_actuation_inert.py`)
  and holds until `vm_first_realization` supersedes it. That row is the one to update first, and
  updating it is a deliberate, reportable act — not a side effect of adding a compute row.
