# Final report: detailed actual-state export (`nctl actual --detail`)

Status: **complete** (2026-08-06). Step reports: [report1.md](report1.md)
(feature + tests), [report2.md](report2.md) (policy rewording),
[report3.md](report3.md) (bundle composition), [report4.md](report4.md)
(verification evidence).

## Schema choice

`nctl.actual.v1` → **`nctl.actual.v2`**: the envelope data gains an
always-present `devices` section (identity + allowlisted `ActualFacts`; with
`--detail` also `facts_raw` = the nodeutils facts dict from
`inventory_raw_json.facts`, passed through unchanged) and a `detail_level`
field (`"basic"`/`"raw"`). Clean bump, no dual schema (breaking-change
phase). Optional positional `HOST` scopes the devices section; an unknown
host is a named `unknown_host` error with exit 1. The bundle schema stays
`nctl.bundle.v1`; `actual_detail.json` is an optional self-described fifth
payload file.

## Files touched

- `nctl/src/nctl_core/actual_render.py` — devices section, detail/host
  parameters, schema bump, text summary lines.
- `nctl/src/nctl_core/cli/main.py` — `HOST` argument and `--detail` option
  on `actual` (raw facts are JSON-only; `--help` says so).
- `nctl/src/nctl_core/sources/actual.py` — comment/docstring rewording only
  (strict Proxmox models untouched).
- `nauto/README.md` — "never reads `inventory_raw_json`" demoted to the
  recommended-practice stance.
- `nctl/docs/state-bundle.md` — optional `actual_detail.json`, size caveat,
  v2 annotation.
- `nctl/tests/test_actual_render.py`, `nctl/tests/test_cli_actual.py` — new
  and updated cases (passthrough, non-detail purity, HOST scoping,
  unknown host, never-ingested device, CLI wiring).

## Gate output

`cd nctl && uv run pytest -q --durations=20` → **1255 passed**, 0 failed,
0 skipped. Live read-only check against the local scratch Nautobot confirmed
a real device's GPU (Quadro RTX 8000, 48 GB), memory (123.41 GB), and Docker
container facts arrive in `facts_raw` (excerpt in report4.md).

## Acceptance

A consumer can now obtain per-node detail beyond the basic facts via
`nctl actual --detail`, and a state bundle can carry it.
