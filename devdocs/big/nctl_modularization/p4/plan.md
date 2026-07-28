# nctl Modularization Phase 4 Implementation Plan: Drift Evaluation and Production Composition Boundaries

Parent: [roadmap.md](../roadmap.md) — Phase 4. Predecessor: [p3](../p3/) (see Section 2).

Status: proposed. Local, offline, nctl-only. No cross-repository change, no deployment, no live
actuation.

## 1. Goal

Give per-resource drift evaluation and production composition cohesive owners, and leave the
comparator seam demonstrably ready for the compute evaluator that `vm_first_realization` will write.

```text
current
  drift/evaluation.py (1,236 lines) mixing three resource evaluators with IP-range normalization
    and overlap classification, MAC/interface candidate selection and scoring, fact extraction,
    and formatting helpers
  + gap-status derivation and MAC normalization each implemented twice
  + production/composer.py (833) mixing composition, route resolution, and report shaping
  + production/contract.py (807) mixing an input validation schema with the canonical-JSON/digest
    utility that three non-production callers depend on
  + no written statement of where a compute evaluator would register

to
  one owner per pure deterministic rule (IP ranges, MAC/interface candidates, gap status)
  + one owner per resource evaluator, behind the unchanged comparator registry
  + composition, route resolution, and report shaping separated where each has its own reason
    to change
  + a documented compute-evaluator registration point with no placeholder
  + byte-identical artifacts, envelopes, drift codes, and manifest coverage
```

Phase 4 changes internal structure only. It does not touch `reconcile/` beyond import lines, does
not write the `nctl/README.md` responsibility map (Phase 5), and does not make compute actionable.

## 2. Inherited state

Phase 3 is recorded through `p3/report8.md` as **partially complete**, with two residuals:

- Step 6's physical test-ownership split is incomplete: the IPAM action-result matrix and the direct
  action-boundary evidence cases still live in `tests/test_reconcile_executor.py`.
- Steps 9–10 and `p3/report.md` were not written, because the local Nautobot runtime gate stopped
  during test-database setup (`duplicate key value violates unique constraint
  "pg_type_typname_nsp_index"` for `dcim_module`) in both `--keepdb` and `--clean` modes. This is
  outside the Phase 3 diff.

Phase 4 does not adopt those residuals. Step 0 records them as inherited, and:

- Phase 4 changes drift and production code that the runtime gate exercises through nintent's
  `test_desired_node_link_http.py`. Attempt the runtime gate once in Step 8. If it is still
  unhealthy for the same pre-existing reason, record it as unavailable with the evidence — a
  substituted proof is visible in the report and prevents an unqualified `complete`.
- The Phase 3 test-split residual may be closed opportunistically if a Phase 4 step touches the same
  file; otherwise it stays a Phase 3 residual and is restated in the Phase 4 report.

Planning-time tuple, all six worktrees clean: superproject `f46a3a6`, nctl `786b61b`, nintent
`4f46bc8`, nauto `6dab422`, nodeutils `775ed7f`, ansible_agdev `66b31c8`. Installed image nintent is
`84ac0b1`. nctl ordinary collects **970**.

## 3. Scope

### In scope

`drift/evaluation.py`, `drift/evaluation_snapshot.py`, `drift/comparators.py`,
`drift/service_placement.py`, `drift/status.py` (import line only), `production/composer.py`,
`production/contract.py`, `production/adapter.py`, `production/derivation.py`, the `dnsmasq*.py`
family, new modules created by this phase, the import lines of any module referencing a moved
symbol, the affected `nctl/tests/` modules, `devtests/test_strategy/MANIFEST.md`, and this phase's
documents.

### Prohibited

Everything else is at the implementer's discretion. These six are not:

1. **No observable change.** Envelope fields and error codes, event names and fields, artifact paths
   and fields, drift codes, target statuses, exit codes, CLI flags, and command names stay
   identical. Deterministic artifact bytes and digests stay byte-identical to the Step 0 baseline
   (declared generation-id/timestamp fields excluded). A changed digest is a defect, not an update.
