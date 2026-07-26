# Test Strategy Phase 0 Step 8 Report — Audit Mocked External Behavior

Parent: [plan.md](plan.md) — Step 8.

Status: **partially complete** (Step 8 complete: 6 core external boundary assumptions audited against normative software versions and recorded in `external-boundaries.tsv`; overall Phase 0 in progress).

## 1. External Boundary Audit Summary

| Boundary Domain | Required Normative Comparison | Normative Software Version | Current Mocked Tests | Maintained Real Proof Status | Proposed Smallest Real Conformance Case | Phase 3 Gap Owner |
|---|---|---|---|---|---|---|
| **OpenSSH** | `ssh-keyscan`, `ssh-keygen`, `ssh -G`, non-default port, stable `HostKeyAlias`, malformed store | `OpenSSH_10.0p2` | `nctl/tests/test_ssh_enroll.py` | Unit stubs pass | Disposable OpenSSH fixture with real binary | Phase 3 OpenSSH gate |
| **Ansible** | Inventory parsing, variable precedence, forbidden overrides, exact `--limit`, check mode | `ansible [core 2.21.1]` | `nctl/tests/test_production_composer.py` | Role helper unit test passes | `ansible-inventory` / `ansible-playbook --check` dry gate | Phase 3 Ansible gate |
| **Nautobot / Django** | GraphQL/REST/Job discovery, permissions, transactions, ORM constraints, field rules | `Nautobot 3.1.3` / `Django 5.2.14` | `nintent` local fast suite (13 skips) | Full 304-case disposable Nautobot App suite passes in Docker | Disposable Nautobot App real HTTP suite | Phase 3 Nautobot real-HTTP node-link gate |
| **HTTP Transport** | 401/403 status, malformed JSON, timeouts, post-write refetch | HTTP/1.1 REST & GraphQL | `nctl/tests/test_nautobot.py` | `respx` / `httpx` mock tests pass | Disposable real HTTP denial & timeout suite | Phase 3 real-HTTP error gate |
| **Filesystem** | Atomic private writes (`0600`/`0700`), canonical paths, corruption, restart reads | POSIX / macOS filesystem | `nctl/tests/test_events.py` | Real temporary file tests pass | Real filesystem atomic write/read/corruption gate | Phase 3 durable evidence gate |
| **Privileged Helper** | Proxmox allowlisted `pvesh` helper boundary | `pvesh` / sudo allowlist | `nodeutils/tests/test_pvesh_helper_integration.py` | Real integration test passes (~2.2s) | Existing real helper integration test | Retained nodeutils integration gate |

## 2. Key Findings & Boundary Safety Rules

1. **Normative OpenSSH & Ansible Verification**:
   - Ordinary unit tests fake `ssh-keyscan` and `ansible-inventory` execution. These assumptions must be validated against real `OpenSSH_10.0p2` and `ansible [core 2.21.1]` in Phase 3 without weakening strict SSH policy.

2. **Disposable Nautobot Real-HTTP Node-Link Gap**:
   - The disposable Nautobot App suite passes all 304 cases in Docker, but `desired_node_link` fail-closed reset variants rely on unit mocks rather than real HTTP requests. Phase 3 will close this gap.

## 3. Evidence Artifact Created

- `.local/test-strategy/p0/20260726T034839Z/external-boundaries.tsv`: Detailed audit table mapping external boundary assumptions to normative versions, current unit mocks, maintained real tests, smallest proposed real conformance cases, and Phase 3 gap owners.

## 4. Gate Summary & Handoff

- Every externally defined assumption is mapped to either a maintained real proof or a precisely bounded Phase 3 gap owner.
- Ready to proceed to Step 9: Resolve compatibility against named consumers (`report9.md`).
