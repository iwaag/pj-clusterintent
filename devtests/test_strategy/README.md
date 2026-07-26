# Test Strategy Conformance Gates

These tests are narrow normative-boundary checks. They use only synthetic data and fixture-owned
loopback processes/files; they must not read `.local/secrets`, `nctl.toml`, a live inventory, or a
managed SSH store.

Run the OpenSSH gate from the superproject root:

```bash
uv run --project nctl pytest -q devtests/test_strategy/test_openssh_conformance.py
```

It requires `ssh`, `sshd`, `ssh-keygen`, and `ssh-keyscan`. A missing binary is a failure because
this is a required Phase 3 gate. The test creates an ED25519 host key, client key, authorized-keys
file, managed store, and loopback-only `sshd` under pytest's temporary directory; teardown stops
only that exact process and pytest removes the directory.

