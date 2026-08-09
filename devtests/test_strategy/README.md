# Test Strategy Conformance Gates

These tests are narrow normative-boundary checks. They use only synthetic data and fixture-owned
loopback processes/files; they must not read `.local/secrets`, `nctl.toml`, a live inventory, or a
managed SSH store.

The repository-wide gate list is the
[test strategy command matrix](../../README_DEV.md#test-strategy-command-matrix) in the root
developer guide.

## Test tiers and admission

- **Tier A — transition, mutation, trust, authority, or safety boundary:** assert positive
  evidence that the action, preflight, write, observation, denial, or durable evidence path ran.
- **Tier B — deterministic rule:** use readable parameter tables or focused cases for a distinct
  validation, normalization, parser, or rendering failure mode.
- **Tier C — presentation:** retain smoke-level coverage unless a UI/API surface owns mutation
  authority.

Before adding a test, record its distinct failure mode, tier, why a different layer is not the
clearer owner, the fixture replacing an external boundary, and the positive evidence proving the
path ran. During review, consolidate input-only variants, reject unverified external-tool mocks,
require exact scope and no-repeat assertions for mutations, and update the command matrix for
every new environment prerequisite.

## Nautobot exact-local-source runtime gate

Run this gate from the superproject root. It stages the checked-out `nintent`, `nauto`, `nctl`,
and `nodeutils` sources, plus only nctl's missing pure-Python HTTP dependencies, under one
fixture-owned container path. It prints each resolved module path, revision, and tracked-index
digest before running; a deployed package cannot satisfy the gate.

```bash
./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb
```

Use `--clean` for migration/final verification. This removes and recreates only the named,
test-owned `test_nautobot` database, runs `makemigrations --check --dry-run`, then runs the same
exact-local-source suite. An optional test label keeps iteration narrow:

```bash
./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb \
  nautobot_intent_catalog.tests.TEST_MODULE
```

It requires the healthy local `nautobot-nautobot-1` and `my_postgres_db` containers documented in
the root developer guide, Docker, and each local checkout's uv environment. The gate explicitly
clears `NAUTOBOT_TOKEN` and `GITHUB_TOKEN`; it uses only test-created token/rows and loopback HTTP.
On every normal success or failure path it removes its exact `/tmp/test-strategy-nautobot-runtime-*`
stage. It never restarts, rebuilds, deploys, or reconfigures the persistent scratch stack.

Run the OpenSSH gate from the superproject root:

```bash
uv run --project nctl pytest -q devtests/test_strategy/test_openssh_conformance.py
```

It requires `ssh`, `sshd`, `ssh-keygen`, and `ssh-keyscan`. A missing binary is a failure because
this is a required Phase 3 gate. The test creates an ED25519 host key, client key, authorized-keys
file, managed store, and loopback-only `sshd` under pytest's temporary directory; teardown stops
only that exact process and pytest removes the directory.

Run the Ansible boundary gate from the superproject root:

```bash
uv run --project nctl pytest -q devtests/test_strategy/test_ansible_conformance.py
```

It requires `ansible-inventory` and `ansible-playbook`. Its inventory has nctl's closed SSH policy;
the fixture playbook declares `connection: local` only so its exact-host check/apply proof writes
temporary markers rather than contacting an SSH target.

## Compute-contract freshness gate

Run this from the superproject root whenever either nintent's compute contract or nctl's bound
consumer changes:

```bash
uv run --project nctl pytest -q devtests/test_strategy/test_compute_conformance.py
```

It imports only the sibling nintent checkout, regenerates the deterministic owner fixture in
memory, and compares it with nctl's committed fixture. It has no network, Nautobot, or secret
prerequisite.
