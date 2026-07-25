# Phase 1 Step 5 — Update current nctl documentation

Parent: [plan.md](plan.md), Step 5.

Private evidence directory: `.local/remove-unused-surfaces/p1/20260725-152425/`.

## Staging correction carried over from Step 3

Before starting Step 5's own edits, `git status` showed `src/nctl_core/events.py` and
`tests/test_compatibility_snapshots.py` as modified-but-uncommitted even though `report3.md`
already described and tested those exact edits. Root cause: the Step 3 commit ran
`git add -A src/nctl_core/serve src/nctl_core/events.py tests/test_compatibility_snapshots.py
tests/test_cli_serve.py ...`, and `tests/test_cli_serve.py` (already removed by an earlier
`git rm`) made that pathspec invalid, aborting the whole `git add` with no files staged for that
command; only the prior `git rm`-staged deletions made it into commit `699bc71`. The working tree
still had the correct content the whole time (report3.md's recorded test run genuinely exercised
it), so this was a commit-hygiene gap, not a code or test defect. Committed separately as a fixup
(`747b635` in `nctl`, matching root commit) before proceeding, so the tree now matches every prior
report exactly.

## Documentation edits

- `README.md`: removed the two `uv run --extra serve nctl serve` usage lines, removed `serve,`
  from the Braindump isolation sentence, rewrote the `ops list`/`ops show` paragraph to drop the
  `nctl serve` cross-reference and describe `nctl_core.operations_index` as a retained CLI-only
  helper over durable disk evidence, and deleted the entire `## Serve (realtime API)` section
  (config/auth, endpoint table, single-flight execution, WebSocket protocol/replay, reference live
  dashboard, and the compatibility-freeze pointer at its end).
- `docs/compatibility.md`: rewrote the intro paragraph (was "Phase 5 gives `nctl_core` external
  subscribers... over HTTP/WebSocket") to describe the frozen shapes as CLI/`nctl ops` disk
  evidence; dropped the `/api/v2` phrasing from the breaking-change paragraph; removed the
  `nctl.serve.v1` row from the envelope table; deleted the entire `## 4. HTTP/WS API surface
  (/api/v1)` section.
- `docs/event-log.md`: reworded the header note from "external subscribers... read this format
  over HTTP/WS" to "durable disk evidence consumed by the CLI and `nctl ops`"; deleted the
  `## In-process subscriber bus (Phase 5)` section and replaced it with one sentence stating the
  JSONL file is the sole source of truth with no subscriber bus.
- `docs/output-format.md`: reworded the header note from "external subscribers... consume these
  envelopes over HTTP" to "the CLI's `--json` output ... not ... any external HTTP subscriber."
  (No `nctl.serve.v1` entry existed in this file's own tables.)
- `docs/usage_example.md`: removed the `"Serve the live dashboard/API" | nctl serve` lookup row.

Static dashboard documentation (its own usage rows, `nctl.dashboard.v1`, and every dashboard
config/behavior description) is untouched in all five files.

## Deletion search across the five edited files

```bash
grep -n -i "nctl serve\|nctl_core\.serve\|nctl\.serve\.v1\|ServeConfig\|NCTL_SERVE_TOKEN\|/api/v1\|websocket\|fastapi\|uvicorn" \
  README.md docs/compatibility.md docs/event-log.md docs/output-format.md docs/usage_example.md
```

No matches in any of the five files.

## Verification

`uv run pytest -q`: **980 passed** — documentation-only changes, no code touched in this step
beyond the Step 3 staging fixup recorded above.

## Gate

Current nctl documentation no longer instructs a user or agent to install, run, call,
authenticate to, or subscribe to the deleted server, while all static-dashboard documentation for
Phase 2 remains intact. Proceeding to Step 6.
