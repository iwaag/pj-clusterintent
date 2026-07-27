# Test Strategy Phase 4 — Step 0 Report: Frozen Baseline

Parent: [plan.md](plan.md), Step 0.

Status: **`complete`**.

## Frozen state

Private evidence was created at `.local/test-strategy/p4/20260727T114614Z/` with mode `0700`;
its files are mode `0600`. It is ignored by Git. The superproject was clean on `main` at
`12dcde36aaa0e554a4c4d750f4a0d4d32bff6738`, with no ahead/behind delta. The frozen submodule
tuple matches the plan baseline:

| Repository | Revision | State |
|---|---|---|
| `nctl` | `87f1737e3a1de24217a916d28d46f85adf16aee2` | clean, `main...origin/main` |
| `nintent` | `6a4b2afc891b9404c9cbdc09e4c4d6c1e8379711` | clean, `main...origin/main` |
| `nauto` | `e1f350c8cadf53077e232e9f90fd91cc704457b9` | clean, `main...origin/main` |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | clean, `main...origin/main` |
| `ansible_agdev` | `da0dffe6bc0124bfb2dbbc8125660e4740bcaaa9` | clean, `main...origin/main` |

Tracked test-file SHA-256 fingerprints, branch state, and the initial filesystem state were
recorded privately. No tracked file was modified during the capture except this sanitized report.

## Installed prerequisites and scratch state

The installed versions were recaptured rather than copied from Phase 0: Python `3.14.2`, uv
`0.11.24`, Git `2.50.1`, Docker `29.4.0`, Docker Compose `5.0.1`, OpenSSH `10.0p2`, and Ansible
core `2.21.1`. Host-level `pytest`, `psql`, and `redis-cli` are intentionally absent; the
component-local uv environments and service containers are the supported interfaces.

The three declared persistent Nautobot containers, PostgreSQL, and Redis were healthy. Ports
`8000`, `5432`, and `6379` were held by the declared Docker/OrbStack boundary. The named,
test-owned `test_nautobot` database exists (checked through `my_postgres_db` as the documented
`nautobot` role). No container, database, network, volume, or service was restarted, rebuilt,
reconfigured, or removed.

## Command and manifest inventory

The private work queue points to all Phase 0 manifests and the Phase 1–3 dispositions/results;
Step 4 will resolve their owners into the tracked sanitized manifest. The current commands are
split among component documents, `devtests/test_strategy/README.md`, and Phase 0–3 reports.
The only currently maintained conformance commands are the root-scoped OpenSSH and Ansible gates;
the exact-local-source Nautobot procedure remains Phase 3 prose-only. The matrix work in Steps
1 and 3 is therefore required, not a documentation-only confirmation.

The capture also found historical active name
`test_p3_node_link_http.py`, scheduled for the bounded Step 2 rename. No secret value was read or
recorded. No external or production command was run.

## Gate result

The revision tuple, tool/prerequisite state, scratch before-state, test fingerprints,
command inventory, and private manifest sources are captured. Step 0 is complete.
