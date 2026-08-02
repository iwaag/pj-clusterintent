# cluster_agent Phase 2 Plan: node authentication (mTLS) + one real node

References: [roadmap.md](../roadmap.md), [refined_idea.txt](../refined_idea.txt),
[p1/contract.md](../p1/contract.md), [p1/report5.md](../p1/report5.md)

## Goal

Put per-node client-certificate authentication (mTLS) in front of the Phase 1
cagent API, back it with an auth ledger bound to DesiredNode UUIDs, enroll one
real node (agpc), and pass a real request from that node over mTLS.

## Exit criteria (from the roadmap, restated)

1. An enrolled client on agpc sends a request over mTLS and gets a response.
2. A revoked certificate is rejected.
3. A real-TLS-stack conformance test passes, covering at least: valid,
   revoked, expired, unregistered, and UUID-mismatch certificate paths.

## Scope and freedom

Experimental cluster, no production workload. This is a breaking-change
phase: the Phase 1 identity-header stub is **deleted, not kept as a
fallback** — identity comes from the client certificate only. Break the API,
CLI, evidence identity shape, and config freely; update the contract document
to match instead of preserving compatibility.

Only the three roadmap-wide prohibitions apply:

1. Responses remain reads + plan presentation only (unchanged from Phase 1).
2. OpenCode stays on 127.0.0.1. Only the cagent API becomes reachable from
   the LAN/VPN, and only over mTLS.
3. No secrets in Git, binaries, or evidence. New in this phase: the CA
   private key and any node private key are secrets. CA material lives under
   `.local/` (gitignored); node keys never leave their node. Evidence and
   the ledger store public identifiers only (UUID, cert serial, public-key
   fingerprint, not-after date).

Everything else — CA tooling, ledger storage format, cert lifetime, SAN
encoding details, whether a plaintext loopback dev port survives — is the
implementer's choice, recorded in the report.

## Steps

House style: one step at a time, `p2/reportN.md` + one commit per step.
Steps 0–4 touch only the command node and are approval-free. **Step 5
touches agpc (a real cluster node) — pause for user approval before the
first SSH/Ansible action against it.**

### Step 0 — Research: Python mTLS + cert tooling decisions

Verify the mechanics before building. Deliverable: `p2/mtls_notes.md`
recording what was actually tested locally (throwaway keys, loopback):

- `cagent-api` is stdlib-only `http.server.ThreadingHTTPServer`
  ([server.py](../../../../cagent/src/cagent_api/server.py)). Confirm that
  wrapping its socket with `ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)`,
  `verify_mode = ssl.CERT_REQUIRED`, `load_verify_locations(ca_cert)` works,
  and that the handler can read the peer certificate per-connection via
  `self.connection.getpeercert()` — including extracting a SAN URI from it.
  If this works (it should), no framework change is needed.
- Decide the certificate identity encoding. Recommended: a URI SAN carrying
  the DesiredNode UUID, e.g. `urn:clusterintent:node:<uuid>`, per
  refined_idea.txt. Confirm `getpeercert()` surfaces it.
- Pick CA tooling. **Gotcha: macOS ships LibreSSL 3.3** (`openssl version`),
  which lacks some OpenSSL 3.x conveniences (e.g. `-addext` behavior
  differs, no `-not_after` for minting expired test certs). Two viable
  paths: (a) LibreSSL + config-file SAN sections for the real CA, or (b) a
  small Python script using the `cryptography` package for both the real CA
  and test certs. Option (b) gives one code path for production-ish signing
  and for minting expired/mismatched certs in the conformance test — likely
  the better trade. Either way `cryptography` may be added to cagent's dev
  dependency group; keep the runtime zero-dependency if practical.
- Confirm revocation strategy: application-level check of the cert serial
  against the ledger at connection/request time is sufficient. Do **not**
  build CRL/OCSP distribution — the API server and the ledger live on the
  same host.
- Confirm how agpc will reach the API: find the command node's address as
  seen from agpc (mDNS name or VPN IP — check how Ansible/SSH reaches
  things today), and note that `CAGENT_API_HOST` must change from
  `127.0.0.1` to that reachable interface. Check curl on agpc supports
  `--cert/--key/--cacert` (any modern curl does; just confirm once in
  Step 5's live work if SSH access isn't approved yet).

### Step 1 — Contract update (`p2/contract.md`)

Write the Phase 2 contract as a delta over the frozen p1 contract (copy or
diff-style, implementer's choice; make it self-standing enough to read
alone). Changes to specify:

