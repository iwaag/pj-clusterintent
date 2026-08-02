# Step 0 — mTLS mechanics research notes

Throwaway script (not committed): loopback `ssl.SSLContext` server +
`http.client.HTTPSConnection` client, both using certs minted by the
`cryptography` package. Ran with `uv run python <script>` from `cagent/`.

## What was tested and confirmed

1. **Server-side TLS wrap works with stdlib only.** Wrapping the
   `ThreadingHTTPServer`/`HTTPServer` socket via
   `ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)` +
   `verify_mode = ssl.CERT_REQUIRED` + `load_verify_locations(ca_cert)` +
   `load_cert_chain(server_cert, server_key)`, then
   `httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)`, accepts
   a valid mTLS client and rejects handshakes that don't present a
   CA-signed cert. No change needed to `cagent_api.server` beyond wrapping
   the socket before `serve_forever()` — `BaseHTTPRequestHandler` itself is
   TLS-agnostic.
2. **`self.connection.getpeercert()` surfaces a URI SAN**, per-connection,
   inside the request handler. Confirmed shape:
   `{'subjectAltName': (('URI', 'urn:clusterintent:node:<uuid>'),), ...}`.
   This is the seam Step 4 uses to extract the DesiredNode UUID — no new
   dependency needed for extraction, just parsing the tuple.
3. **Expired certs fail at the TLS handshake layer**, before any HTTP
   request is processed: client raises
   `SSLError: [SSL: SSLV3_ALERT_CERTIFICATE_EXPIRED]`. Confirms contract.md
   Step 1's design ("TLS handshake proves key possession and CA signature +
   validity window" happens before any ledger/DesiredNode check can run) and
   confirms conformance test case 3 (expired cert) is a handshake-level
   failure, not an application-level rejection.

## CA tooling decision: `cryptography` (Python), not LibreSSL CLI

Command node `openssl` is **LibreSSL 3.3.6** (confirmed:
`openssl version` → `LibreSSL 3.3.6`), which lacks OpenSSL 3.x conveniences
(`-addext` behavior differs, no easy way to mint an already-expired test
cert). Chose option (b) from the plan: the `cryptography` package for both
the real CA/signing tooling (Step 2) and the conformance test's expired/
mismatched fixtures (Step 5a) — one code path instead of two.

- Added `cryptography>=50.0.0` to `cagent`'s `dependency-groups.dev` (not
  `dependencies` — keeps the running server zero-runtime-dependency;
  `cryptography` is only needed by the CA/ledger tooling and tests, which
  run as separate console scripts / test processes, not imported by
  `cagent_api.server`/`main`). Installed via `uv add --group dev
  cryptography` inside `cagent/`; resolved to `cryptography==50.0.0` (plus
  `cffi`, `pycparser`).
- Leaf keys use `ec.SECP256R1()` (P-256) — small, fast, no LibreSSL/OpenSSL
  version-skew concerns since key generation happens entirely in Python.

**Revised runtime-dependency note for Step 4**: unlike the CA/ledger tooling,
the running `cagent-api` server process itself only needs the stdlib `ssl`
module to wrap its socket and verify against a CA cert file — it does not
need to *parse* certificates with `cryptography` at request time, only read
`getpeercert()`'s already-parsed dict. So `cagent-api`'s own runtime import
graph can stay dependency-free; only `cagent-ca`/`cagent-ledger` tooling and
tests import `cryptography`.

## Revocation strategy

Confirmed application-level: check the cert serial against the ledger at
connect/request time. No CRL/OCSP — API server and ledger are on the same
host, per the plan and roadmap Phase 2 hint.

## Identity encoding

URI SAN `urn:clusterintent:node:<uuid>` (plan's recommendation), confirmed
`getpeercert()` returns it as `('URI', 'urn:clusterintent:node:<uuid>')` in
`subjectAltName`. Parsing: split on the last `:`, validate the remainder is
a canonical UUID (reuse the `_UUID_RE` shape from
`nctl_core/ssh_trust.py:validate_desired_node_id`, or just `uuid.UUID(...)`
which normalizes/validates equivalently).

## agpc reachability (for Step 4's `CAGENT_API_HOST` bind and Step 5b)

- Command node (this machine) is itself a cluster node: `agstudio`
  (`agstudio.local`, LAN IP `192.168.0.100`), confirmed via
  `scutil --get LocalHostName` / `ifconfig`.
- agpc resolves via mDNS `agpc.local` (LAN IP `192.168.0.110` per
  `ansible_agdev/inventories/generated/production.yml`); confirmed reachable
  per `.local/localenv_memo.md` ("agpc.local / agstudio.local は疎通確認済み").
  agpc's DesiredNode UUID is `c82421c3-c42a-4bea-91ce-7468ae8a249c` (same
  file, `nctl_ssh_host_key_alias: nctl-node-c82421c3-...`).
- `CAGENT_API_HOST` moves from `127.0.0.1` to `192.168.0.100` (or `0.0.0.0`
  bound on the LAN interface) in Step 4 so agpc can dial it; OpenCode itself
  is untouched on `127.0.0.1:4097`.
- The server TLS cert's SAN/CN must cover whatever address agpc actually
  dials (`192.168.0.100`, or `agstudio.local` if curl on agpc resolves mDNS)
  — decided at Step 2 signing time, confirmed live in Step 5b.
- curl `--cert/--key/--cacert` support on agpc: not checked yet (agpc is a
  live cluster node — deferred to Step 5b's live work per the plan, not
  worth an extra SSH round-trip just to check curl's version ahead of time).

## No framework change needed

Everything above works with stdlib `ssl` + `http.server` as currently used
by `cagent_api.server`/`main`. Step 4 wraps the socket and adds an identity
extraction + ledger/DesiredNode check seam; no new HTTP framework, no change
to the async/worker/evidence design from Phase 1.