2. **No compute activation.** No comparator, planner action, reconciler, actuator, or seeded compute
   row. Documenting the registration point must not create a stub, placeholder, or empty
   registration.
3. **No new framework.** No plugin discovery, provider abstraction, event bus, DI container, or
   second registry. An interface needs two current implementations, or one plus a second named in an
   approved roadmap.
4. **No compatibility artifact.** No re-export shim, alias, deprecated import path, dual reader, or
   `monkeypatch.setattr(..., raising=False)` to keep a moved symbol or stale patch target alive
   (`README_DEV.md`, breaking-change phase).
5. **No cross-repository or deployment action.** No nintent/nauto/nodeutils/ansible_agdev source
   change, no image rebuild, no submodule push, no submodule-pointer move by the agent.
6. **No live actuation.** No `reconcile --yes`, Job apply, SSH enrollment or Ansible run against real
   nodes, nodeutils collection from real nodes, ingest, or Proxmox operation. Read-only `nctl`
   commands and plan-mode `nctl reconcile` against the local scratch Nautobot are allowed, as are
   both runtime-gate modes against the scratch stack.

### Discretion

Module names, file granularity, the order of Steps 2–7, and whether to combine steps into one commit
are the implementer's call. A proposed split may be dropped if Step 1 refutes its reason to change —
record the keep and its reason; absence of a finding is a finding. Any new module must satisfy the
roadmap's module admission rules.

## 4. Planning-time findings

Verified against the tuple in Section 2. Step 1 re-verifies each and records confirmed/refuted; a
refuted finding withdraws its proposal in that step's report.

1. **`drift/evaluation.py` holds four independent groups.** The three resource evaluators
   (`evaluate_node_intent` :215, `evaluate_endpoint_intent` :329, `evaluate_service_intent` :540)
   change when a resource's comparison policy changes. The IP-range rules
   (`normalize_endpoint_ip_string` :106 through `classify_endpoint_ip_ranges` :177, plus
   `_classified_ip_ranges` :1120, `_overlap_records` :1152, and the three sort/identity keys
   :1181–:1205) change when addressing policy changes and have a second consumer: six of them are
   imported directly by `tests/test_drift_evaluation.py`, and `dnsmasq.py` re-derives range facts.
   The MAC/interface candidate rules (`_matching_ip_candidates` :922,
   `_interface_candidates_for_endpoint` :935, `_interface_facts` :972, `_primary_mac_candidate` :982,
   `_primary_mac_candidate_from_facts` :1000, `_interface_sort_key` :1231) change when candidate
   selection or scoring changes. Node candidate ranking (`_rank_node_candidates` :707,
   `_node_candidate_score` :739) is a fourth, node-only rule.
   **Proposal:** pure-rule modules under `drift/` for the IP-range and MAC/interface groups, and one
   module per resource evaluator; each importing nothing but `sources.*` read-models and stdlib.
2. **Gap-status derivation is duplicated.** `evaluation.py::_status_from_gaps` :1028 and
   `evaluation_snapshot.py::_status_from_gaps` :294 return the same severity precedence
   (`conflict`, `missing`, `partial`, `needs_review`, `unknown`, else `satisfied`) through different
   code. **Proposal:** one owner, consumed by both.
3. **MAC normalization is implemented twice.** `evaluation.py::_normalize_mac` :1206 and
   `dnsmasq.py::_normalize_mac` :636 (the residual Phase 3 handed forward). Step 1 compares them
   symbol-for-symbol; if identical in behavior, one owner and one caller-side import. If they differ,
   record the difference and its reason rather than unifying it silently — the dnsmasq path feeds
   deterministic artifact bytes.
