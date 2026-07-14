# Phase 0 Implementation Plan: Scaffolding

Parent: [roadmap.md](../roadmap.md) — Phase 0: establish the skeleton of `nctl` and the design conventions.

## Current state (as of 2026-07-14)

- The `nctl` submodule exists at the repo root but contains only a LICENSE file. Everything is built from scratch.
- Desired state lives in Nautobot via the `nintent` plugin (`nautobot_intent_catalog`), which exposes REST endpoints (`/api/plugins/intent-catalog/nodes`, `/endpoints`). Nautobot itself provides the generic GraphQL endpoint (`/api/graphql/`).
- Actual state is dumped by `nodeutils collect` as JSON with `schema_version: nodeutils.inventory.v1` (top-level keys: `collector`, `identity`, `collected_at`, `facts`, `self_reported`).
- Local dev Nautobot: `http://localhost:8000/`, token available (see `.local/localenv_memo.md`; never commit it).

## Deliverables

1. `nctl/` uv-managed Python project: `nctl_core` library + thin CLI entry point.
2. Shared layers: config (`nctl.toml`), Nautobot client, nodeutils dump reader.
3. Documented common JSON output envelope and JSON Lines event log format.
4. `nctl status [--json]` as the reference implementation of all conventions.
5. Unit tests + docs.

## Step 0.1 — Project scaffolding

Layout inside the `nctl` submodule:

```
nctl/
  pyproject.toml          # uv-managed; [project.scripts] nctl = "nctl_core.cli.main:app"
  README.md               # usage + conventions summary (envelope, events, config)
  docs/
    output-format.md      # JSON envelope spec (Step 0.4)
    event-log.md          # JSON Lines event spec (Step 0.5)
  example.nctl.toml
  src/nctl_core/
    __init__.py
    config.py             # Step 0.2
    nautobot.py           # Step 0.3
    dumps.py              # Step 0.3
    output.py             # Step 0.4 (envelope models + renderers)
    events.py             # Step 0.5 (operation ID + JSONL emitter)
    status.py             # Step 0.6 (pure library logic for `status`)
    cli/
      __init__.py
      main.py             # Typer app; commands are thin wrappers only
  tests/
```

Decisions:

- Python >= 3.11 (matches other submodules; `tomllib` in stdlib).
- Dependencies: `typer` (CLI), `httpx` (HTTP), `pydantic` v2 (schemas/validation). Dev: `pytest`, `respx` (httpx mocking).
- Convention (enforced by review, stated in README): CLI functions contain no business logic — they parse args, call `nctl_core`, and render. Every core function returns pydantic models, never prints.

## Step 0.2 — Configuration layer (`config.py`)

- File: `nctl.toml`, resolved in order: `--config PATH` → `$NCTL_CONFIG` → `./nctl.toml` → pj-clusterintent repo root (walk up from cwd looking for `.gitmodules` containing `nctl`).
- Schema (pydantic-validated):

```toml
[nautobot]
url = "http://localhost:8000"
# token is never stored inline; one of:
token_env = "NAUTOBOT_TOKEN"        # default
# token_file = "~/.config/nctl/nautobot_token"

[inventory]
dumps_dir = "/var/lib/nodeutils"    # where nodeutils inventory.json files land
                                    # (dir of per-host files or a single file)

[events]
log_dir = "~/.local/state/nctl/events"

[repo]
root = "."                          # pj-clusterintent checkout, for submodule checks
```

- Provide `Config.load(path: Path | None) -> Config` plus clear errors (missing file vs. invalid field) surfaced through the standard error shape (Step 0.4).
- Ship `example.nctl.toml`; git-ignore `nctl.toml` at the parent-repo root.

## Step 0.3 — Nautobot client and dump reader

`nautobot.py`:

- `NautobotClient(url, token)` wrapping httpx with the `Authorization: Token …` header and sane timeouts.
- `graphql(query, variables) -> dict` against `/api/graphql/`, raising a typed `NautobotError` (connection / auth / GraphQL-errors) — this is the primary interface Phase 1–2 will build on.
- `ping() -> NautobotInfo` — GET `/api/` (version, authenticated) and a probe of `/api/plugins/intent-catalog/nodes/?limit=1` to confirm the nintent plugin is installed. Used by `status`. (In Phase 0-EX1 this REST probe is replaced by a GraphQL schema introspection check once nintent registers its GraphQL types — see roadmap.)
- No caching, no retries in Phase 0.

`dumps.py`:

