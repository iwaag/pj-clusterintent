# nctl Modularization Phase 3 Implementation Plan: Give Reconcile Orchestration an Action-Execution Seam

Parent: [roadmap.md](../roadmap.md) — Phase 3. Predecessor: [p2/report.md](../p2/report.md).

Status: proposed; nctl source restructuring plus one required nintent **test-only** repoint that needs
explicit user approval before it is made.

## 1. Goal

Phase 3 makes `reconcile/executor.py` sequence rounds, record evidence, and decide terminal state
without knowing how any individual action is performed. Every current action kind moves behind one
registered handler interface; the executor stops importing `observation`, `ledger`, `dnsmasq_apply`,
and `ansible` to perform work; and the reconcile envelope contract stops living inside the module
that orchestrates it.

This is the roadmap's highest-risk phase. It touches the exact-target-set contract, the SSH preflight
boundary, partial-progress evidence, the largest test module in the repository (2,355 lines, 75
monkeypatch sites), and one runtime-gate test that lives in another repository.

The phase must answer, and prove:

1. What exactly does a handler receive, what does it return, and where is the shared translation of
   `LedgerActionError` / `NautobotJobError` / `NautobotError` into an `ActionResult` — once, or five
   times?
2. Which decisions stay executor-owned because they sequence the *operation* rather than perform an
   *action*: production regeneration, the bootstrap/service phase boundary, the shared
   `NautobotClient` lifetime, plan construction, forced observation, scope summary, terminal
   persistence?
3. Does the exact planned host set still flow unbroken through planning, SSH scan, inventory
   validation, Ansible `--limit`, `ActionResult`, and post-actuation observation — proven by the same
   tests at the same layer, not by a narrower substitute?
4. Does every evidence rule survive verbatim: `mutated=true` after a successful side effect with a
   later failure, retained action and preflight records, final-drift refresh or a truthful
   `final_drift_unknown`, no rewritten history?
5. Which of the 75 monkeypatch sites in `test_reconcile_executor.py` patched a name that has moved,
   and does every repointed patch still intercept the same call site — with no `raising=False` and no
   re-export keeping a stale target alive?
6. Are the two real multi-round transitions still single tests traversing the real drift engine,
   planner, and executor?

The observable result is:

```text
current
  reconcile/executor.py (1,261 lines) mixing the reconcile envelope contract, plan/apply entry, the
    round loop, production inventory regeneration, per-reconciler dispatch, ledger/Job/playbook/
    dnsmasq/observation execution, playbook host grouping, SSH scan-error policy, plan construction,
    forced-observation rewrite, scope summary, terminal persistence, and text rendering
  + 25 intra-core imports, of which 5 exist only to perform an action
  + one SSH scan-error policy written twice, in executor.py and dnsmasq_apply.py
  + two compatibility aliases in dnsmasq_apply.py kept alive only by two tests
  + a nintent runtime test reaching into nctl's private `_execute_action`

to
  reconcile/results.py owning the `nctl.reconcile.v2` envelope contract
  + reconcile/actions/ owning one handler per action kind behind one dispatch entry point, with one
    error translation and one action-boundary evidence emitter
  + reconcile/executor.py reduced to lock, entry, round sequencing, production regeneration,
    preflight phase boundary, evidence retention, terminal state, and final-drift refresh
  + one SSH scan-error owner in reconcile/ssh_preflight.py
  + zero compatibility aliases
  + a nintent runtime test calling the public seam
  + identical envelopes, identical events, identical artifacts, identical target sets, identical
    manifest coverage
```

Phase 3 does not touch `drift/evaluation.py`, `production/composer.py`, `production/contract.py`,
the dnsmasq render/query family beyond the two findings in Section 4.3, or the `compute` package.
Those are roadmap Phase 4. It does not write the README responsibility map or the "Adding a
reconciler" section — that is Phase 5.

## 2. Required outputs

Phase 3 produces:

1. this implementation plan;
2. one private evidence directory under `.local/nctl-modularization/p3/<UTC timestamp>/`;
3. a frozen symbol-level disposition table for every symbol leaving `reconcile/executor.py`, with its
   destination module, layer, reason to change, consumers, and owning step;
4. a monkeypatch/private-symbol impact table: every one of the 75 `monkeypatch.setattr` sites and
   every direct private-symbol call in `nctl/tests/`, `nintent/`, and `devtests/`, with its current
   target, its post-move target, and the call site it must still intercept;
5. the handler table specification: reconciler id, module, phase, client need, and the exact test
   that owns each handler's contract;
6. corrections to [`roadmap.md`](../roadmap.md) and the Phase 0 evidence where this phase disproves a
   recorded fact, committed in the step that finds the contradiction;
7. `nctl_core/reconcile/results.py` and the reduced executor;
8. the `nctl_core/reconcile/actions/` package with one handler per current action kind and one
   dispatch entry point;
9. one SSH scan-error owner, with `dnsmasq_apply.py`'s duplicate deleted;
10. the deletion of `dnsmasq_apply.py`'s two compatibility aliases, with their tests re-owned by
    `nctl_core.ansible`;
11. behavior-preservation evidence: byte-identical reconcile plan-mode envelope and artifacts against
    the Step 0 baseline, identical event vocabulary and per-event fields at the action boundary,
    identical deterministic artifacts, identical envelope error codes, compute still inert;
12. before/after measurements using the Phase 0 method: files, lines, fan-in/fan-out, collected
    cases, runtime, slowest tests, skips, and the executor's import count;
13. one `report<N>.md` per step under `devdocs/big/nctl_modularization/p3/`; and
14. `devdocs/big/nctl_modularization/p3/report.md` with a final state of `complete`,
    `partially complete`, or `blocked`.

Tracked files Phase 3 may change:

- `devdocs/big/nctl_modularization/p3/plan.md`, `report<N>.md`, `report.md`;
- `devdocs/big/nctl_modularization/roadmap.md` and `devdocs/big/nctl_modularization/p0/*.md`, only to
  correct a fact this phase disproves;
- under `nctl/src/nctl_core/`: `reconcile/executor.py`, the new `reconcile/results.py`, the new
  `reconcile/actions/` package, `reconcile/ssh_preflight.py`, `reconcile/ledger.py`,
  `reconcile/reconcilers.py` (docstring only), `dnsmasq_apply.py`, `cli/main.py` (imports only), and
  the import lines of any module that referenced a moved symbol;
- optionally `nctl_core/reconcile_render.py` (Step 7, only if Section 5.8's independent-reason test
  passes);
- under `nctl/tests/`: the test modules that follow the moved ownership, plus the new handler and
  ssh-preflight test modules;
- `nctl/README.md`, only where a named path becomes wrong;
- `devtests/test_strategy/MANIFEST.md`, for the rows whose owning test module changes and for the
  `forced-observation-refresh` precise-ID correction Phase 0 already recorded as owed;
- `nintent/nautobot_intent_catalog/tests/test_desired_node_link_http.py`, **only** the two
  `_execute_action` call sites and their import line, and **only after** the Section 3.4 approval; and
- `README_DEV.md`, only if a gate's command or prerequisite changes.

Nothing else. In particular: no nintent application, model, migration, or Job change; no nauto,
nodeutils, or ansible_agdev change; no image rebuild; no change to
`nctl/tests/fixtures/compute_conformance.json`; no drift, production composition, dnsmasq render, or
compute logic change; no new runtime dependency.

## 3. Authority and safety boundary

### 3.1 Allowed actions

Phase 3 may:

- read and edit the tracked files listed in Section 2;
- run every ordinary offline suite and every gate in the root command matrix, including the Nautobot
  runtime gate in both `--keepdb` and `--clean` modes against the local scratch stack, OpenSSH
  conformance, Ansible conformance, and privileged-helper integration;
- run read-only `nctl` commands against the local Nautobot — `status`, `drift`, `drift --json`,
  `render dnsmasq`, `render hosts-intent`, `render production` into a phase-owned temporary
  directory, `ops list`, `ops show`;