4. **`evaluation_snapshot.py` splits along a real boundary, with one exception.** It owns snapshot
   traversal and evaluator invocation (`evaluate_all_nodes` :33, `evaluate_all_endpoints` :49,
   `evaluate_all_services` :73) and is correctly orchestration; but `evaluate_all_services` also
   carries the content-spec/placement evidence shaping (:208–:293), and it holds the duplicate from
   finding 2. **Proposal:** confirm the boundary, move the gap-status duplicate out, and decide
   whether content-spec shaping belongs beside `drift/service_placement.py`.
5. **`drift/comparators.py` is a registry adapter that also carries production policy.** Its six
   `@register` adapters are thin, except `production_policy` :176 (95 lines) which composes a full
   production inventory inside a comparator and shapes three diff records (:271, :291, :304).
   **Proposal:** keep the adapters where they are; give the production-policy diff derivation its own
   owner if Step 1 confirms it changes for production-composition reasons rather than comparator
   reasons.
6. **The compute evaluator's registration point already exists and needs only a written statement.**
   `drift/registry.py::register(resource_type)` is the seam; a compute comparator would
   `@register("compute_instance")`, receive `(SourceSnapshot, DriftContext)`, read
   `snapshot.desired.compute_platforms` / `.compute_instances` (already typed and populated by
   `compute/collection.py`), and emit `DiffRecord`s whose `Target.kind` is a new string —
   `drift/model.py` deliberately leaves `Target.kind` open. `drift/status.py::UNKNOWN_CODES` is where
   its no-data codes would extend. Document exactly this; add nothing.
7. **`production/composer.py` mixes three reasons to change.** Composition (`compose_production_inventory`
   :282, `_compose_host` :676, `_build_inventory_document` :788, `render_production_inventory_yml`
   :818) changes when inventory shape changes. Route resolution (`resolve_effective_route` :497,
   `try_resolve_operational_values` :520, `ResolvedSshTarget` :205) changes when connection policy
   changes and has an external consumer — `reconcile/ssh_preflight.py:31` imports `ResolvedSshTarget`,
   and `inventory_trust.py:18` reproduces the same priority chain through
   `contract.select_local_route`. Report shaping (`build_node_report_record` :545,
   `_placement_desired_entry` :605, `_operational_override_entry` :621, `_placement_effect_entry`
   :636, `_placement_evidence` :777, `render_production_report_json` :830) changes when report
   schema 3.0 changes and is already documented as pure translation that must not influence inventory
   bytes. **Proposal:** three owners. The `NodeInput`/`PlacementInput`/`RealizedState` data models are
   imported by `production/adapter.py:23` and `drift/comparators.py:55`; Step 1 decides whether they
   move with composition or become their own contract module (this also resolves Phase 0's deferred
   `adapter.py` decision).
8. **`production/contract.py` holds two responsibilities with disjoint consumers.**
   `canonical_json` :155 / `canonical_json_digest` :171 are a deterministic serialization utility
   consumed by `reconcile/fingerprint.py:15` and `production/profiles.py:25` — neither is production
   composition — and the manifest's `deterministic-rendering` row points at their test. The rest is
   the production input/output validation schema (`validate_deployment_profiles` :177,
   `validate_production_inventory_document` :397, `validate_production_report_v3` :473, and the
   `_validate_*` family). A third group is route/variable resolution (`select_local_route` :319,
   `resolve_connection_variables` :340, `merge_host_variables` :380), which belongs with finding 7's
   route owner rather than with a validation schema. **Proposal:** split canonical serialization out
   (it is not production-specific — consider a top-level module), move the route rules to the route
   owner, and leave the validation schema as `production/contract.py`. Moving
   `canonical_json_digest` changes the `deterministic-rendering` manifest row's owning test ID:
   update the row in the same commit.
9. **The dnsmasq family has no duplicated skip/finding policy.** Skip and finding derivation lives
   only in `dnsmasq.py` (`_dns_skip_reasons` :390, `_dhcp_skip_reasons` :400, `_base_skip_reasons`
   :407, `_dhcp_range_skip_reasons` :494, `_blocking_finding` :521, `_skip_entry` :548,
   `_range_skip_entry` :564). `dnsmasq_query.py` maps snapshot rows, `dnsmasq_render.py` builds the
   envelope, `dnsmasq_apply.py` actuates. Phase 0 already recorded the family as `keep`.
   **Proposal:** record the audit result as an absence-of-finding, fix only finding 3's MAC
   duplication, and leave the family alone.
