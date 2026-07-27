# Test Strategy Phase 4 — Step 1 Report: Maintained Nautobot Runtime Gate

Parent: [plan.md](plan.md), Step 1.

Status: **`complete`**.

## Implemented gate

Added [`run_nautobot_runtime_gate.sh`](../../../../devtests/test_strategy/run_nautobot_runtime_gate.sh)
and documented it in [`devtests/test_strategy/README.md`](../../../../devtests/test_strategy/README.md).
It is the single exact-local-source entry point for the Nautobot App runtime tier:

```bash
./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb
./devtests/test_strategy/run_nautobot_runtime_gate.sh --clean
```

The optional final argument is a test label for iteration. The gate stages the four local sources
and only nctl's missing pure-Python HTTP dependency chain under one fixture-owned path, then prints
the source revisions, tracked-index digests, and resolved module files. It fails if any of
`nautobot_intent_catalog`, `jobs`, `nctl_core`, or `nodeutils_collect` resolves outside that path.
It explicitly clears `NAUTOBOT_TOKEN` and `GITHUB_TOKEN`; the runtime tests create their own token
and use loopback HTTP.

`--keepdb` reuses the named test database. `--clean` drops only `test_nautobot`, lets the test
runner reconstruct it, and runs `makemigrations --check --dry-run` before the suite. Neither mode
reads root `nctl.toml` or `.local/secrets`, nor restarts, rebuilds, deploys, or reconfigures the
persistent scratch stack.

## Verification and isolation

Both modes collected and passed the Phase 3 expected **290** cases with no model migration change.
The stage path was absent after each run. The clean run recreated the test-owned database; the
keepdb run then reused it successfully. The persistent web, worker, scheduler, PostgreSQL, and
Redis prerequisites remained running.

Early local invocations exposed only a gate-owned cleanup detail: `docker cp` may create
root-owned staged files, so cleanup now uses root only for the exact generated stage path. The
known stale test database was recreated through the documented `--clean` boundary rather than
touching the persistent scratch database. Both corrections were bounded to the gate's declared
ownership.

No secret, real inventory, external host, Proxmox endpoint, public-network call, or production
mutation was used.
