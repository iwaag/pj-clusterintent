# Phase 0 Step 3 — Capture the current nctl surface and retained evidence behavior

Parent: [plan.md](plan.md), Step 3.

All commands were `--help` invocations, Python model introspection (`.model_fields.keys()`),
config loading, and directory listings — no operation, dashboard, or serve run. Full `--help`
transcript saved to the private evidence file `nctl-command-help.txt`.

## Top-level command names

```text
status actual drift dashboard reconcile lifecycle serve render apply ops braindump ssh session
```

Matches plan §2.1's planning-time snapshot exactly; still includes `dashboard` and `serve`.

## `dashboard`/`serve` options and schemas

- `nctl dashboard`: `--config`, `--out`, `--from`, `--no-push`, `--json` (envelope `nctl.dashboard.v1`).
- `nctl serve`: `--config`, `--host`, `--port`, `--json` (envelope `nctl.serve.v1`).

## Current config sections (`nctl/example.nctl.toml`)

```text
[nautobot] [inventory] [events] [ansible] [repo] [reconcile] [dashboard] [ssh] [serve]
```

Nine sections; `[dashboard]` and `[serve]` are the two Section 4.1 requires gone, plus their keys
(`dashboard.out_dir`/`.url`, `serve.*` — full contents were not needed beyond section names for
this step).

## Optional/development server dependencies (`nctl/pyproject.toml`)

```toml
[project.optional-dependencies]
serve = ["fastapi>=0.115", "uvicorn[standard]>=0.34"]

[dependency-groups]
dev = ["fastapi>=0.115", "pytest>=8.0", "respx>=0.21", "uvicorn[standard]>=0.34"]
```

`serve` is a distinct installable extra; `fastapi`/`uvicorn` are also currently pinned in the
unconditional `dev` group (relevant for Phase 1/4 dependency cleanup — a plain install has no
`serve` extra, but `dev` currently still pulls both packages for the test suite).

## Current model fields

```text
ReconcileData:  operation_id, mode, scope, state, event_log_path, artifact_dir, plan_path,
                initial_drift_path, final_drift_path, rounds, manual_review, unsupported,
                summary, scope_summary, dashboard, progress_made, ssh_preflight
RoundSummary:   round, drift_fingerprint, actions, ssh_preflight
EventRecord:    ts, operation_id, op, seq, event, level, message, data
OperationRecord: operation_id, op, state, ok, result, started_at, updated_at, last_seq,
                 event_count, corrupt_lines, log_path, artifact_dir, artifacts
```

Comparing field-for-field against plan §4.3/§4.4/§4.5: `ReconcileData` has exactly one field beyond
the frozen target set — `dashboard` — which §4.3 requires removed in place (no `v3`, no null
replacement). `RoundSummary`, `EventRecord`, and `OperationRecord` already match their frozen
target field sets exactly; no change is required to them by this initiative.

## `nctl.ops.list.v1` / `nctl.ops.show.v1`

`nctl_core/ops_render.py` defines `OPS_LIST_SCHEMA = "nctl.ops.list.v1"` and
`OPS_SHOW_SCHEMA = "nctl.ops.show.v1"`, referenced identically by `cli/main.py`'s `--json` help
text. Matches plan §4.5 exactly; no change required.

## Existing operation evidence paths (names/counts only)

`Config.load().events.log_dir` resolves to `~/.local/state/nctl/events` (outside the repo tree).
It currently contains **197** `<ULID>.jsonl` event-log files and **148** operation artifact
subdirectories — historical evidence from routine local use, preserved as `historical` per plan
§6.4. Contents were not read.

## Gate

The current surface is fully comparable field-for-field with Section 4: only `ReconcileData.dashboard`
needs removal; the `dashboard`/`serve` CLI commands, config sections, and `serve` optional
dependency are the only surface deltas versus the frozen retained contract.
