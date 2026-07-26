# Test Strategy Phase 0 Step 7 Report — Inventory Fixtures and Repeated Semantic Payloads

Parent: [plan.md](plan.md) — Step 7.

Status: **partially complete** (Step 7 complete: shared fixtures, factories, and repeated semantic payloads cataloged with trust boundaries, scope, determinism, and dispositions in `fixture-ownership.tsv`; overall Phase 0 in progress).

## 1. Shared Fixture & Factory Inventory Summary

| Fixture / Helper Category | Submodule | Location | Semantic Payload | Trust Boundary | Disposition | Notes / Proposed Merge |
|---|---|---|---|---|---|---|
| `nintent_factories` | `nintent` | `nautobot_intent_catalog/tests/factories.py` | Intent model factories (Factory Boy) | Internal / Synthetic | `keep` | Owns desired model test data creation; clean teardown. |
| `nctl_reconcile_stubs` | `nctl` | `nctl/tests/test_reconcile_executor.py` | Executor mock stubs & response envelopes | Internal / Mocked | `keep` | Owns multi-round reconcile executor testing. |
| `nctl_dnsmasq_render_fixtures` | `nctl` | `nctl/tests/test_dnsmasq_render.py` | Golden dnsmasq records & digest fixtures | Internal / Golden | `keep` | Owns dnsmasq rendering contract assertions. |
| `nctl_sources_fixtures` | `nctl` | `nctl/tests/test_sources_desired.py` | Canonical desired state YAML payloads | Internal / Schema | `keep` | Owns YAML parsing and schema validation tests. |
| `nauto_fake_orm` | `nauto` | `nauto/tests/test_proxmox_cluster_vm_upsert.py` | In-memory fake ORM database store | Internal / Fake | `replace` | Proposed for replacement in Phase 2 with fast pure policy tests + disposable Nautobot app gate. |
| `nodeutils_pvesh_integration_fixture` | `nodeutils` | `nodeutils/tests/test_pvesh_helper_integration.py` | Real privileged Proxmox helper env | External / Real | `keep` | Owns real privileged helper boundary testing (~2.2s). |
| `ansible_agdev_helper_fixture` | `ansible_agdev` | `ansible_agdev/roles/.../tests/test_helper.py` | Shell helper boundary stubs | Internal / Shell | `keep` | Owns role helper execution boundary tests. |

## 2. Trust Boundary & Merging Rules

1. **Trust Boundary Separation**:
   - Desired state, actual state, observed nodeutils reports, OpenSSH trust stores, and CLI presentation payloads are kept strictly separated.
   - Structurally similar dictionary fixtures are not merge candidates when they represent different authority or trust boundaries.

2. **Orphan & Accidental Dependency Analysis**:
   - Zero orphan fixture files found across the 5 submodules.
   - Zero accidental public network calls found in ordinary test fixtures (all tests use local/disposable state).

## 3. Evidence Artifact Created

- `.local/test-strategy/p0/20260726T034839Z/fixture-ownership.tsv`: Catalog of all shared fixtures, factories, and payload builders with semantic purpose, trust boundary, mutability/determinism, external behavior, and preliminary disposition.

## 4. Gate Summary & Handoff

- Every shared fixture has a named contract, trust boundary, and disposition.
- Ready to proceed to Step 8: Audit mocked external behavior (`report8.md`).
