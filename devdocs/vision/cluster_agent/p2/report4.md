# Step 4 report — mTLS in the API server + connect-time checks

## What was done

- `cagent/src/cagent_api/auth.py`: `extract_node_identity(peercert)` parses
  the URI SAN and lowercases the cert serial (stdlib `getpeercert()`
  returns it uppercase; `ca.py`'s `serial_hex` is lowercase — confirmed the
  mismatch live and normalized at the one seam that reads both).
  `CertAuthenticator(ledger, node_resolver)` implements contract.md's
  connect-time checks 2 and 3 (TLS handshake itself, check 1, already
  happened by the time this code runs — an unverified/expired cert never
  reaches it): ledger lookup by serial (`403` if unregistered/revoked),
  then live DesiredNode validity (`403` if pruned/retired), returning a
  `store.Identity(class="node", uuid, cert_serial)` on success. A
  `NodeResolverError` (Nautobot unreachable) surfaces as `502
  nautobot_unavailable`, not a silent pass or a `403`.
- `cagent/src/cagent_api/node_resolver.py`: `NautobotNodeResolver`, one
  `urllib.request` GraphQL POST (`{ desired_nodes { id lifecycle } }`) per
  check, **no caching** — checked live every request, which is what makes
  `nctl prune` (and the retired-lifecycle case, treated the same way)
  de-facto revocation without any extra step. Reads the connection URL and
  token from the **existing** `nctl.toml` (`[nautobot] url`/`token_env`/
  `token_file`) via stdlib `tomllib`, rather than inventing a second
  Nautobot-config surface. Chose `urllib.request` over `nctl_core`'s
  `httpx`-based client since cagent is a separate, independent project
  (matches the `nctl serve` precedent in README_DEV of not folding
  cluster-agent-shaped code into nctl) and one GraphQL POST doesn't warrant
  either a new runtime dependency or an import across project boundaries.
- `store.py`: `Identity` is now `(identity_class, uuid, cert_serial)`,
  matching contract.md's evidence shape exactly (`as_dict()` returns
  `{"class", "uuid", "cert_serial"}`). Session ownership
  (`continue_session`) now compares `identity.uuid`, replacing the deleted
  class+name comparison.
- `server.py`: the header-parsing `_identity()` is gone. `make_handler`
  and `build_server` now take an `authenticate(handler) -> Identity`
  callable — production wires `auth.CertAuthenticator`; this is the seam
  the plan asked for so unit tests don't need real TLS. `build_server` also
  gained an optional `ssl_context` parameter: when given, it wraps the
  listening socket with `ctx.wrap_socket(..., server_side=True)` before
  returning (confirmed in Step 0 that a wrapped listening socket hands back
  already-handshaken per-connection `SSLSocket`s from `accept()`, so no
  other code needed to change).
- `main.py`: builds the server TLS context (`CERT_REQUIRED`, verify against
  the CA cert), constructs `Ledger`/`NautobotNodeResolver`/
  `CertAuthenticator`, and wires them into `build_server`. `CAGENT_API_HOST`
  default changed from `127.0.0.1` to `0.0.0.0` (OpenCode's own URL/bind is
  untouched, still `127.0.0.1:4097`). New env vars: `CAGENT_LEDGER_PATH`,
  `CAGENT_CA_DIR`, `CAGENT_TLS_SERVER_CERT`/`_KEY`, `CAGENT_NCTL_TOML`
  (all documented in `cagent/README.md`, which also gained the
  `cagent-ca`/`cagent-ledger` operator walkthrough).
- **Design choice**: no plaintext loopback listener was kept (the plan left
  this open). Chose to drop it entirely — one identity story, not two, and
  nothing in Phase 1/2 needs plaintext local debugging enough to justify a
  second code path with its own (lack of) authentication story.
- Tests: `tests/fakes.py` gained `FakeAuthenticator`, reading a test-only
  `X-Test-Node-Uuid` header instead of a real cert — used by every existing
  `test_server.py` case (updated: identity/ownership assertions now check
  `uuid` instead of `name`; the old bad-identity-class test was deleted
  since identity class is no longer client-declared). New:
  `tests/test_auth.py` (7 tests: SAN/serial extraction, all three
  accept/reject paths, the 502 Nautobot-unreachable path) and
  `tests/test_node_resolver.py` (7 tests, against a **real loopback HTTP
  stub server**, not a mocked `urllib` — active/retired/pruned lifecycle
  outcomes, GraphQL error surfacing, unreachable-host handling, and
  `nctl.toml` token-env/token-file loading).
- **Manual full-stack smoke check** (scratch, not committed): built a real
  `ssl.SSLContext`-wrapped `build_server` with a real CA-signed node cert,
  a real `Ledger`, and a fake (always-valid) node resolver; sent a real
  mTLS `POST /requests` — `202 queued`. Revoked the cert's serial via the
  same `Ledger` instance mid-run and repeated the identical request on a
  fresh connection — `403 forbidden`, immediately, no restart. This is
  the same shape Step 5a's conformance test formalizes, run once here to
  catch wiring bugs before writing that test.

## Deviations from the plan

None. All Step 4 checklist items (TLS wrap, per-request ledger + DesiredNode
checks, UUID session ownership, `CAGENT_API_HOST` rebind, README update,
identity-injection seam that doesn't need real TLS for unit tests) are
present. The plaintext-loopback-listener choice was explicitly left open by
the plan; documented the "didn't keep it" decision above per its
"say so in the report" instruction.

## State

`uv run pytest -q` in `cagent/`: **63 passed** (was 49 at end of Step 3;
+7 `test_auth.py`, +7 `test_node_resolver.py`, `test_server.py` updated
in place, one obsolete header-validation test removed). No CA/ledger
material or live evidence was left under `.local/`/`~/.local/state/cagent/`
— the full-stack smoke check ran entirely under a temp directory, deleted
after the run. No live process left running.

## Next

Step 5a — the real-TLS-stack conformance test
(`devtests/test_strategy/test_mtls_conformance.py`), covering valid,
revoked, expired, unregistered, and UUID-mismatch paths. Step 5b (enroll
agpc) needs explicit approval before touching that node.
