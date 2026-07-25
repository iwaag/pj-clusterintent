# Phase 3 Report — Step 2 (`[dashboard]` config and `nctl dashboard` CLI)

Date: 2026-07-16. Implements [p3/plan.md](plan.md) Step 2. nctl commit: `p3s2`.

## What was built

- **Config**: new optional `[dashboard]` section (strict model, like the rest of `nctl.toml`):
  `out_dir` (default `~/.local/state/nctl/dashboard`) and `url` (optional, informational only —
  where the out dir is served on the LAN; nctl never fetches it). `example.nctl.toml` updated.
- **`nctl_core/dashboard_render.py`** — `build_dashboard(cfg, *, out_dir, from_file, push)`:
  - default path runs the same `build_drift` as `nctl drift` (full cluster, no filters — a
    partial dashboard would misreport cluster health), renders the Step 1 page, and atomically
    replaces `index.html` + `drift.json` (staged `.tmp` → `Path.replace`) in the out dir;
    `drift.json` is the exact `nctl.drift.v1` envelope, so the directory serves humans and AI
    from the same generation;
  - `--from FILE` renders a saved envelope instead (schema field validated:
    `drift_payload_unreadable` / `drift_payload_schema_mismatch` / `drift_payload_invalid`),
    touching no network on the drift side;
  - a **failed** drift run still writes the artifacts (the page shows the errors — Step 1's
    failed-run rendering) and the dashboard envelope carries the drift errors, so `ok` and the
    exit code follow the drift run and the file write, per the plan;
  - envelope `nctl.dashboard.v1`: `html_path`, `drift_json_path`, `generated_at`, `summary`,
    `severity_summary`, `status_push` (Step 3's aggregate; placeholder zeros in this commit),
    `dashboard_url`.
- **CLI**: `nctl dashboard [--out DIR] [--from FILE] [--no-push] [--json]`, a thin Typer
  wrapper like every other command. Decision 2 holds: `nctl drift` is untouched and remains
  side-effect free; this command is the regeneration entry point.

## Tests

`tests/test_dashboard_render.py` (9) + `tests/test_cli_dashboard.py` (4): artifact writing to
the configured/overridden out dir (including no leftover `.tmp` staging files and `drift.json`
byte-equivalence to the envelope), `--from` happy path plus all three rejection codes,
failed-drift-still-writes behavior, text rendering, config defaults (tilde expansion), CLI
text/JSON/option-passthrough/exit-code.

Full nctl suite after the step: **254 passed**.
