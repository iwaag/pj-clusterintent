# Step 5a report — Conformance test (real TLS stack)

## What was done

- `devtests/test_strategy/test_mtls_conformance.py`, the mTLS analogue of
  `test_openssh_conformance.py`: real keys (`cagent_api.ca`), a real CA, a
  real `ssl.SSLContext`-wrapped loopback server running the actual
  `cagent_api.server`/`auth`/`store`/`worker` code (not a stand-in), and a
  throwaway `Ledger` — all owned by pytest's `tmp_path` and a fixture that
  shuts the exact server down on teardown. DesiredNode validity is faked
  (`_FakeNodeResolver` with a fixed valid-UUID set) rather than read from a
  live Nautobot, matching both the plan's split ("OpenCode side can be
  faked here; this test owns the TLS/ledger boundary, not the agent
  conversation") and `devtests/test_strategy/README.md`'s rule that these
  gates must not read `nctl.toml` or a live inventory — `node_resolver.py`'s
  own real-HTTP behavior already has its own real-stub-server test
  (`cagent/tests/test_node_resolver.py`, Step 4).
- Six cases, each asserting positive evidence beyond "no error"
  (README_DEV lesson 1):
  1. **valid + registered + active**: `202` then `GET` confirms
     `identity == {"class": "node", "uuid": ..., "cert_serial": ...}` —
     the actual UUID from the cert, not just "some 200".
  2. **revoked serial**: `403 forbidden`, plus a direct ledger read
     confirming `state == "revoked"` (not inferring revocation from the
     HTTP response alone).
  3. **expired cert**: asserts the connection itself raises `ssl.SSLError`
     with an expiry-related message — a TLS handshake failure, never
     reaching HTTP, matching contract.md's check ordering. Minted via
     `ca.sign_node_cert_for_test`'s explicit past `not_after` (the
     CSR-based production path, `sign_node_cert`, has no way to do this on
     purpose — confirmed as a design property, not a gap, in Step 2).
  4. **unregistered (CA-signed, not in ledger)**: `403 forbidden`, plus a
     direct ledger read confirming `get(serial) is None`.
  5. **UUID with no valid DesiredNode** (the fake resolver's set doesn't
     include it — the pruned/retired case): `403 forbidden`.
  6. **session owned by another UUID**: node A creates a session, node B
     (separately CA-signed and ledger-registered) tries to continue it —
     `403 forbidden`, plus `store.list_sessions()` confirming the session
     is still recorded as owned by node A, not reassigned or corrupted.
- Added the gate to `README_DEV.md`'s command matrix (`mTLS conformance`
  row), run via `uv run --project cagent pytest -q
  devtests/test_strategy/test_mtls_conformance.py` from the superproject
  root — chose `cagent`'s uv environment (not `nctl`'s, unlike the other
  conformance gates) since this test only needs `cagent_api` and its
  `cryptography` dev dependency, no `nctl_core` import.

## Deviations from the plan

None. All five plan-listed minimum cases are covered as six concrete test
functions (the plan's case 5, "UUID-mismatch," names two distinct
scenarios with "or" — cert SAN UUID with no valid DesiredNode, *or* a
session owned by another UUID — both are covered as separate tests rather
than picking one).

## State

`uv run --project cagent pytest -q devtests/test_strategy/test_mtls_conformance.py`
from the superproject root: **6 passed**. `uv run pytest -q` in `cagent/`:
still **63 passed** (this gate lives in `devtests/`, not `cagent/tests/`,
so it doesn't change that count). No CA/ledger material or server process
left running — the fixture's `tmp_path` and explicit `httpd.shutdown()`
own all cleanup.

## Next

Step 5b — enroll agpc and pass a real request over mTLS. **Live, needs
explicit user approval before the first SSH/Ansible action against agpc**,
per the plan.
