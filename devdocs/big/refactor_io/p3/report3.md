# Phase 3 Step 3 Report — nctl batch writer and clients

## Result

Complete locally. `nctl_core.desired_write` is now the single nctl owner of
the desired-state batch envelope and POST path. Lifecycle writes, actual-node
links, and compute realization links submit that client. Lifecycle preserves
its GraphQL refetch confirmation and performs no request when already at the
requested state. Compute realization uses one atomic two-operation batch,
eliminating the former platform-first partial write path.

`nctl desired apply -f FILE` is available as the thin operator client. It
accepts only a Phase 0 envelope, is dry-run by default, commits only with
`--yes`, supports standard input through `-f -`, and emits the raw artifact
with `--json`.

## Verification

Focused batch/lifecycle/ledger/CLI tests: **42 passed**.

`cd nctl && uv run pytest -q --durations=20`: **987 passed**.

The repository's former PATCH-route test expectations were replaced with exact
batch POST envelopes, including a 409 artifact that leaves an action
unmutated.