- run `nctl reconcile` and `nctl reconcile <host>` in **plan mode only** (never `--yes`) against the
  local Nautobot, into a phase-owned event/artifact directory, as the Section 5.9 end-to-end
  preservation baseline. Plan mode fetches drift, builds a plan, reads the local managed SSH store,
  and writes only its own operation artifacts; it starts no scan, no Job, no Ansible process, and no
  Nautobot write;
- restart the local scratch Nautobot web, worker, and scheduler containers if the runtime gate needs
  a healthy stack;
- commit in `nctl`, in `nintent` (only the approved test repoint), and in the superproject; and
- remove only the exact disposable resources this phase created.

### 3.2 Prohibited actions

Phase 3 must not:

- push any submodule or move a submodule pointer without the user doing it;
- change nintent application code, models, migrations, Jobs, or GraphQL schema; rebuild the Nautobot
  image; or bump `NINTENT_COMMIT` / `NAUTO_COMMIT`;
- change any envelope field, envelope error code, event name, event field, artifact path, artifact
  field, plan schema field, drift code, exit code, CLI flag, or command name;
- change an `ActionResult`'s `action_id`, `reconciler_id`, `action_kind`, `target_slugs`, `success`,
  `detail`, `error`, or `mutated` value for any input that produces it today;
- change the `nctl.reconcile.v2` or `nctl.reconcile.plan.v1` schema strings or model field sets;
- add a compatibility alias, re-export shim, dual reader, deprecated import path, or
  `monkeypatch.setattr(..., raising=False)` to keep a moved symbol or a stale patch target working
  (`README_DEV.md`, breaking-change phase);
- introduce a plugin discovery mechanism, provider abstraction, generic event bus, DI container,
  registry of registries, or any abstract base class / Protocol with fewer than two current
  implementations;
- add a second reconciler registry, or move identity, DAG validation, or topological ordering out of
  `reconcile/registry.py`;
- add a handler for `new_node_baseline`, a compute comparator, a compute planner action, a compute
  reconciler, or a compute actuator, seed a desired or actual compute row, or otherwise make compute
  non-inert;
- decompose either real multi-round transition test into per-stage unit tests;
- weaken strict SSH verification, exact target scoping, Ansible override rejection, plan/apply
  separation, desired-MAC fail-closed behavior, or the non-executable prose boundary;
- write into `ansible_agdev/inventories/generated/`, `nctl.toml`, or any tracked artifact path; or

### 3.3 Stop conditions

Stop the affected step, preserve evidence, and ask rather than widening authority when:

- preserving an `ActionResult` field, an event field, an envelope error code, or an artifact path and
  completing a move turn out to be mutually exclusive;
- a repointed monkeypatch cannot intercept the same call site it intercepted before, so the test's
  meaning would change (Section 4.3 finding 11);
- the bootstrap/service partition, the shared-client lifetime, or the SSH preflight ordering cannot be
  reproduced exactly by handler metadata;
- a boundary listed in Section 5.10 as "must be re-proven" has no test that exercises it at its
  normative layer, so the proof would have to be substituted with a narrower one;
- either real multi-round transition test requires a structural change beyond repointing a patch
  target to keep passing;
- a deterministic artifact's bytes or digest differ from the Phase 2 baseline for any reason other
  than a declared generated-at / generation-ID / observation-timestamp field;
- the Nautobot runtime gate fails in a way not explained by the Phase 3 diff;
- the nintent repoint in Section 3.4 turns out to require more than the two call sites and one import
  line; or
- any revision in the six repositories moves mid-phase (Section 4.4).

A green suite after a move is never by itself the proof that a boundary held; Section 5.10 names the
specific test for each boundary.

### 3.4 Approval gate

Phase 3 has **one approval gate**, and it must be requested before Step 3 lands.