- **Identity**: the `X-Cluster-Agent-Identity-*` headers are removed. A
  node's identity is the DesiredNode UUID taken from the verified client
  certificate's SAN. The request body's node slug/ID is never trusted as
  identity (roadmap hint — restate it in the contract).
- **Connect/request-time checks**, in order: TLS handshake proves key
  possession and CA signature + validity window; then the API checks the
  ledger (serial registered, not revoked) and that the corresponding
  DesiredNode currently exists and is allowed to make requests. Define the
  error responses for each rejection (the TLS layer rejects handshake-level
  failures with no HTTP response; ledger/DesiredNode failures return the
  p1 error envelope with a `forbidden`-class code).
- **Session ownership** is now enforced: a session created by UUID X can
  only be continued/cancelled/listed by UUID X.
- **One sentence** stating that `nctl prune` of a DesiredNode is de-facto
  revocation: a UUID that no longer resolves to a valid DesiredNode fails
  the connect-time check automatically (roadmap requirement).
- The `human` identity class remains defined but has no entrance in
  Phase 2 (it returns in Phase 4 with its own authentication). Say so
  explicitly so its absence is not read as removal.

### Step 2 — Local CA and signing tooling

A self-signed local CA on the command node:

- CA private key + issued-cert records under `.local/` (suggested:
  `.local/cagent-ca/`). The CA certificate (public) may be committed or
  distributed as a file — implementer's choice; it must reach agpc in
  Step 5 either way.
- A signing entry point (script or `cagent-*` subcommand) that takes a CSR
  plus an explicit DesiredNode UUID, and emits a client certificate with
  the UUID in the SAN. **The UUID is an operator-supplied argument bound at
  signing time — never parsed out of the CSR's self-claimed fields.**
- Also emit the API server's own TLS server certificate from the same CA
  (curl on agpc will use `--cacert` with this CA, so the server cert must
  chain to it and match the name/IP agpc dials).
- Choose modest lifetimes and write them down (e.g. CA 5y, leaf 1y — no
  rotation automation this phase).

### Step 3 — Auth ledger + CLI surface

The ledger owns "which public key of which DesiredNode is currently
trusted". Storage is free choice — a single JSON/JSONL file under `.local/`
(same durable-evidence spirit as `nctl ops` / cagent evidence) is entirely
adequate; don't reach for a database.

- Row shape (minimum): DesiredNode UUID, cert serial, public-key
  fingerprint, issued/not-after timestamps, state
  (`active` / `revoked` + revoked-at). Public identifiers only.
- **A human-usable CLI is required** (roadmap: don't repeat the
  DesiredWorkspace no-GUI mistake). Suggested: a `cagent-ledger` console
  script alongside the existing `cagent-evidence`, with `list`, `show`,
  `register` (called by/after Step 2 signing), and `revoke <serial>`.
- Enrollment writes to the ledger; revocation is a ledger state flip, no
  cert reissue needed to test it.

### Step 4 — mTLS in the API server + connect-time checks

Wire it together in cagent:

- TLS-wrap the server socket; require and verify client certs against the
  CA. Extract the UUID from the SAN; attach it as the request identity
  (replacing the deleted header stub in store/evidence — evidence now
  records `{"class": "node", "uuid": ..., "cert_serial": ...}` or similar).
- Per-request checks: serial active in ledger; DesiredNode UUID currently
  valid. For the DesiredNode check, shell-out or HTTP to the source nctl
  already uses is fine — note that `nctl_core/ssh_trust.py` already derives
  SSH `HostKeyAlias` values from DesiredNode UUIDs, so the UUID⇄node
  resolution surface exists; reuse whatever is cheapest (direct Nautobot
  REST query is also acceptable). Cache per-connection if latency bites;
  don't optimize preemptively.
- Enforce session ownership by UUID.
- Bind: `CAGENT_API_HOST` moves to the LAN/VPN-reachable interface.
  OpenCode stays untouched on loopback. Whether to also keep a plaintext
  loopback listener for local debugging is implementer's choice — if kept,
  give it a distinct identity handling story and say so in the report.
- Update `cagent/README.md` (start commands, new env vars/paths).
- Existing unit tests will break where they used identity headers — update
  them to the new identity injection seam. Keep the seam such that unit
  tests don't need real TLS (real TLS is Step 5's conformance test's job).

### Step 5a — Conformance test (real TLS stack)

