# Phase 5 Report — Step 1 (event bus and operation index in `nctl_core`)

Date: 2026-07-17. Implements [p5/plan.md](plan.md) Step 1 — the server-independent
groundwork: an in-process event subscriber bus, a filesystem operation index, and the
`nctl ops` CLI view. This is the first suggested commit boundary; no server code exists yet,
and no existing command's behavior, schema, or event vocabulary changed.

## What was built

### In-process event subscriber bus (`nctl_core/events.py`)

`subscribe(callback, max_pending=1024) -> unsubscribe` registers a process-wide subscriber;
`OperationLog._write` publishes each record to the bus **after** a successful file append
(a record that failed to reach the file is never published, keeping the file strictly
authoritative). The delivery contract mirrors the existing "never crash the command" rule:

- each subscriber gets its own worker thread and bounded FIFO queue, so `emit` never blocks
  on a slow consumer;
- when a subscriber's queue is full, the **oldest** pending record is dropped, with a
  one-time stderr warning and a per-subscriber drop counter — correctness comes from JSONL
  replay by `seq`, not from the bus (plan Decision 6: the bus is a latency optimization,
  not a second log);
- a raising callback is warned about once on stderr and muted; the exception never
  propagates into `emit` or affects other subscribers;
- `unsubscribe()` is idempotent, stops the worker, and removes the entry from the
  process-wide registry.

### Operation index (`nctl_core/operations_index.py`)

Pure filesystem reads over `[events].log_dir` — no Nautobot, no Ansible, no writes:

- `list_operations(log_dir, limit=None)` enumerates `<id>.jsonl` files **and** bare
  `<id>/` artifact directories (an operation whose log write failed still shows up, as
  `state="no_events"`), newest first via ULID ordering;
- `load_operation(log_dir, id)` builds a typed `OperationRecord`: op name and `started_at`
  from the first record; `state` (`running` / `finished` / `no_events`), `ok`, `result`
  (the `finished` record's message — for reconcile this is the Phase 4 terminal-state
  vocabulary, e.g. `converged` / `non_converged`), `updated_at`, and `last_seq` from the
  last record; plus the artifact file list (relative POSIX names + sizes) from the
  operation directory;
- `read_events(log_dir, id, after_seq=-1)` parses the JSONL with the `after_seq` cursor
  semantics the Step 4 WebSocket replay will reuse, returning `(records, corrupt_count)`;
- corrupted or truncated JSONL lines are counted and skipped, never fatal — a crash
  mid-write must not make history unreadable;
- operation IDs are validated against the ULID alphabet (`OperationIndexError`) before any
  path is formed, so a malformed ID can never traverse outside the log directory — the
  same check the Step 2 HTTP endpoints will sit on.

### `nctl ops` CLI (`nctl_core/ops_render.py`, `cli/main.py`)

Thin CLI view making the index testable and useful before the server exists:

- `nctl ops list [--limit N] [--json]` → `nctl.ops.list.v1`;
- `nctl ops show <id> [--after-seq N] [--json]` → `nctl.ops.show.v1` (record + artifact
  list + event tail); unknown/malformed IDs return the usual `EnvelopeError` codes
  (`unknown_operation` / `malformed_operation_id`) and exit code 2.

Deliberate deviation from the "everything emits events" habit: `ops` commands are snapshot
reads in the plan's Decision 3 sense and do **not** create an `OperationLog` — inspecting
history must not grow the history being inspected.

### Documentation

`docs/event-log.md` gained a short "In-process subscriber bus (Phase 5)" section stating
the delivery/isolation contract and that lossless consumption means file replay by `seq`.

## Verification

- Full suite: **447 passed** (was 415; 32 new tests across `test_events_bus.py`,
  `test_operations_index.py`, `test_cli_ops.py`), `uv run pytest -q`, 3.4s.
- New test coverage, per the plan's Step 1 list:
  - bus: delivery order matches file content exactly; raising subscriber muted with a
    single warning while the file still gets every record; a stuck subscriber with
    `max_pending=2` never blocks `emit` and drops oldest (received `[0, 5, 6]` of 7);
    fan-out to multiple subscribers; unsubscribe idempotency; failed file write → no
    publish;
  - index: finished/running/no-events states; Phase 4-shaped fixture (plan.json +
    `round-00/` drifts + `actuation_completed`/`observation_completed`/`drift_resolved`
    events) indexed correctly; 3 corrupt lines (garbage, wrong shape, truncated tail)
    counted and skipped around 3 valid records; `after_seq` cursor; malformed-ID
    rejection incl. `../escape`; newest-first ordering and `--limit`;
  - CLI: text/JSON output, exit codes 0/2, `--after-seq` pass-through.
- Smoke test against the real Phase 4 history (`~/.local/state/nctl/events`, 54 entries):
  `nctl ops list --limit 3` correctly showed the three newest reconcile runs with states
  `failed` / `already_converged` / `non_converged`, and `nctl ops show <id> --json`
  returned the full record and events for a real operation.

## Notes for later steps

- `result.json` does not actually exist in today's reconcile artifact set (the plan's
  current-state section over-promises it slightly): Phase 4 writes `plan.json`,
  `round-NN/drift-before.json`, `round-NN/drift-final.json`, `jobs/*.json`, etc. The index
  therefore lists whatever files exist rather than expecting fixed names. The terminal
  envelope will need to be persisted (or rebuilt) server-side in Step 3 for
  `GET /operations/{id}` to return it after the fact — worth writing a `result.json` from
  the runner at that point.
- Real operation directories also contain `probe-config/` and `slurp/` entries; the Step 2
  artifact-serving allowlist must exclude those (the index itself may list them — it is
  local-only; the HTTP layer does the filtering).
- The bus registry is process-wide state; tests clean up via `unsubscribe()` in
  `try/finally`. The Step 3 runner should follow the same discipline.

## Commits

- nctl: `p5s1` — event subscriber bus, operations index, `ops` CLI, tests, event-log doc.
- parent: this report + nctl submodule pointer.
