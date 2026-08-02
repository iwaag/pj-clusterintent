# Step 2 report — Local CA and signing tooling

## What was done

- `cagent/src/cagent_api/ca.py`: pure functions over `cryptography` objects
  — `build_ca` (self-signed CA, `BasicConstraints(ca=True)`, `key_cert_sign`
  usage), `sign_server_cert` (DNS/IP SANs, `SERVER_AUTH` EKU),
  `sign_node_cert` (takes a real CSR + an explicit operator-supplied
  `node_uuid` argument; **uses the CSR's public key but ignores its
  self-claimed subject entirely** — the UUID SAN and CN are always set from
  the caller's argument, ­never parsed out of the CSR), and
  `sign_node_cert_for_test` (a test/dev-only variant that skips the CSR
  round trip and accepts an explicit `not_before`/`not_after`, used later by
  the Step 5a conformance test to mint an already-expired cert — the
  CSR-based production path has no way to do this on purpose, which is
  correct). Identity encoding: `urn:clusterintent:node:<uuid>`, with
  `node_uuid_to_san_uri`/`san_uri_to_node_uuid` round-tripping through
  `uuid.UUID(...)` so a malformed UUID fails loudly at signing time.
  `public_key_fingerprint` is SHA-256 of the DER SubjectPublicKeyInfo, hex —
  a public identifier for ledger storage. Leaf and CA keys are `SECP256R1`
  (P-256).
- `cagent/src/cagent_api/ca_cli.py`: the `cagent-ca` console script (added
  to `pyproject.toml`'s `[project.scripts]`), subcommands `init`,
  `sign-server`, `sign-node`, `show-ca`. Default CA dir is
  `<repo-root>/.local/cagent-ca/` (gitignored). `init` refuses to overwrite
  an existing CA without `--force` (overwriting invalidates every
  previously signed cert — the message says so). CA private key is written
  `chmod 0600`. `sign-node` prints the exact `cagent-ledger register`
  command an operator runs next (Step 3's ledger owns registration, kept as
  a manual, visible next step rather than auto-registering from inside
  `sign-node` — separates "the CA vouches for this key" from "the ledger
  currently trusts it," matching the plan's ledger-vs-CA separation).
- `cagent/tests/test_ca.py` (8 tests) and `cagent/tests/test_ca_cli.py`
  (4 tests): CA self-signature verifies, node cert SAN round-trips to the
  correct UUID and uses the CSR's public key while ignoring its
  self-claimed CN, server cert DNS/IP SANs, expired-cert minting, malformed
  UUID rejection, fingerprint stability/uniqueness, CLI init/sign-node
  end-to-end (including interop against a real `openssl`-generated CSR,
  checked manually below), overwrite guard, key file permissions, and
  "sign without an existing CA" failure.
- Manual scratch verification (not committed): `cagent-ca init` →
  `cagent-ca sign-server` (with `--dns agstudio.local --ip 192.168.0.100`,
  the addresses Step 0 identified) → an `openssl ecparam`/`openssl req`
  -generated real CSR signed via `cagent-ca sign-node`, confirmed with
  `openssl x509 -text` that the SAN URI carries the exact UUID passed on
  the command line. Confirms interop with whatever CSR tool Step 5b ends up
  using on agpc (not necessarily Python/`cryptography`).

## Deviations from the plan

None. Chose modest lifetimes as suggested: CA default 1825 days (5y), leaf
default 365 days (1y) — both overridable via `--days`.

## State

`uv run pytest -q` in `cagent/`: **37 passed** (was 25 at end of Phase 1;
+8 `test_ca.py`, +4 `test_ca_cli.py`). No CA material was committed — the
manual scratch CA/keys/certs used for verification were created under
`/tmp` and deleted after the check; nothing persists under `.local/` from
this step.

## Next

Step 3 — auth ledger + `cagent-ledger` CLI surface.
