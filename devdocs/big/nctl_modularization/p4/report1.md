# P4 Step 1 — Audit and frozen dispositions

Status: complete.

Private evidence: `.local/nctl-modularization/p4/20260728T022804Z/phase-surface-search.txt`.

| subject | current owner | disposition / destination | reason and consumers | proof / step |
|---|---|---|---|---|
| IP range normalization, classification, overlap and keys | `drift/evaluation.py` | move to `drift/ip_ranges.py` | addressing policy; evaluators and direct evaluation tests | `test_drift_evaluation`; 2 |
| MAC/interface facts and candidate selection | `drift/evaluation.py` | move to `drift/interfaces.py` | endpoint and node comparison policy | `test_drift_evaluation`; 2 |
| Node candidate ranking | `drift/evaluation.py` | move to `drift/node_candidates.py` | node-only matching policy | `test_drift_evaluation`; 2 |
| Gap-status precedence | both evaluation modules | one `drift/gap_status.py` owner | shared deterministic severity ordering | evaluation tests; 2 |
| MAC normalizer | `evaluation.py`, `dnsmasq.py` | one `drift/interfaces.py` owner | symbol-for-symbol behavior is identical (strip, lowercase, colon removal, require 12 hex digits, emit canonical colon form); dnsmasq bytes are a consumer | dnsmasq/evaluation tests; 2 |
| Node/endpoint/service evaluation | `drift/evaluation.py` | separate evaluator modules | resource comparison policy changes independently | ordinary suite; 3 |
| Snapshot traversal | `evaluation_snapshot.py` | keep orchestration; move only gap status | resolves read-model relationships once; its service content/placement shaping is service-evaluation orchestration and remains colocated | snapshot tests; 3 |
| Production-policy diffs | `comparators.py` | move derivation to `drift/production_policy.py`; retain registration adapter | changes for production composition/report semantics, not registry mechanics | comparator ordering test unchanged; 3 |
| Compute registration seam | `drift/registry.py` | document only | existing decorator registry is sufficient; no compute implementation | `compute-inert`; 4 |
| Production input models | `production/composer.py` | move to `production/models.py` | adapter and comparator both consume them; models are a stable contract | composer/adapter tests; 5 |
| Route resolution and SSH target | `production/composer.py`, `production/contract.py` | `production/routes.py` | connection-policy reason to change; preflight is external consumer | composer/preflight tests; 5 |
| Report translation | `production/composer.py` | `production/reporting.py` | report schema reason to change, isolated from inventory bytes | composer test; 5 |
| Inventory composition | `production/composer.py` | keep in composer | one coherent inventory-shape owner after the above moves | composer tests; 5 |
| Canonical JSON/digest | `production/contract.py` | `nctl_core/canonical.py` | generic deterministic serialization; reconcile and profile callers are not production-schema consumers | deterministic-rendering manifest row; 6 |
| Production validation schema | `production/contract.py` | keep in contract | validation-schema owner after utility/route moves | contract tests; 6 |
| dnsmasq skip/finding policy | `dnsmasq.py` | deliberate keep | audit found a single owner; query/render/apply have separate mapping/rendering/actuation roles | dnsmasq tests; 7 |

The searches found only real consumers of the planned moves: no deprecated import path, re-export, or `raising=False` compatibility hook exists or will be introduced. `deterministic-rendering` is the sole manifest row whose named owning test/import changes in Step 6. The route search also identified test-local production imports; these will be updated directly with production consumers, not preserved through aliases.
