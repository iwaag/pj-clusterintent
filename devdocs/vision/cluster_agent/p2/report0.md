# Step 0 report — Research: Python mTLS + cert tooling decisions

## What was done

Ran a throwaway loopback probe (`ssl.SSLContext` server wrapping a stdlib
`HTTPServer` socket, `http.client.HTTPSConnection` client, both certs minted
by the `cryptography` package), executed via `uv run python <script>` from
`cagent/`. Findings written to [`mtls_notes.md`](mtls_notes.md); script was
scratch-only, not committed.

Verified end-to-end:

- `ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)` + `CERT_REQUIRED` +
  `load_verify_locations` + `load_cert_chain`, wrapping the server socket
  before `serve_forever()`, correctly requires and verifies a client cert
  against a throwaway CA. No framework change needed to
  `cagent_api.server`/`main`.
- `self.connection.getpeercert()` inside the request handler surfaces a URI
  SAN as `('URI', 'urn:clusterintent:node:<uuid>')` — this is the Step 4
  identity-extraction seam.
- An expired client cert fails at the TLS handshake itself
  (`SSLV3_ALERT_CERTIFICATE_EXPIRED`), before any HTTP request reaches the
  handler — confirms the contract's planned check ordering (TLS validity
  window first, ledger/DesiredNode checks second) and confirms conformance
  test case 3 is a handshake-level failure to assert on.

CA tooling: chose the `cryptography` package (option b) over LibreSSL CLI
scripting (option a). Command node `openssl` is confirmed **LibreSSL
3.3.6**, which lacks convenient expired-cert minting; one Python code path
serves both the real CA (Step 2) and the conformance test's
expired/mismatched fixtures (Step 5a). Added `cryptography>=50.0.0` to
`cagent`'s `dependency-groups.dev` (not `dependencies`) via
`uv add --group dev cryptography` — resolved `cryptography==50.0.0`. The
running `cagent-api` server process itself stays import-free of
`cryptography`: it only needs stdlib `ssl` to wrap its socket and read the
already-parsed `getpeercert()` dict, not to parse certs itself. Only the
CA/ledger tooling and tests import `cryptography`.

Revocation: confirmed application-level ledger check at connect/request
time is sufficient, no CRL/OCSP, per the plan.

agpc reachability: this command node is itself cluster node `agstudio`
(`agstudio.local`, `192.168.0.100`, confirmed via `scutil`/`ifconfig`). agpc
resolves via `agpc.local` (`192.168.0.110` per
`ansible_agdev/inventories/generated/production.yml`), reachability already
confirmed per `.local/localenv_memo.md`. agpc's DesiredNode UUID is
`c82421c3-c42a-4bea-91ce-7468ae8a249c`. `CAGENT_API_HOST` will move to
`192.168.0.100` in Step 4; OpenCode stays on `127.0.0.1:4097`, untouched.
curl `--cert/--key/--cacert` support on agpc itself was not checked here —
deferred to Step 5b's live work per the plan, to avoid an extra SSH
round-trip against a live node just to check a curl version ahead of time.

## Deviations from the plan

None. All Step 0 checklist items were verified as listed in the plan.

## State

No repo code changed except `cagent/pyproject.toml` /
`cagent/uv.lock` (new dev dependency). No live process started or left
running.

## Next

Step 1 — write `p2/contract.md` as the Phase 2 delta over the frozen p1
contract.
