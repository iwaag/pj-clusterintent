# Test Strategy Phase 3 — Step 2 Report: Disposable OpenSSH Conformance Gate

Parent: [plan.md](plan.md), Step 2.

Status: **`complete`**.

## Implemented gate

Added [devtests/test_strategy/test_openssh_conformance.py](../../../../devtests/test_strategy/test_openssh_conformance.py)
and its usage documentation. The gate requires the installed `ssh`, `sshd`, `ssh-keygen`, and
`ssh-keyscan` binaries; absence is an explicit assertion failure, never a skip.

Each case creates a temporary ED25519 host key, client key, authorized-keys file, strict managed
store, and a configuration-validated `sshd` bound only to `127.0.0.1` on a collision-safe
non-default port. It starts no external connection and reads or writes no real SSH store.

Using nctl's real store, probe, fingerprint, and production-target preflight functions with the
real binaries, it proves:

- a bare UUID-derived `HostKeyAlias`, non-default port, and matching offered key yield `ready`;
- a legacy bracketed alias is not enrolled, and an endpoint-named store line fails closed as an
  invalid managed store;
- a different offered/managed key yields `mismatch` with public SHA-256 fingerprints only;
- malformed and invalid-UTF-8 stores raise the strict store-read failure; and
- `ssh -G` resolves the exact host, port, alias, fixture-only known-hosts path, strict checking,
  disabled host-IP checking, and disabled host-key updates.

OpenSSH 10.0p2 normalizes input `yes`/`no` booleans in `ssh -G` output to `true`/`false`; the gate
asserts those normative effective values while the nctl policy builder remains the exact
`StrictHostKeyChecking=yes` / `UpdateHostKeys=no` source.

## Verification and cleanup

```text
uv run --project nctl pytest -q devtests/test_strategy/test_openssh_conformance.py  2 passed
cd nctl && uv run pytest -q tests/test_ssh_preflight.py tests/test_ssh_enroll.py    64 passed
```

Fixture teardown terminates the exact `sshd` process and verifies its port is closed. All keys,
stores, configuration, and logs remain in pytest's temporary directory and were removed. The
tracked test/report evidence contains only public fingerprints and no raw key material.