- `load_dump(path) -> NodeDump` — parse a nodeutils report, hard-require `schema_version == "nodeutils.inventory.v1"` (fail loudly on mismatch; breaking-change phase, no compat shims).
- `scan_dumps(dumps_dir) -> list[NodeDump]` — discover `*.json`/`*.yaml` reports; each carries `identity.hostname` and `collected_at` for freshness reporting.
- Model only what Phase 0 needs (`schema_version`, `collector`, `identity`, `collected_at`); keep `facts`/`self_reported` as raw dicts for now — Phase 2 owns their typing.

## Step 0.4 — Common JSON output format (`output.py`)

Envelope for every command's `--json` output (documented in `docs/output-format.md`):

```json
{
  "schema": "nctl.status.v1",
  "generated_at": "2026-07-14T12:00:00+00:00",
  "ok": true,
  "data": { },
  "errors": [ {"code": "nautobot_unreachable", "message": "…", "detail": {}} ]
}
```

Rules:

- `schema` is `nctl.<command>.v1`; bump the suffix on breaking change (free to do so pre-freeze, but always explicit).
- `ok` is the machine verdict; exit code mirrors it (0 ok / 1 command-level failure / 2 usage-or-config error).
- Human-readable output is always a rendering of the same `data` — implement `render_text(envelope)` per command; never compute text from separate state.
- `--json` prints the envelope to stdout as a single JSON document; diagnostics go to stderr only.

Implementation: generic `Envelope[T]` pydantic model + a small helper that a CLI command calls once (`emit(envelope, json_mode)`).

## Step 0.5 — Event log format (`events.py`)

JSON Lines, one file per operation: `<log_dir>/<operation_id>.jsonl` (documented in `docs/event-log.md`):

```json
{"ts": "2026-07-14T12:00:00.123+00:00", "operation_id": "01J...", "op": "status", "seq": 0, "event": "started", "level": "info", "message": "…", "data": {}}
```

- `operation_id`: ULID (sortable, unique); also included in the command's JSON envelope (`data.operation_id`) so logs and output cross-reference.
- Core event vocabulary (extensible per-op via `data`): `started`, `step_started`, `step_completed`, `warning`, `failed`, `finished`. `drift_resolved` etc. are added by later phases within the same envelope shape.
- API: `op = OperationLog.start("status", log_dir)` … `op.emit(event, message, **data)` … `op.finish(ok=…)`. Failure to write events must not crash a command (warn on stderr).
- `nctl status` uses it even though it's short-running — the point is to exercise the convention end to end.

## Step 0.6 — `nctl status` (reference command)

`data` payload of `nctl.status.v1`:

```json
{
  "operation_id": "01J...",
  "nautobot": {"reachable": true, "url": "…", "version": "2.x", "authenticated": true, "intent_catalog": true},
  "dumps": {"dir": "…", "hosts": [{"hostname": "agpc", "collected_at": "…", "age_hours": 12.5}], "errors": []},
  "submodules": [{"name": "nintent", "commit": "…", "state": "clean|modified|uninitialized"}]
}
```

- Submodule state: run `git submodule status` in `repo.root` and parse the prefix (`-` uninitialized, `+` out-of-sync, `U` conflict) plus `git status --porcelain` per submodule for dirtiness.
- Each of the three checks degrades independently: an unreachable Nautobot still yields dump + submodule info, with `ok: false` and an entry in `errors`.
- Text rendering: one section per check with ✓/✗ markers.

## Step 0.7 — Tests and docs

- Unit tests: config resolution order; dump parsing (valid, wrong `schema_version`, malformed); Nautobot client against `respx` mocks (ok / 401 / connection refused); envelope schema snapshot for `status --json` (golden file — this is the "stable schema" guard from the exit criteria); event emitter writes valid JSONL with monotonic `seq`.
- CI-less for now; `uv run pytest` documented in README.
- Update parent `README.md` only if command names change from what it already states (it already describes `nctl` correctly).

## Out of scope for Phase 0

- dnsmasq rendering/apply (Phase 1), drift computation (Phase 2), any HTML/serve output (Phases 3/5).
- Retries, caching, auth beyond the token, Windows support.
- Typing `facts` / `self_reported` from nodeutils dumps.

## Exit criteria (from roadmap, made checkable)

- [ ] `uv run nctl status` and `uv run nctl status --json` work against the local dev Nautobot.
- [ ] `status --json` matches the `nctl.status.v1` golden schema in tests.
- [ ] Envelope and event log formats are documented in `nctl/docs/` and `status` emits a real event log file.
- [ ] All three checks (Nautobot, dumps, submodules) degrade independently with correct `ok`/exit codes.

## Suggested commit order

1. Scaffolding + config (Steps 0.1–0.2) — `nctl status` stub that only loads config.
2. Output envelope + events (Steps 0.4–0.5) with docs.
3. Nautobot client + dump reader (Step 0.3).
4. Full `status` + tests (Steps 0.6–0.7).