10. **`tests/test_module_boundaries.py` covers only the `compute` package.** Phase 3 handed forward
    the extension to the drift evaluators. **Proposal:** extend it to the pure-rule and evaluator
    modules this phase creates, asserting they load no CLI, HTTP, Nautobot runtime, Ansible, or
    subprocess module.

## 5. Steps

Each step ends with one `report<N>.md` and one commit. A failing gate stops the step rather than
starting the next one.

### Step 0 — Freeze and baseline

1. Confirm all six worktrees clean; record the tuple and the installed image revision.
2. Confirm zero desired compute platform and instance rows.
3. Reproduce nctl ordinary (**970**) and compute conformance (**1**).
4. Re-run the Phase 0 measurement method into `*-before.tsv`: package/file/line totals, import edges,
   fan-in/fan-out, layer violations, collected cases, runtime, slowest tests.
5. Capture baselines: the deterministic artifacts (`render dnsmasq`, `render hosts-intent`,
   `render production` into a phase-owned temp directory), `nctl drift --json` and `nctl status`
   envelopes, and a plan-mode `nctl reconcile --json` envelope. Record the declared exclusion fields.
6. Record the Section 2 inherited Phase 3 residuals.

### Step 1 — Audit and freeze dispositions

No behavior change. Verify each Section 4 finding; write a symbol-level disposition table (symbol,
current module, destination, layer, reason to change, consumers, owning test, step) including every
deliberate keep with its reason; write the test/manifest impact table; run the roadmap's required
searches over this phase's surface and classify the matches.

### Step 2 — One owner per pure deterministic rule

Move the IP-range rules, the MAC/interface candidate rules, and node candidate ranking out of
`drift/evaluation.py` into pure modules. Unify the gap-status duplicate (finding 2) and decide
finding 3's MAC normalization. Repoint `tests/test_drift_evaluation.py`'s direct imports. Tests move
with their subject; no assertion is deleted, weakened, or merged.
Gate: nctl ordinary; the pure modules import only read-models and stdlib.

### Step 3 — One owner per resource evaluator

Split node, endpoint, and service evaluation into their own modules. Confirm or correct the
`evaluation_snapshot.py` boundary (finding 4) and the `comparators.py` production-policy question
(finding 5). Orchestration keeps snapshot traversal and evaluator invocation; the comparator registry
and its ordering-independence test are untouched.
Gate: nctl ordinary; `run_comparators` output for a fixed snapshot is identical to Step 0.

### Step 4 — Document the compute evaluator registration point

Write finding 6 into the drift package docstring or `drift/registry.py`'s existing prose: the
decorator call, the arguments a comparator receives, the desired collections it reads, the
`Target.kind` freedom, and where its no-data codes extend `UNKNOWN_CODES`. No stub, no placeholder,
no empty registration. Re-run `compute-inert` by name.
Gate: `tests/test_compute_actuation_inert.py::test_valid_compute_collections_produce_no_drift_and_no_plan_actions` passes; compute rows remain zero.

### Step 5 — Production composition, route resolution, report shaping

Apply finding 7. Keep `NodeOutcome`'s existing guarantee that report translation cannot influence
inventory bytes, and prove it: the composed inventory bytes and report bytes for a fixed input are
identical to Step 0.
Gate: nctl ordinary; `tests/test_production_composer.py` passes with its assertions unchanged;
production artifact bytes identical.

### Step 6 — Canonical serialization versus validation schema

Apply finding 8. Repoint `reconcile/fingerprint.py`, `production/profiles.py`, `inventory_trust.py`,
and the tests. Update the `deterministic-rendering` manifest row in this commit and re-run its gate.
Gate: `canonical_json` bytes and digests unchanged; every manifest row still resolves.

