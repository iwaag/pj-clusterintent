# Phase 0 Report — Steps 0.1–0.2 (scaffolding + config)

Date: 2026-07-14. Covers commit unit 1 from [plan.md](plan.md): project scaffolding, the
configuration layer, and a `nctl status` stub that only resolves config.

## What was built

Inside the `nctl` submodule (previously LICENSE-only):

- `pyproject.toml` — uv-managed, Python >= 3.11, hatchling build. Runtime deps: `typer`,
  `httpx`, `pydantic` v2 (httpx/pydantic are unused until Step 0.3/0.4 but pinned now so the
  dependency set is settled). Dev group: `pytest`, `respx`. Entry point `nctl` →
  `nctl_core.cli.main:app`.
- `src/nctl_core/config.py` — the Step 0.2 config layer:
  - Resolution order as planned: `--config` → `$NCTL_CONFIG` → `./nctl.toml` → parent-repo
    root (found by walking up to the nearest `.gitmodules` mentioning `nctl`).
  - Pydantic-validated sections `[nautobot]` / `[inventory]` / `[events]` / `[repo]` with
    `extra="forbid"` on every model — an inline `token =` key is rejected by validation, so
    credentials can only come from `token_env` (default `NAUTOBOT_TOKEN`) or `token_file`.
  - `NautobotConfig.resolve_token()` implements the token_file-then-env lookup.
  - Distinct error types: `ConfigNotFoundError` vs `ConfigInvalidError` (parse vs schema
    errors both map to the latter), for clean mapping onto exit codes.
  - Relative `repo.root` resolves against the config file's own directory (`source_path`).
- `src/nctl_core/cli/main.py` — Typer app. Per the plan's convention the command only parses
  args, calls `Config.load`, and renders; config errors print to stderr and exit with code 2.
  A no-op `@app.callback()` keeps the `status` subcommand name explicit while it is the only
  command. `status` currently prints the resolved config and a "checks not implemented"
  placeholder — the real checks are Steps 0.3–0.6.
- `example.nctl.toml`, `README.md` (layout, setup, conventions summary), `.gitignore`.
- `tests/test_config.py` — 11 tests: all four resolution-order precedence cases, not-found,
  valid load, inline-token rejection, malformed TOML, missing section, and token resolution
  from env and file. All pass (`uv run pytest`).

Outside the submodule:

- Parent `.gitignore` now ignores `/nctl.toml`; a working copy was created at the repo root
  from `example.nctl.toml`.

## Verification

- `uv run pytest` — 11 passed.
- `uv run nctl status` from inside `nctl/` — resolves the root `nctl.toml` via the repo-root
  fallback and prints config summary, exit 0.
- `uv run nctl status --config /nonexistent.toml` — stderr error, exit 2.
- Run from an unrelated cwd — clear "no nctl.toml found (searched …)" error listing the
  search locations.

## Deviations from plan

- None in behavior. One addition: `Config.source_path` (where the config was loaded from) is
  kept on the model so relative paths and error messages stay anchored; the plan didn't
  specify this.
- `docs/output-format.md` and `docs/event-log.md` are intentionally absent — they belong to
  commit unit 2 (Steps 0.4–0.5).

## Next

Commit unit 2: output envelope (`output.py`) + event log (`events.py`) with their docs,
then wire the `status` stub to emit a real `nctl.status.v1` envelope skeleton.