`nintent/nautobot_intent_catalog/tests/test_desired_node_link_http.py` imports and calls nctl's
private `_execute_action` at two sites (lines 32, 330, and 309's owning test). Both are inside the
Nautobot runtime gate, and one of them
(`test_run_reconcile_retains_real_http_mutation_and_refreshes_final_drift`) is the manifested owner
of `post-mutation-evidence`. When `_execute_action` is replaced by the public seam, that file must be
repointed or the runtime gate fails.

This is the same class of change the user explicitly authorized in Phase 2. It is nonetheless a
cross-repository edit, so:

- the phase must **ask before making it**, stating the two call sites, the new call form, and the
  fact that it is test-only;
- no compatibility re-export may be added to avoid asking;
- the change requires **no image rebuild and no push to pass the gate** — the runtime gate runs
  nintent's tests from the local checkout, and no nintent application code changes; and
- the resulting nintent commit is user-owned for pushing, as always.

If the user declines, Phase 3 stops at `partially complete` with the seam unbuilt rather than
retaining `_execute_action` as a shim; the report states that explicitly.

Everything else in Phase 3 is local, reversible, and inside the scratch classification. The runtime
gate's `--clean` mode recreates and destroys only the named `test_nautobot` database, which
`.local/localenv_memo.md` and `README_DEV.md` classify as reusable scratch state.

If a stop condition fires, report it and ask; do not convert it into an approval request for a
broader authority.

## 4. Governing inputs and planning-time findings

### 4.1 Required reading before Step 0

- root [`README.md`](../../../../README.md) and [`README_DEV.md`](../../../../README_DEV.md),
  especially the command matrix, lesson 6 (fail closed but truthfully), and lesson 9 (completion
  language);
- [`.local/localenv_memo.md`](../../../../.local/localenv_memo.md) — scratch classification and the
  nintent update flow this phase must *not* trigger;
- [`roadmap.md`](../roadmap.md), governing decisions 1, 3, 4, and 5 in full, plus the module
  admission rules and the Phase 3 exit criteria;
- [`p0/report.md`](../p0/report.md) with `report3.md` (import graph), `report4.md` (responsibility
  map), `report7.md` (action seam), and `report8.md` (error taxonomy);
- [`p2/report.md`](../p2/report.md) and `p2/report10.md` — what Phase 3 inherits;
- the private Phase 0 evidence under `.local/nctl-modularization/p0/20260727T141512Z/`:
  `action-interface.md` (the frozen seam design), `module-responsibilities.tsv`, `import-edges.tsv`,
  `layer-violations.tsv`, `error-taxonomy.tsv`, `move-impact.tsv`, `manifest-impact.tsv`,
  `structure-asserting-tests.tsv`, `artifact-baseline.tsv`, and `collect_step3.py`;
- the private Phase 2 evidence under `.local/nctl-modularization/p2/20260728T120000Z/`:
  `import-edges.tsv`, `layer-violations.tsv`, `module-coupling.tsv`, `package-totals.tsv`,
  `envelope-codes-before.tsv`, `error-disposition.tsv`, and `artifact-compare.tsv`;
- [`devtests/test_strategy/MANIFEST.md`](../../../../devtests/test_strategy/MANIFEST.md), rows
  `reconcile-host-scope`, `reconcile-dry-plan`, `post-mutation-evidence`, `partial-ipam-progress`,
  `dnsmasq-convergence`, `non-dhcp-ipam-convergence`, `forced-observation-refresh`,
  `desired-node-link`, `desired-mac-safe-stop`, `ssh-trust-identity`, `ansible-scope-and-policy`; and
- [`nctl/docs/compatibility.md`](../../../../nctl/docs/compatibility.md) — internal module layout is
  explicitly outside the current-consumer policy; durable artifacts, JSONL events, and CLI envelopes
  are inside it.

### 4.2 Frozen inputs from earlier phases

These are decided and must not be re-litigated:

- **The seam is a static registered handler interface with executor-owned rounds and evidence**
  (Phase 0 decision, `action-interface.md`). Not plugin discovery, not a provider abstraction, not a
  registry of registries, not a DI container.
- **`reconcile/registry.py` remains the sole owner of reconciler identity, DAG validation, and
  deterministic topological ordering.** Handler registration is an explicit static mapping keyed by
  registered reconciler id.
- **`planner.build_plan` is the single owner of exact action target sets.** A handler derives only
  `action.parameters["host_slugs"]` / `action.targets`; it never widens or re-derives a target set.
- **Executor-minted production regeneration (`reconciler_id="production_inventory"`,
  `action_kind="render"`) stays executor-owned** evidence and sequencing. It is not a reconciler and
  gets no handler.
- **The executor retains** lock, dry/apply entry, round sequencing, production regeneration, the
  preflight phase boundary, the operation log, terminal state, and the final-drift refresh.
- **Error codes, not Python types, are the consumer contract** (Phase 2). Any error type this phase
  touches keeps its code and message verbatim.
- **Compute stays inert** for the whole roadmap.

### 4.3 Planning-time findings

Each finding below was derived at planning time from the frozen tuple in Section 4.4. Step 1 must
re-verify every one against the checkout and record the result; a refuted finding is recorded as
refuted and the plan's proposal for it is withdrawn in that step's report.

1. **The executor dispatches on `reconciler_id`, not on `action_kind`.** `_execute_action`
   (`executor.py:756-813`) branches on `action.reconciler_id` through five cases plus an
   unknown-reconciler raise. Exactly one `action_kind` branch exists in the module:
   `_run_playbook_action` tests `action.action_kind == "dnsmasq_config"` (`executor.py:888`). The
   roadmap's Phase 3 wording ("`_execute_action` branches on `action.action_kind`") and the
   current-state table are imprecise. Both branch families must go; the roadmap sentence is amended
   in the step that confirms this, and the exit criterion is read as "no per-action-kind and no
   per-reconciler-id branch in the executor".
2. **`new_node_baseline` is registered but unreachable.** It appears in `reconcile/reconcilers.py:61`
   and `tests/test_reconcile_registry.py:43` only. `classify.py` maps no diff code to it, no
   `plan_*` function builds it, and `_execute_action` has no branch for it — an action carrying that
   id today would fall through to
   `LedgerActionError("unknown_reconciler", "no executor for reconciler …")`. Phase 0's
   `action-interface.md` lists it among the seam's implementers; that is wrong for the current
   checkout. **Proposal:** register **no** handler for it (governing decision 4 forbids an
   implementation with no consumer), preserve the identical unknown-reconciler failure path, and
   record the divergence from `action-interface.md` as a Phase 0 correction. Deleting the
   registration is out of scope — it is identity metadata that `vm_first_realization` may claim.
3. **The SSH scan-error policy is implemented twice, identically.** `executor.py::_ssh_scan_errors`
   (lines 167-194) and `dnsmasq_apply.py::_ssh_preflight_errors` (lines 432-454) produce the same
   three codes in the same order (`ssh_host_key_unenrolled`, `ssh_host_key_mismatch`,
   `ssh_host_key_unreachable`), the same `f"{code}: {slugs}"` message, and the same
   `{"hosts": [entry.model_dump() …]}` detail, over the same sorted slug ordering. `dnsmasq_apply.py`
   holds the ordering in `_PREFLIGHT_STATUS_CODES`; the executor inlines the identical tuple.
   **Proposal:** one public owner, `reconcile/ssh_preflight.py::ssh_scan_errors`, consumed by both.
   Both call sites' envelope errors must be byte-identical afterwards.
4. **`dnsmasq_apply.py` carries two live compatibility aliases.**
   `_inventory_group_hosts = inventory_group_hosts` and `_parse_recap = parse_recap`
   (`dnsmasq_apply.py:456-458`) are explicitly labelled "compatibility aliases for callers/tests that
   used the pre-Step-1 private names". Their only consumers are
   `tests/test_dnsmasq_apply.py:1022` and `:1030`; the real owner is `nctl_core.ansible`
   (`ansible.py:113`, `ansible.py:144`), already partly covered by `tests/test_ansible.py:64`.
   **Proposal:** delete both aliases and re-own the two tests to `tests/test_ansible.py` against the
   public names. This is the roadmap's "pass-through wrappers with one caller and no boundary
   meaning" deletion, and `README_DEV.md`'s breaking-change rule forbids keeping them.
5. **The bootstrap/service partition and the shared-client lifetime are one decision, expressed as a
   frozenset.** `_BOOTSTRAP_LEDGER_RECONCILERS = {"observe_node", "link_actual_node",
   "reconcile_ipam"}` (`executor.py:73`) both selects the bootstrap phase and, implicitly, decides
   which actions receive the shared `NautobotClient` (bootstrap actions get it; service actions get
   `client=None` and the ledger branches `assert client is not None`). Under the seam this becomes
   two explicit fields of handler metadata, `phase` and `needs_client`. An action whose
   `reconciler_id` has **no** handler must continue to partition into the **service** phase, so it
   still fails with the identical unknown-reconciler error at the same point in the round.
6. **Post-actuation observation is executor-minted, not planned.** `_execute_round` calls
   `_run_observation_action(..., action_id="post_actuation_observation")` directly with a target set
   derived from `plan.actions` (`executor.py:633-650`). `action-interface.md` does not address it.
   **Proposal:** the executor mints an in-memory `ReconcileAction`
   (`id="post_actuation_observation"`, `reconciler_id="observe_node"`,
   `action_kind="observation"`, targets from the same sorted slug set) and dispatches it through the
   same seam, so the executor keeps exactly one execution path. The minted action must never enter
   `plan.actions`, `plan.json`, or any `plan_created` event, and the produced `ActionResult` fields
   must be identical to today's.
7. **Forced observation is plan construction, not execution.** `_with_forced_observation`
   (`executor.py:1086-1126`) rewrites or prepends a planned action *before* `plan.json` is written.
   It stays with plan construction in the executor and does not move behind the seam.
8. **Plan construction must not be separated from production regeneration in this phase.**
   `load_deployment_profiles` is called by both `_build_plan_or_error` (`executor.py:1064`) and
   `_regenerate_production_inventory` (`executor.py:669`). Because they share one module today, a
   single `monkeypatch.setattr(executor_module, "load_deployment_profiles", …)` intercepts both call
   sites — and 8 tests rely on that. Splitting plan construction into its own module would silently
   halve what those patches cover. **Proposal:** keep `_build_plan_or_error` and
   `_with_forced_observation` in the executor, record the reason (they are this operation's plan
   construction, called only by the two entry points, and separating them buys no ownership while
   changing what 8 existing tests actually exercise), and record it as a deliberate keep under
   roadmap decision 1.
9. **`_scope_summary` is a keep unless a second consumer appears.** It reports drift targets in scope
   for the terminal envelope; its only caller is the executor, twice. Absence of a finding is a
   finding: Step 1 records the keep with its reason rather than moving it for size.
10. **The reconcile envelope contract must move for dependency reasons, not size reasons.**
    `ActionResult`, `RoundSummary`, `ReconcileData`, `ExecutedAction`, and `RECONCILE_SCHEMA` are
    defined in `executor.py`. Handlers must construct `ActionResult`/`ExecutedAction`, and the
    executor must import the handlers; if the contract stays in the executor the dependency is
    circular. `tests/test_current_consumer_contracts.py:22` imports `ReconcileData` from the
    executor and must be repointed. This is a forced, dependency-driven move with an independent
    reason to change (`nctl.reconcile.v2` is an independently versioned public contract read by
    `nctl ops show` and `cli/main.py`, while orchestration changes when sequencing changes).
11. **75 monkeypatch sites patch names on the executor module object.**
    `tests/test_reconcile_executor.py` binds `executor_module` and patches, among others,
    `run_observation` (9 sites), `execute_link_actual_node` (9), `load_deployment_profiles` (8),
    `load_profile_reconciliation` (6), `write_production_artifacts` (11), `execute_reconcile_ipam`
    (4), `AnsibleRunner` (4), `fetch_and_compute_drift` (2), `_InterruptFlag` (2), `_execute_round`
    (2), `build_dnsmasq_apply`, `build_production_render_context`, `build_source_snapshot`,
    `resolve_operational_values`, `default_ssh_probe_runner`, and `_regenerate_production_inventory`.
    Every symbol that moves behind the seam invalidates its patch target. `monkeypatch.setattr`
    without `raising=False` raises `AttributeError` for a missing attribute, so a stale target fails
    loudly rather than silently disabling an assertion — Phase 3 must therefore never add
    `raising=False`, and must never re-export a moved symbol into the executor namespace to keep a
    patch alive. Each repointed patch must be checked to still intercept the same call site.
12. **Three executor privates are called directly by tests, and two by nintent.**
    `tests/test_reconcile_executor.py` calls `_group_hosts_by_playbook` (line 235), `_ssh_scan_errors`
    (1448), and `_execute_round` (1565).
    `nintent/nautobot_intent_catalog/tests/test_desired_node_link_http.py` imports `_execute_action`
    (line 32) and calls it positionally at line 330, inside
    `test_real_http_post_patch_failure_is_retained_by_executor_evidence`; the same file's
    `test_run_reconcile_retains_real_http_mutation_and_refreshes_final_drift` is the manifested owner
    of `post-mutation-evidence`. The nintent repoint is Section 3.4's approval gate.

### 4.4 Frozen tuple, collision, and sequencing rule

Planning-time tuple, all six worktrees clean: superproject
`b4fc107241985bf49257bfdb18dbb594685afb60`, nctl `a07db7f35e83ed53e8105edf5b4a133fd398692b`, nintent
`3fbe896f9378006b8aeac22063488ba76ce9b5b4`, nauto `6dab422a725a2e2e4e24e98079e992d1111c0ef1`,
nodeutils `775ed7fad5110a96186a737147b87d3bf450ced2`, ansible_agdev
`66b31c89986d1b2ecfa187a72209d8bd96838fd4`. The installed Nautobot image carries nintent
`2130bd850ffc1c5ef277c6fa9cc787194ecafd21`, which is behind the local nintent HEAD; Phase 3 changes
no nintent application code, so this divergence is recorded as inherited state and is a stop
condition only if the runtime gate fails in a way it explains.

`vm_first_realization` is not written and must not start. VM Phase 3 Steps 9–12 must not seed compute
while Phase 3 runs — a seeded compute row would change the plan-mode baseline and the inertness
proof. Recapture the tuple at the start and end of the phase and around the runtime gate. If a
component revision moves: finish or terminate the current command safely, mark the affected capture
stale, and recollect it against one new frozen tuple.

## 5. The Phase 3 design made concrete

### 5.1 Target module map

| Module | State | Layer | Owns | May import | Must not import |
|---|---|---|---|---|---|
| `reconcile/results.py` | new | contract | `RECONCILE_SCHEMA`, `ActionResult`, `RoundSummary`, `ReconcileData` | pydantic, `reconcile.model` | anything that executes, renders, or transports |
| `reconcile/actions/contract.py` | new | contract + evidence | `ActionContext`, `ExecutedAction`, `ActionHandler`, and the shared action-boundary result/event constructors (`actuation_result`, `failed_action_result`) | `reconcile.model`, `reconcile.results`, `events`, `artifacts`, `config`, `output`, runtime handles | any handler module, the executor, CLI |
| `reconcile/actions/dispatch.py` | new | orchestration seam | the static `reconciler_id -> ActionHandler` table, `handler_for`, `execute_action`, the single `action_started` emit, and the single `LedgerActionError`/`NautobotJobError`/`NautobotError` translation including the unknown-reconciler path | `reconcile.actions.*`, `reconcile.registry` | the executor |
| `reconcile/actions/observe.py` | new | action handler | the `observe_node` action, including its `SshStoreReadError`-versus-`ValueError` distinction | `observation`, `actions.contract` | the executor, other handlers |
| `reconcile/actions/ledger_link.py` | new | action handler | the `link_actual_node` action | `reconcile.ledger`, `actions.contract` | the executor, other handlers |
| `reconcile/actions/ipam.py` | new | action handler | the `reconcile_ipam` action, its Job runner construction, its applied/unresolved success rule, and its `mutated` rule | `reconcile.ledger`, `jobs`, `actions.contract` | the executor, other handlers |
| `reconcile/actions/playbook.py` | new | action handler | the `service_profile` action and playbook host grouping by derived OS | `ansible`, `production.adapter`, `production.derivation`, `actions.contract` | the executor, other handlers |
| `reconcile/actions/dnsmasq.py` | new | action handler | the `dnsmasq_config` action | `dnsmasq_apply`, `actions.contract` | the executor, other handlers |
| `reconcile/executor.py` | reduced | orchestration | lock, plan/apply entry, round sequencing, production regeneration, preflight phase boundary, plan construction, forced observation, scope summary, evidence retention, terminal state and persistence, final-drift refresh, `RoundOutcome`, `_InterruptFlag` | `reconcile.actions.dispatch`, `reconcile.*`, drift/production/source modules | any handler module directly, `observation`, `reconcile.ledger`, `dnsmasq_apply`, `ansible`, `jobs` |
| `reconcile/ssh_preflight.py` | extended | orchestration | the existing trust checks and target scans **plus** the single `ssh_scan_errors` policy | `output`, `ssh_*`, `config` | any handler module |
| `dnsmasq_apply.py` | reduced | orchestration | unchanged apply behavior, minus the duplicated scan-error policy and the two compatibility aliases | `reconcile.ssh_preflight`, `ansible` | — |
| `reconcile_render.py` | new (Step 7, conditional) | presentation | `render_reconcile_text` | `reconcile.results`, `output` | anything that executes |
| `reconcile/registry.py` | unchanged | orchestration | identity, DAG validation, topological order | `reconcile.model` | — |
| `reconcile/reconcilers.py` | docstring only | orchestration | reconciler identity metadata and per-target planning | unchanged | — |

Every new module must satisfy the roadmap's module admission rules; Step 1 records the check per
module, including its consumers and its independent reason to change.

### 5.2 The seam, made concrete

```python
# reconcile/actions/contract.py

@dataclass(frozen=True)
class ActionContext:
    cfg: Config
    operation_log: OperationLog
    artifacts: OperationArtifacts
    round_index: int
    snapshot: SourceSnapshot
    client: NautobotClient | None
    now: Callable[[], datetime]
    command_runner: CommandRunner | None
    ssh_probe: SshProbeRunner
    generated_at: str


class ExecutedAction(BaseModel):
    result: ActionResult
    terminal_errors: list[EnvelopeError] = Field(default_factory=list)


@dataclass(frozen=True)
class ActionHandler:
    reconciler_id: str
    execute: Callable[[ActionContext, ReconcileAction], ExecutedAction]
    phase: Literal["bootstrap", "service"]
    needs_client: bool
```

```python
# reconcile/actions/dispatch.py

def execute_action(context: ActionContext, action: ReconcileAction) -> ExecutedAction: ...
def handler_for(reconciler_id: str) -> ActionHandler | None: ...
def action_phase(reconciler_id: str) -> Literal["bootstrap", "service"]: ...
```

Two deliberate refinements of Phase 0's `action-interface.md`, both recorded in Step 1:

- **`ActionContext` is a frozen dataclass, not a `Protocol`.** There is exactly one context
  implementation and there is no second one planned; a Protocol would be an interface with one
  implementer, which governing decision 4 forbids. The field set is Phase 0's, unchanged.
- **The error translation stays at the seam boundary, not inside each handler.** Phase 0's wording
  ("handlers do not allow `SshStoreReadError`, `NautobotJobError`, `LedgerActionError`, or
  Ansible/process exceptions to escape") is implemented as one `try/except` in
  `dispatch.execute_action`, reproducing today's `except (LedgerActionError, NautobotJobError,
  NautobotError)` block verbatim — same `code = getattr(exc, "code", "action_failed")`, same
  `mutated = bool(getattr(exc, "mutated", False))`, same `action_completed` event, same
  `error=f"{code}: {exc}"`. Copying that block into five handlers would recreate exactly the defect
  Phase 2 removed from Braindump. `SshStoreReadError` remains handled inside the observation handler,
  where it already is, because it sets `terminal_errors` rather than producing a failed result alone.

The `op.emit("action_started", …)` call stays in `execute_action`, before dispatch, exactly where
`_execute_action` emits it today.

### 5.3 The handler table

| reconciler id | handler module | phase | needs client | action kinds today |
|---|---|---|---|---|
| `observe_node` | `actions/observe.py` | bootstrap | no | `observation` |
| `link_actual_node` | `actions/ledger_link.py` | bootstrap | yes | `ledger_patch` |
| `reconcile_ipam` | `actions/ipam.py` | bootstrap | yes | `job` |
| `service_profile` | `actions/playbook.py` | service | no | `playbook` |
| `dnsmasq_config` | `actions/dnsmasq.py` | service | no | `dnsmasq_config` |
| `new_node_baseline` | none (finding 4.3.2) | service (default) | — | registered identity only |

`phase` reproduces `_BOOTSTRAP_LEDGER_RECONCILERS` exactly. `action_phase` returns `"service"` for any
id without a handler, preserving today's partition and today's unknown-reconciler failure point.
`needs_client` documents the existing `assert client is not None`; the executor keeps deciding the
client's lifetime (one client opened for the bootstrap phase, closed in a `finally`, `None` for the
service phase) because that is round sequencing, not action work.

The `dnsmasq_config` handler exists because the current `action_kind` branch inside
`_run_playbook_action` proves it is a different execution path, not because it has a different name:
it calls `build_dnsmasq_apply` with an exact `host_limit`, while `service_profile` runs
`ansible-playbook` with an exact `--limit`. Two current implementations, two reasons to change; the
interface is admissible.

### 5.4 What the executor keeps, and why

| Retained | Reason it is not an action |
|---|---|
| `run_reconcile`, `_run_plan_only`, `_run_apply` | operation entry, mode separation, lock scope |
| the round loop, fingerprint no-progress rule, max-rounds rule, blocker rules | round sequencing and terminal-state vocabulary |
| `_regenerate_production_inventory` | executor-minted evidence and generation sequencing (Phase 0 decision); it is not a registered reconciler |
| the round-start SSH gate and the post-regeneration service scan | the preflight phase boundary decides whether *any* action may run, before dispatch |
| `_build_plan_or_error`, `_with_forced_observation` | plan construction for this operation (findings 4.3.7, 4.3.8) |
| `_scope_summary` | terminal reporting of drift targets in scope (finding 4.3.9) |
| `_finish`, `_persist_terminal_result` | terminal state and durable result contract |
| `RoundOutcome`, `_InterruptFlag` | the round loop's own control types |

After Phase 3 the executor imports `reconcile.actions.dispatch` and no longer imports `observation`,
`reconcile.ledger`, `dnsmasq_apply`, `ansible`, `jobs`, `production.adapter`, or
`production.derivation` **for action execution**. `production.profiles` and `production_render` stay,
because production regeneration stays.

### 5.5 The exact target set, unchanged and re-proven

`planner.build_plan` remains the single owner. A handler reads only `action.targets` and
`action.parameters["host_slugs"]`; it never consults the snapshot to widen a set, never falls back to
a group membership, and never re-derives hosts from drift. The same set must flow through:

`build_plan` → `action_host_slugs` / `ssh_required_host_slugs` → the round-start scan → production
route validation → `verify_resolved_ssh_targets` → Ansible `--limit` or `build_dnsmasq_apply(host_limit=…)`
→ `ActionResult.target_slugs` → the post-actuation observation target set.

Named proofs, run and recorded by name in Step 8:

| Link | Test |
|---|---|
| host scope end to end, siblings excluded | `tests/test_dnsmasq_apply.py::test_host_scoped_reconcile_targets_scans_and_deploys_only_the_requested_host` (`reconcile-host-scope`) |
| scan uses the freshly regenerated route | `tests/test_reconcile_executor.py::test_service_phase_scans_freshly_regenerated_route_not_round_start_snapshot` |
| Ansible limit and blocked-render non-invocation | `tests/test_reconcile_executor.py::test_dnsmasq_config_action_with_blocked_render_never_invokes_ansible` |
| post-actuation observation set and evidence retention | `tests/test_reconcile_executor.py::test_post_actuation_observation_store_failure_retains_deployment_evidence` |
| SSH preflight before the first production playbook | `tests/test_reconcile_executor.py::test_service_phase_blocks_on_mismatched_key_after_production_regen` |
| playbook grouping uses the fixed operation timestamp | `tests/test_reconcile_executor.py::test_playbook_grouping_passes_the_fixed_operation_timestamp_to_resolver` (repointed to the playbook handler) |

### 5.6 Evidence semantics, unchanged

Every rule below is preserved textually, and each is named in the Step 8 report with its test:

- `ExecutedAction.result` is appended to `RoundSummary.actions` **before** `terminal_errors` is
  inspected, so a store failure inside observation never erases the action record;
- `had_side_effects` is `result.success or result.mutated`, and drives the final-drift refresh;
- a failed `reconcile_ipam` with at least one applied endpoint is `success=False, mutated=True`;
- a failed post-PATCH confirmation is `success=False, mutated=True` with `node_link_not_confirmed` in
  the error;
- `outcome.summary` is appended unconditionally, including for interruption, unavailable production
  regeneration, a post-regen scan failure, and a store-read failure;
- a failed final-drift refresh after side effects appends `final_drift_unknown` rather than reporting
  stale round-start drift as final; and
- `data.progress_made` counts action success or positive mutation, never mere summary presence.

### 5.7 The test split

`tests/test_reconcile_executor.py` (2,355 lines) splits along the same ownership boundary as the
source, and nothing else changes about it:

**Stays in `tests/test_reconcile_executor.py`** — plan mode, refresh-observation entry rules, terminal
`result.json` persistence, pre-assigned operation id, the round-start SSH gate, already-converged,
manual/global/local blockers, no-progress and max-rounds, lock contention, interruption, production
regeneration failure paths, post-regeneration scan, independent service-action failure, evidence
retention, final-drift refresh and `final_drift_unknown`, unknown host, and **both real multi-round
transitions** (`test_real_multi_round_dnsmasq_content_convergence`,
`test_real_multi_round_ipam_convergence_for_non_dhcp_endpoint`), which stay single tests traversing
the real drift engine, planner, and executor and are never decomposed.

**Moves to `tests/test_reconcile_actions.py`** — the cases whose subject is one handler's own
contract: playbook grouping and its timestamp propagation, the IPAM applied/unresolved/mutated
matrix, the ledger link action's own outcome mapping, the observation action's
`SshStoreReadError`-versus-`ValueError` distinction, and dispatch-level cases (unknown reconciler,
the shared error translation, the `action_started`/`action_completed` emissions).

**Moves to `tests/test_reconcile_ssh_preflight.py`** — `test_ssh_scan_errors_maps_unenrolled_status_too`
and any other direct test of the now-shared scan-error policy, plus a new case proving
`dnsmasq_apply` and the executor produce identical envelope errors from identical entries.

**`tests/test_dnsmasq_apply.py`** keeps its name and every apply case; only the two alias tests leave,
re-owned by `tests/test_ansible.py` against the public `inventory_group_hosts` / `parse_recap`.

Rules for the split: no assertion is deleted, weakened, merged, or converted to a narrower layer. A
test moves only if its subject moved. Every `monkeypatch.setattr` is repointed to the module that now
owns the patched name and re-verified to intercept the same call site; `raising=False` is never
introduced.

Manifest consequences, updated in the same commit as the move that causes them:

| Row | Today | After |
|---|---|---|
| `partial-ipam-progress` | `test_reconcile_executor.py::test_reconcile_ipam_partial_conflict_is_not_reported_as_success` | repointed if and only if that test moves to `test_reconcile_actions.py` |
| `forced-observation-refresh` | `test_reconcile_executor.py` (module only) | precise ID, closing the Phase 0 `manifest-impact.tsv` finding — proposed: `::test_refresh_observation_executes_once_then_converges` |
| `reconcile-dry-plan`, `dnsmasq-convergence`, `non-dhcp-ipam-convergence` | `test_reconcile_executor.py::…` | unchanged; these tests stay |
| `reconcile-host-scope` | `test_dnsmasq_apply.py::…` | unchanged |
| `post-mutation-evidence`, `desired-node-link` | nintent runtime tests | unchanged IDs; the file's `_execute_action` call sites are repointed |

### 5.8 Text rendering: extract only if it earns it

`render_reconcile_text` renders a completed envelope and decides nothing; its only consumer is
`cli/main.py`; every other domain in the repository already puts this in a `*_render.py` module
(`drift_render.py`, `production_render.py`, `dnsmasq_render.py`, `ops_render.py`,
`braindump_render.py`). Step 7 extracts it to `nctl_core/reconcile_render.py` **if** Step 1 confirms
that its reason to change (human text format) is independent of the round loop's and that no test
depends on it living in the executor. If Step 1 refutes either, it stays and the keep is recorded
with its reason. Absence of a finding is a finding.

### 5.9 The end-to-end preservation baseline

Beyond the suite, Phase 3 captures a real plan-mode envelope as its behavior reference, because the
seam changes the code path that produces it:

- Step 0 runs `nctl reconcile --json` and `nctl reconcile <host> --json` in plan mode against the
  local Nautobot, into a phase-owned event/artifact directory, and stores the envelope, the
  `plan.json`, the `result.json`, and the JSONL event stream;
- Step 8 repeats both runs and diffs them field by field, excluding only `operation_id`,
  `generated_at`, timestamps, and the paths that embed the operation id;
- the diff must be empty. A difference in `state`, `scope_summary`, `summary`, `manual_review`,
  `unsupported`, `ssh_preflight`, `plan.actions`, any event name, or any event field is a defect, not
  an update.

If the local Nautobot is unavailable, this baseline is recorded as unavailable and the phase cannot
claim it — a substituted proof is visible in the report and prevents an unqualified `complete`.

### 5.10 Behavior that must not change, and the named proof for each

| Behavior | Named proof |
|---|---|
| exact target set through planning, scan, inventory, `--limit`, action, observation | the six tests in Section 5.5, each re-run and named |
| SSH preflight fail-closed distinctions (missing, corrupt, unenrolled, unreachable, mismatched) | `tests/test_reconcile_executor.py::test_apply_blocks_on_unenrolled_ssh_host_before_any_action_executes`, `::test_apply_blocks_on_mismatched_offered_key_before_observation_runs`, `::test_apply_reports_ssh_store_read_failed_when_managed_store_is_corrupt`, plus the OpenSSH conformance gate (`ssh-trust-identity`) |
| dry plan has zero side effects | `::test_plan_mode_never_mutates_and_reports_planned` and `::test_dry_plan_reports_ssh_preflight_without_blocking` (`reconcile-dry-plan`) |
| partial IPAM progress | `::test_reconcile_ipam_partial_conflict_is_not_reported_as_success` (`partial-ipam-progress`) plus the fully-applied and no-endpoint cases |
| post-mutation evidence over real HTTP | `nintent/.../test_desired_node_link_http.py::DesiredNodeLinkRealHttpTests.test_run_reconcile_retains_real_http_mutation_and_refreshes_final_drift` (`post-mutation-evidence`) in the runtime gate, both modes |
| executor evidence retention over real HTTP | `nintent/.../test_desired_node_link_http.py::…::test_real_http_post_patch_failure_is_retained_by_executor_evidence` — the repointed call site |
| desired-node link over real GraphQL/PATCH | `desired-node-link`, runtime gate |
| both real multi-round transitions | `::test_real_multi_round_dnsmasq_content_convergence` (`dnsmasq-convergence`), `::test_real_multi_round_ipam_convergence_for_non_dhcp_endpoint` (`non-dhcp-ipam-convergence`) |
| forced observation | `::test_refresh_observation_executes_once_then_converges` (`forced-observation-refresh`) |
| interruption safety and mid-round retention | `::test_interrupted_before_round_reports_failed`, `::test_interruption_mid_round_retains_actions_completed_before_it` |
| Ansible scope and override rejection | the Ansible conformance gate (`ansible-scope-and-policy`) |
| desired-MAC fail-closed behavior | `tests/test_dnsmasq_render.py::test_desired_mac_mismatch_then_resolved_round_trip` (`desired-mac-safe-stop`) |
| compute inertness | `tests/test_compute_actuation_inert.py::test_valid_compute_collections_produce_no_drift_and_no_plan_actions` (`compute-inert`) |
| deterministic artifacts | `render dnsmasq`, `render hosts-intent`, `render production` bytes and digests compared with the Phase 0/2 baseline under the declared exclusions |
| operation evidence readability | `tests/test_operations_index.py::test_list_operations_over_real_phase4_layout` (`operation-evidence-reader`) |
| current-consumer envelope contract | `tests/test_current_consumer_contracts.py`, repointed import only |
| domain purity | `tests/test_module_boundaries.py` unchanged and still passing |

## 6. Evidence layout

Create `.local/nctl-modularization/p3/<UTC timestamp>/` with mode `0700`, files `0600`:

```text
README.txt
commands.jsonl
revisions-start.tsv
revisions-end.tsv
symbol-disposition.tsv
handler-table.tsv
patch-impact.tsv
private-symbol-consumers.tsv
duplication-findings.tsv
p0-corrections.md
roadmap-corrections.md
import-edges-before.tsv
import-edges-after.tsv
module-coupling-before.tsv
module-coupling-after.tsv
package-totals-before.tsv
package-totals-after.tsv
executor-imports-before.tsv
executor-imports-after.tsv
reconcile-plan-baseline/
reconcile-plan-after/
reconcile-plan-compare.tsv
artifact-compare.tsv
envelope-codes-before.tsv
envelope-codes-after.tsv
event-vocabulary-before.tsv
event-vocabulary-after.tsv
test-split.tsv
manifest-impact.tsv
gate-results.tsv
logs/
```

`commands.jsonl` records timestamp, working directory, sanitized argument vector, exit code, duration,
and output digest. No inherited environment values, tokens, headers, or payload bodies. The plan-mode
baseline directories hold envelopes, plans, results, and event streams from the local scratch stack
only; no key material, no authorization header, and no private prose enters any file.

## 7. Implementation procedure

Each step ends with its own `report<N>.md` and exactly one commit. Every step is local and reversible;
a failing gate stops the step rather than starting the next one.

### Step 0 — Freeze the tuple, reproduce the baselines

1. Re-read every governing input in Section 4.1.
2. Confirm all six repositories are clean; preserve any user change rather than cleaning it. Record
   HEAD, branch, upstream relation, submodule pointer, and porcelain status into
   `revisions-start.tsv`, plus the installed nintent image revision.
3. Confirm compute is still unseeded (zero desired compute platform and instance rows).
4. Reproduce the Phase 2 exit numbers: nctl ordinary (970 expected), compute conformance, and the
   fixture digest `ccff71d9…`. Any difference stops the step.
5. Re-run the Phase 0 measurement method with `collect_step3.py` into the `*-before.tsv` files, and
   record the executor's import list and count separately into `executor-imports-before.tsv`.
6. Capture the deterministic artifacts into a phase-owned temporary directory and confirm they still
   match the Phase 0 baseline under the declared exclusion rule.
7. Capture the envelope error codes reachable from `src/` into `envelope-codes-before.tsv`, and the
   full event-name and event-field vocabulary emitted by the reconcile path into
   `event-vocabulary-before.tsv`.
8. Capture the Section 5.9 plan-mode baseline (cluster scope and one host scope) into
   `reconcile-plan-baseline/`.

Gate: one clean frozen tuple, compute unseeded, all Phase 2 numbers reproduced, and every baseline
captured before any edit.

### Step 1 — Audit, verify the findings, and freeze the dispositions

No production or test code changes in this step except the corrections it commits to the roadmap and
the Phase 0 evidence.

1. Verify each Section 4.3 finding against the checkout. Record confirmed/refuted with the evidence
   into `p0-corrections.md` and `roadmap-corrections.md`, and amend the roadmap sentence that says the
   executor branches on `action_kind` (finding 1) and the `action-interface.md` implementer list
   (finding 2).
2. Write `symbol-disposition.tsv`: one row per symbol leaving `executor.py`, with `symbol`,
   `current_module`, `target_module`, `layer`, `reason_to_change`, `consumers`, `test_owner`, `step`.
   Include the explicit keeps from Section 5.4 with their reasons.
3. Write `handler-table.tsv` from Section 5.3, adding for each handler its independent reason to
   change, its consumers, and the admission check.
4. Write `patch-impact.tsv`: all 75 `monkeypatch.setattr` sites with current target, post-move target,
   the call site each must still intercept, and whether the patch's coverage changes. Any row where
   coverage would change is a Section 3.3 stop condition, not a silent acceptance.
5. Write `private-symbol-consumers.tsv`: every direct use of an executor private in `nctl/tests/`,
   `nintent/`, and `devtests/`, with its post-move form.
6. Write `duplication-findings.tsv` (findings 3 and 4, plus anything else the audit finds), each with
   its disposition and owning phase.
7. Run the roadmap's required searches restricted to this phase's surface — `action_kind`,
   `_execute_action`, `register_reconciler`, `registered_reconciler_ids`, `register(`,
   `from nctl_core`, `import nctl_core`, `subprocess`, `phase`, `legacy`, `fallback`, `shim`, `TODO`
   — across active source, tests, fixtures, configuration, and current documentation. Classify each
   match; a match is never deletion permission.
8. Write `test-split.tsv` and `manifest-impact.tsv`: every test that moves, its destination, and every
   manifest row affected, including the `forced-observation-refresh` precise-ID correction.
9. Request the Section 3.4 approval for the nintent repoint, stating the exact call sites and the new
   call form. Record the answer.

Gate: every symbol leaving the executor has a destination and a reason; every keep has a recorded
reason; every patch site has a verified post-move target; the roadmap and Phase 0 corrections are
committed; the nintent approval is recorded; no source or test behavior changed.

### Step 2 — Lift the reconcile result contract out of the executor

1. Create `reconcile/results.py` with `RECONCILE_SCHEMA`, `ActionResult`, `RoundSummary`, and
   `ReconcileData`, moved textually — no field, default, alias, or docstring semantics changed.
2. Repoint `executor.py` and `tests/test_current_consumer_contracts.py`. No re-export is added.
3. Confirm the `nctl.reconcile.v2` schema string, every field name, and every default is unchanged by
   diffing the model JSON schemas before and after.
4. Run: nctl ordinary.

Gate: the envelope contract has one owner; the model JSON schema diff is empty; no re-export exists.

### Step 3 — Introduce the seam and move the bootstrap handlers

1. Create `reconcile/actions/contract.py` (Section 5.2) with `ActionContext`, `ExecutedAction`,
   `ActionHandler`, and the shared `actuation_result` / `failed_action_result` constructors moved from
   the executor with their event emissions unchanged.
2. Create `reconcile/actions/dispatch.py` with the static table, `handler_for`, `action_phase`,
   `execute_action`, the single `action_started` emit, and the one error translation including the
   unknown-reconciler path with its identical message.
3. Move `observe_node`, `link_actual_node`, and `reconcile_ipam` into `actions/observe.py`,
   `actions/ledger_link.py`, and `actions/ipam.py`. The observation handler keeps the
   `SshStoreReadError`-versus-`ValueError` distinction and the `terminal_errors` contract exactly.
4. Rewrite `_execute_round`'s bootstrap loop to build one `ActionContext` and call
   `dispatch.execute_action`; partition actions with `dispatch.action_phase`.
5. Mint the post-actuation observation action per finding 4.3.6 and route it through the same seam.
   Assert in the step's report that `plan.json` and `plan_created` are unaffected.
6. Repoint the affected monkeypatch sites per `patch-impact.tsv`.
7. After the recorded approval, repoint nintent's two `_execute_action` call sites and its import line
   to `execute_action(ActionContext(...), action)`. Nothing else in that file changes.
8. Run: nctl ordinary; then the Nautobot runtime gate in `--keepdb` mode to prove the repointed
   nintent sites before continuing.

Gate: the three bootstrap handlers execute through the seam; the executor no longer imports
`observation` or `reconcile.ledger`; `nctl ordinary` and the runtime gate pass; no re-export or
`raising=False` was added.

### Step 4 — Move the service handlers

1. Move `service_profile` into `actions/playbook.py`, carrying `_group_hosts_by_playbook` and its
   `DerivationFailure`-to-`ValueError` invariant message unchanged.
2. Move `dnsmasq_config` into `actions/dnsmasq.py`, carrying the exact `host_limit` derivation from
   `action.parameters["host_slugs"]`.
3. Rewrite `_execute_round`'s service loop to use the seam. The post-regeneration scan, the
   `production_regeneration_unavailable` stop, and the ordering between them are untouched.
4. Repoint the affected monkeypatch sites and the direct `_group_hosts_by_playbook` call.
5. Run: nctl ordinary, naming `reconcile-host-scope`, `dnsmasq-convergence`, and
   `non-dhcp-ipam-convergence`.

Gate: the executor imports no feature module to perform an action; both multi-round transitions still
pass as single real-path tests.

### Step 5 — Remove the last branches, unify the scan-error policy, delete the aliases

1. Confirm by search that no `action_kind` branch and no `reconciler_id` branch for execution remains
   in `executor.py`, and record the search output.
2. Move the scan-error policy to `reconcile/ssh_preflight.py::ssh_scan_errors` and delete both
   duplicates; prove the resulting envelope errors are byte-identical from both call sites (finding 3).
3. Delete `dnsmasq_apply.py`'s two compatibility aliases and re-own their tests to
   `tests/test_ansible.py` against the public names (finding 4).
4. Update the `reconcile/reconcilers.py` docstring where it describes Step 7 executor behavior that
   has moved, and the `executor.py` module docstring, which currently describes `p4/plan.md`'s
   numbered steps rather than the current contract.
5. Run: nctl ordinary and the Ansible conformance gate.

Gate: zero execution branches in the executor; one scan-error owner; zero compatibility aliases; no
message text changed.

### Step 6 — Re-own the tests along the seam and update the manifest

1. Split `tests/test_reconcile_executor.py` per Section 5.7 into it, `tests/test_reconcile_actions.py`,
   and `tests/test_reconcile_ssh_preflight.py`. No assertion is deleted, weakened, merged, or moved to
   a narrower layer.
2. Add the case proving `dnsmasq_apply` and the executor produce identical scan-error envelopes.
3. Update every affected `MANIFEST.md` row in this commit, including the `forced-observation-refresh`
   precise ID, and re-run each row's named gate.
4. Verify no test patches a name it no longer owns: grep for `raising=False` (must be absent) and
   confirm every `monkeypatch.setattr` target resolves.
5. Run: nctl ordinary with `--durations=20`.

Gate: every manifest row resolves to an existing passing test; the collected-case count is explained
against Step 0's 970; no assertion was lost in the split.

### Step 7 — Text rendering

1. Apply Section 5.8: extract `render_reconcile_text` to `nctl_core/reconcile_render.py` and repoint
   `cli/main.py`, **or** record the keep with its reason if Step 1 refuted the independent-reason
   test.
2. Run: nctl ordinary and the CLI surface tests.

Gate: the decision is recorded either way; presentation renders a completed envelope and decides
nothing.

### Step 8 — Re-prove the boundaries and run the full matrix

1. Re-run the Section 5.9 plan-mode capture into `reconcile-plan-after/` and diff against the Step 0
   baseline under the declared exclusions. The diff must be empty.
2. Re-capture the deterministic artifacts, the envelope error codes, and the reconcile event
   vocabulary; all three diffs must be empty.
3. Run and name every proof in Sections 5.5, 5.6, and 5.10 individually, recording pass/fail per row
   into `gate-results.tsv` — not "the suite passed".
4. Run the complete local matrix: nctl ordinary, compute conformance, nintent Django-free, nauto
   ordinary, nodeutils ordinary, Ansible helper, OpenSSH conformance, Ansible conformance,
   privileged-helper integration.
5. Run the Nautobot runtime gate in both `--keepdb` and `--clean` modes. State the case counts against
   Phase 2's 299 and explain any difference. Name `post-mutation-evidence`, `desired-node-link`, and
   `prose-authority` explicitly.
6. Run read-only `nctl status`, `nctl drift --json`, and `nctl ops list` and confirm the envelopes are
   unchanged in shape.

Gate: every gate green or its failure recorded as pre-existing with the Phase 0/2 evidence that shows
it; both runtime modes pass; every named boundary proof is listed with its result.

### Step 9 — Manifest, documentation, and measurement

1. Verify every `MANIFEST.md` row resolves to an existing, passing test in its named gate.
2. Correct any now-wrong path in `nctl/README.md`. Do not write the responsibility map or the "Adding
   a reconciler" section — that is Phase 5.
3. Re-run the Phase 0 measurement method into the `*-after.tsv` files: package totals, files, lines,
   import edges, fan-in/fan-out, collected cases, runtime, slowest tests, skips, and the executor's
   import count.
4. Record the before/after layering result: which recorded layer violations Phase 3 removed, which it
   left, and which phase owns each remainder.

Gate: every manifest row resolves; before/after measurements use the same method; every structural
change is explained by ownership rather than size.

### Step 10 — Final reconciliation and report

1. Recapture the revision tuple into `revisions-end.tsv` and confirm nothing moved unexpectedly.
2. Run `./devtests/test_strategy/measure_test_strategy.py --runtime` and record the counts.
3. Confirm compute is still unseeded and still inert.
4. Write `report.md`: the tuple, the disposition summaries, the Phase 0/roadmap corrections, every
   split with its reason-to-change justification, every keep with its reason, every deletion with its
   proof of non-use, the named boundary proofs with their results, every gate result, every deviation,
   the measurements, and the definition-of-done verdict.
5. State explicitly what Phase 4 inherits: `drift/evaluation.py` is untouched and still mixes
   orchestration with per-resource evaluation; the IP-range and MAC candidate rules have no owner;
   `production/composer.py` and `production/contract.py` are unsplit; `dnsmasq.py::_normalize_mac`
   remains the recorded second MAC normalization; and the `test_module_boundaries.py` extension to the
   drift evaluators is Phase 4's.
6. State what `vm_first_realization` now inherits from the seam: where a compute actuator would
   register, what an `ActionContext` gives it, and which safety contracts it inherits unchanged.

Gate: one final report with a precise completion state and no unqualified `complete` if any check was
omitted or substituted.

## 8. Verification matrix

| Area | Required proof |
|---|---|
| no execution branching | a recorded search shows zero `action.action_kind ==` and zero `action.reconciler_id ==` execution branches in `executor.py` |
| no feature-module execution import | `executor.py` imports none of `observation`, `reconcile.ledger`, `dnsmasq_apply`, `ansible`, `jobs` for action execution; before/after import lists are recorded |
| seam completeness | every reconciler id reachable from `classify.py` has a handler; `new_node_baseline`'s handler-free status is recorded with its reason |
| registry ownership | `reconcile/registry.py` still owns identity, DAG validation, and topological order; no second registry exists |
| framework restraint | no plugin discovery, provider abstraction, event bus, DI container, or interface with fewer than two current implementations |
| exact target set | the six Section 5.5 tests pass and are named; a host-scoped run still excludes siblings |
| SSH boundary | the three preflight tests plus the OpenSSH conformance gate pass; missing, corrupt, unenrolled, unreachable, and mismatched remain distinct |
| Ansible boundary | the Ansible conformance gate passes; exact `--limit` preserved; forbidden overrides still rejected |
| plan/apply separation | plan mode still has zero side effects; the plan-mode envelope diff is empty |
| evidence | every Section 5.6 rule re-proven by its named test |
| real multi-round transitions | both remain single tests through the real drift engine, planner, and executor |
| envelope and event surface | envelope-code and event-vocabulary diffs are empty; no envelope, event, artifact, plan, drift, or exit-code field changed |
| deterministic artifacts | dnsmasq, hosts-intent, and production bytes and digests identical to baseline under the declared exclusions |
| duplication removed | one `ssh_scan_errors` owner; zero compatibility aliases in `dnsmasq_apply.py` |
| no compatibility artifact | no re-export shim, alias module, dual reader, deprecated import path, or `raising=False` was added |
| test fidelity | every repointed monkeypatch intercepts the same call site; no assertion deleted, weakened, or merged |
| test identity | every `MANIFEST.md` row resolves to an existing passing test at every commit |
| cross-repository discipline | the nintent change is test-only, approved, and limited to two call sites and one import line; no image rebuild, no push by the agent |
| compute inertness | `compute-inert` named and passing; zero desired compute rows |
| measurement | before/after files, lines, coupling, cases, runtime, slowest tests captured with the Phase 0 method |
| scope discipline | `drift/`, `production/`, `compute/`, `dnsmasq*.py` beyond findings 3–4, and the Braindump family are unchanged except for import lines and stale docstrings |

## 9. Reporting and completion states

One `report<N>.md` per step, one `report.md` for the phase. Raw output stays under `.local/`; tracked
prose carries conclusions, decisions, and gate verdicts only. No token, key material, or private
payload appears anywhere.

Use the precise states from `README_DEV.md`:

- `complete` — every exit criterion in Section 10 was exercised and passed;
- `partially complete` — useful work landed and named criteria remain, including the case where the
  Section 3.4 approval is declined and the seam is left unbuilt;
- `blocked` — an external condition actually prevents safe progress. A recoverable local
  test-environment defect is not `blocked`.

`implemented, not deployed` does not apply: there is nothing to deploy. The nintent change is
test-only and needs no image rebuild.

A passing suite is never by itself proof that a boundary held. Name the specific test: the six
target-set tests for the exact target set, the three preflight tests plus the OpenSSH gate for the SSH
boundary, `partial-ipam-progress` for partial progress, `post-mutation-evidence` for real-HTTP
evidence retention, both convergence tests for the real multi-round path, and the plan-mode envelope
diff for end-to-end preservation.

## 10. Exit criteria

Phase 3 is `complete` only when:

1. `executor.py` contains no action-kind branch, no per-reconciler execution branch, and no
   feature-module import for action execution, proven by a recorded search and a before/after import
   list;
2. every current action kind executes through one registered handler behind
   `reconcile/actions/dispatch.py`, with exactly one shared error translation and one action-boundary
   evidence emitter;
3. `reconcile/registry.py` remains the sole owner of reconciler identity, DAG validation, and
   ordering, and no second registry, plugin system, provider abstraction, event bus, or DI container
   was introduced;
4. the exact target set is preserved end to end and positively re-proven by the six named tests at the
   same layer as before, with siblings still excluded from a host-scoped run;
5. the SSH preflight boundary, partial-progress evidence, `mutated=true` after a failed confirmation,
   retained action and preflight records, and the final-drift refresh or truthful
   `final_drift_unknown` are each re-proven by their named test;
6. both real multi-round transitions still run as single tests through the real drift engine, planner,
   and executor;
7. the plan-mode envelope, plan, result, and event stream are identical to the Step 0 baseline under
   the declared exclusions;
8. every envelope field, envelope error code, event name, event field, artifact path, artifact field,
   plan schema field, drift code, exit code, and CLI flag is unchanged;
9. every deterministic artifact is byte-identical to the Phase 0/2 baseline under the declared
   exclusions;
10. the SSH scan-error policy has one owner and both call sites produce byte-identical envelope
    errors; the two `dnsmasq_apply.py` compatibility aliases are deleted with their tests re-owned;
11. no re-export shim, alias, deprecated import path, or `raising=False` was added, and every
    repointed monkeypatch is recorded as intercepting the same call site;
12. the nintent change is test-only, was explicitly approved, and touched only the two `_execute_action`
    call sites and their import line;
13. compute remains inert and no compute row, comparator, planner action, reconciler, or actuator was
    added;
14. the nctl ordinary suite, every conformance gate, the privileged-helper gate, and the Nautobot
    runtime gate in both modes pass, with case counts stated against Phase 2's numbers;
15. every `MANIFEST.md` row resolves to an existing passing test, no manifested ID was renamed without
    its row being updated in the same commit, and the `forced-observation-refresh` precise-ID
    correction is applied;
16. the roadmap and Phase 0 corrections in Section 4.3 are committed; and
17. every omitted or substituted proof is visible in the report and prevents an unqualified
    `complete`.

The outcome is not a shorter `executor.py`. The outcome is that the next agent can add one action kind
by writing one handler module and one table entry, without touching round sequencing, terminal state,
evidence retention, or the exact-target-set contract — and that `vm_first_realization` can add a
compute actuator the same way.