`devtests/test_strategy/test_mtls_conformance.py`, the mTLS analogue of
`test_openssh_conformance.py`: real keys, a real TLS loopback server
(the actual cagent server code, not a stand-in), a throwaway CA and ledger,
all test-owned and cleaned by the fixture. **No mock-only mTLS tests**
(README_DEV lesson 2 — tests must not just agree with our own assumptions
about TLS). Verify at minimum:

1. valid + registered + active → request accepted, identity == expected UUID;
2. revoked serial → rejected with the contract's error;
3. expired cert → TLS handshake fails (mint with past not-after via the
   Step 0 tooling);
4. unregistered (CA-signed but not in ledger) → rejected;
5. UUID-mismatch (cert SAN UUID ≠ any valid DesiredNode / session owned by
   another UUID) → rejected.

Each case asserts positive evidence of the rejection/acceptance path, not
just "no error" (README_DEV lesson 1). Add a row for this gate to the
README_DEV command matrix. The OpenCode side can be faked here — this test
owns the TLS/ledger boundary, not the agent conversation.

### Step 5b — Enroll agpc and pass a real request (LIVE — needs approval)

**Pause for user approval before touching agpc.** Then, following
refined_idea.txt's enrollment procedure over the existing exact-target SSH
path (`~/.ssh/ansible_key`; Ansible ad-hoc from `ansible_agdev/` or plain
ssh — implementer's choice for a single node; the Ansible role comes in
Phase 3, don't build it now):

1. Generate a dedicated private key + CSR **on agpc**; the private key
   never leaves the node.
2. Fetch the CSR to the command node over that SSH path.
3. Sign it bound to agpc's DesiredNode UUID (the UUID Ansible/nctl actually
   resolves for that host, not a self-claimed slug), register in the ledger.
4. Place the certificate + CA cert on agpc over the same path.
5. From agpc, with curl only
   (`curl --cacert ... --cert ... --key ... --data @file`; bodies via
   `@file`, never inline args — roadmap hygiene), send a realistic request
   (e.g. the Phase 1 "I want S3-compatible storage" question), poll to
   completion, and confirm a useful answer.
6. Revoke agpc's serial via `cagent-ledger revoke`, repeat the request from
   agpc, confirm rejection. Re-activate (or re-enroll) afterwards and
   confirm it works again, so the phase ends with agpc enrolled and usable.
7. Confirm evidence on the command node records the UUID/serial identity
   for these requests.

Save the transcript as `p2/e2e_transcript.md` (redact nothing but there
should be nothing secret in it — key material stays in files, not in
commands). Known state: agpc reachable; agbach/agdnsmasq unresponsive is
expected and irrelevant here.

## Useful facts collected at planning time

- cagent is currently **zero-runtime-dependency stdlib Python** (see
  `cagent/pyproject.toml`); API on `127.0.0.1:8788`, OpenCode on
  `127.0.0.1:4097`, started manually (`cagent/README.md`). Phase 1 evidence
  lives per-request with the identity recorded verbatim — that identity
  field is what Step 4 replaces.
- Phase 1 unit tests already fake OpenCode (`cagent/tests/fakes.py`); the
  same pattern serves the conformance test's non-TLS concerns.
- Command node openssl is **LibreSSL 3.3.6** — the main reason Step 0
  recommends deciding tooling before writing the CA scripts.
- The DesiredNode-UUID-as-stable-identity pattern is already proven in this
  repo: SSH trust uses it as `HostKeyAlias`
  (`nctl/src/nctl_core/ssh_trust.py`). Phase 2's cert SAN is the same idea
  on a different channel; the fix_sshkey lessons (identity from the stable
  UUID, never from the route or a self-claimed name) transfer directly.
- The separation to preserve (roadmap): nintent owns DesiredNode
  existence/validity; the ledger owns which key is trusted. Don't write
  cert data into Nautobot, and don't have the ledger duplicate
  DesiredNode validity — check it live.
- Phase 3 will distribute a curl wrapper via Ansible to all target nodes.
  Nothing in Phase 2 needs to anticipate it beyond keeping the curl
  invocation from Step 5b simple enough to wrap in a shell script.

## Out of scope for Phase 2

Human/smartphone entrance and its auth (Phase 4), SSE, the Ansible
distribution role and wrapper (Phase 3), Go CLI, CRL/OCSP infrastructure,
key rotation automation, rate limits, session TTLs, workspace-level
identity, and any relaxation of the reads+plans-only authorization rule.