### Step 7 — dnsmasq audit and module-boundary test

Record finding 9's audit result. Extend `tests/test_module_boundaries.py` per finding 10.
Gate: nctl ordinary; dnsmasq artifact bytes identical.

### Step 8 — Re-prove, measure, report

1. Re-capture every Step 0 baseline and diff. All diffs empty under the declared exclusions.
2. Run and name individually: `dnsmasq-convergence`, `non-dhcp-ipam-convergence`,
   `desired-mac-safe-stop`, `compute-inert`, `deterministic-rendering`, `unmanaged-no-delete`,
   `reconcile-host-scope`, `reconcile-dry-plan`, `operation-evidence-reader`. Not "the suite passed".
3. Run the offline matrix: nctl ordinary, compute conformance, nintent Django-free, nauto ordinary,
   nodeutils ordinary, Ansible helper, OpenSSH conformance, Ansible conformance, privileged-helper
   integration.
4. Attempt the Nautobot runtime gate in both modes. If it fails for the Section 2 pre-existing
   reason, record it as unavailable with the evidence and state that it prevents an unqualified
   `complete`.
5. Verify every `MANIFEST.md` row resolves to an existing passing test.
6. Re-run the Phase 0 measurements into `*-after.tsv`; record which layer violations this phase
   removed and which remain, with their owning phase.
7. Write `report.md`: the tuple, every split with its reason to change, every keep with its reason,
   every deletion with its proof of non-use, the named boundary proofs and their results, gate
   results, deviations, measurements, the inherited Phase 3 residuals, and the definition-of-done
   verdict. State what Phase 5 inherits (the README responsibility map, both extension seams, the
   module admission rules) and what `vm_first_realization` inherits (the documented compute-evaluator
   registration point plus Phase 3's action seam).

## 6. Evidence

Private evidence under `.local/nctl-modularization/p4/<UTC timestamp>/`: the tuple captures, the
disposition and test/manifest impact tables, before/after measurement TSVs, the artifact and envelope
baselines and their comparisons, and gate results. Raw command output stays there; tracked prose
carries conclusions only. No token, key material, or private prose in any file.

## 7. Exit criteria

Phase 4 is `complete` only when:

1. drift orchestration contains no per-resource evaluation logic, and the pure IP-range,
   MAC/interface, and gap-status rules each have exactly one owner;
2. the `evaluation.py` / `evaluation_snapshot.py` boundary is confirmed or corrected, with the reason
   recorded either way;
3. the compute evaluator's registration point is documented with no placeholder, and compute remains
   inert with zero rows;
4. production composition, route resolution, and report shaping are separated where Step 1 confirmed
   an independent reason to change, and every keep is recorded with its reason;
5. canonical serialization and the production validation schema have separate owners, or the merge is
   recorded with its reason;
6. the dnsmasq skip/finding audit result is recorded, and no second MAC normalization survives without
   a recorded reason;
7. every deterministic artifact, drift envelope, status envelope, and plan-mode reconcile envelope is
   identical to the Step 0 baseline under the declared exclusions;
8. every envelope field, error code, event, artifact field, drift code, target status, exit code, and
   CLI flag is unchanged;
9. no compatibility shim, alias, re-export, or `raising=False` was added, and every moved test
   intercepts the same call site with its assertions unchanged;
10. `tests/test_module_boundaries.py` covers the new pure modules and passes;
11. every `MANIFEST.md` row resolves to an existing passing test, with any moved ID updated in the
    same commit;
12. the offline matrix passes with case counts stated against Step 0, and the runtime gate either
    passes in both modes or is recorded as unavailable for a documented pre-existing reason; and
13. every omitted or substituted proof is visible in the report and prevents an unqualified
    `complete`.

The outcome is not fewer lines. It is that a compute evaluator can be added by writing one pure rule
module, one evaluator, and one `@register` adapter — without editing a 1,200-line file.
