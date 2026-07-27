# Test Strategy Phase 3 — Step 6 Report: Observation Schema Traversal

Parent: [plan.md](plan.md), Step 6.

Status: **`complete`**.

## Maintained producer-to-reader proof

Extended `nintent/nautobot_intent_catalog/tests/test_p3_node_link_http.py` with the bounded
Step 6 conformance case. It creates one deterministic synthetic inventory through nodeutils'
real `build_inventory_report()` and `SCHEMA_VERSION`; it does not construct a second report
dictionary for nauto or nctl.

The first submission persists the observer Device, because nauto's real two-stage contract
intentionally defers Proxmox writes until that Device has a stable ORM UUID. The same
builder-produced report, with its producer-owned `nodeutils.proxmox.v1` subtree, is then sent to
nauto's real `IngestNodeutilsInventory` Job. It contains one valid LXC guest and one invalid-VMID
guest. The Job records target-local partial evidence, creates the valid VM, and does not create
the invalid sibling.

Finally nctl's real `NautobotClient` fetches the actual local GraphQL endpoint and its real actual
source parser reads the persisted state. The gate positively asserts schema version, identity,
collection time, inventory source, primary interface, dnsmasq managed-file path/digest, Proxmox
partial state, valid LXC `vmid`/type, and absence of the invalid guest. The traffic is local
GraphQL only; the test token, temporary reports, and Job summary are test-owned and retained only
inside Django's rolled-back test transaction.

## Focused owners retained

Malformed/unsupported/stale report rejection and bounded Proxmox validation remain owned by the
nauto ingest suites; strict actual-GraphQL custom-field parsing remains owned by nctl's actual
source suite. These focused owners passed without duplicating their full matrices in the runtime
gate. nodeutils' real privileged-helper integration test also passed and its accepted output stays
owned by nodeutils.

## Verification and cleanup

```text
nautobot-server test nautobot_intent_catalog.tests.test_p3_node_link_http --keepdb -v 1  10 passed
cd nodeutils && uv run pytest -q tests/test_inventory_report.py tests/test_pvesh_helper_integration.py  17 passed
cd nauto && python3 -m unittest discover -s tests -p 'test_*ingest*.py'  34 passed
cd nctl && uv run pytest -q tests/test_sources_actual.py  13 passed
```

The exact-local-source runtime resolved nintent, nauto, nctl, and nodeutils from separate
`/tmp/p3-*` copies. The copies and copied pure-Python HTTP dependencies were removed by exact
path after the run. No persistent database row, real report, external host, Proxmox endpoint, or
privileged host helper was contacted.
