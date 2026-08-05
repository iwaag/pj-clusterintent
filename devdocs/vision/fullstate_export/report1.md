# Report — Step 1: `nctl actual --detail` with a devices section

Status: complete (2026-08-06)

## What was built

`nctl actual` now renders a `devices` section in addition to the existing
observer → Proxmox Cluster → guest graph:

- Every run (with or without `--detail`) includes one entry per realized
  Device: identity (`id`, `name`, `serial`, `platform`) plus the existing
  allowlisted `ActualFacts`. This was chosen (the plan's "implementer's
  choice") because plain Devices were previously absent from the output
  entirely and the identity/basic-facts view is useful on its own.
- `--detail` additionally populates `facts_raw` per device: the nodeutils
  `facts` dict passed through unchanged from
  `_custom_field_data["inventory_raw_json"]["facts"]`. `facts_raw` is `null`
  when the device has no raw inventory (never ingested), and always absent
  from the data when `--detail` is not given.
- Optional positional `HOST` argument scopes the `devices` section to one
  device by name. The cluster graph is deliberately not filtered (allowed by
  the plan). An unknown host produces an empty `devices` list **plus** a named
  `unknown_host` envelope error, so `ok` is `false` and the exit code is 1 —
  the deliberate choice between the plan's two permitted behaviors.
- A `detail_level` field (`"basic"` | `"raw"`) is included in the envelope
  data for consumers.

## Schema choice

Bumped `ACTUAL_SCHEMA` from `nctl.actual.v1` to **`nctl.actual.v2`**. The
always-present `devices` section and `detail_level` field change the document
shape for every consumer, and the project is in a coordinated breaking-change
phase, so a clean bump with no dual schema was preferred over an "additive v1"
claim. All tests pinning the schema string were updated; the
`state-bundle.md` reference is updated in Step 3.

## Text rendering

Non-`--json` mode prints one short summary line per device
(`device NAME  system=…  ip=…  collected …`) and, under `--detail`, a note
that raw facts are only in `--json` output. Raw facts are never dumped as
text. `--help` for `--detail` states that it should be combined with `--json`.

## Files touched

- `nctl/src/nctl_core/actual_render.py` — schema bump, `ActualDeviceData`
  model, `devices`/`detail_level` in `ActualData`, `detail`/`host` parameters
  on `build_actual`/`render_actual_data`, `_raw_facts` passthrough helper,
  `unknown_host` error, device summary lines in `render_actual_text`.
- `nctl/src/nctl_core/cli/main.py` — `HOST` positional argument and
  `--detail` option on the `actual` command; option help updated to v2.
- `nctl/tests/test_actual_render.py` — fixture device with a raw
  `inventory_raw_json` payload (GPU / memory / containers / extra key);
  new cases listed below.
- `nctl/tests/test_cli_actual.py` — canned envelopes updated to v2 with a
  devices section; CLI passthrough test for `HOST`/`--detail`.

## Test evidence (nctl ordinary gate)

`cd nctl && uv run pytest -q --durations=20` → **1255 passed** (0 failed,
0 skipped). New cases mapping to the plan's required proofs:

- passthrough: `test_render_actual_data_detail_passes_raw_nodeutils_facts_through_unmodified`
  asserts `facts_raw` equals the fixture's GPU/memory/container dict exactly.
- non-detail purity: `test_render_actual_data_without_detail_has_devices_but_no_raw_facts`
  and `test_actual_json_output_never_contains_raw_or_unrelated_data` assert
  raw content is absent without `--detail`.
- never-ingested device: `test_render_actual_data_detail_yields_null_raw_facts_when_never_ingested`.
- HOST scoping: `test_render_actual_data_host_scopes_devices_section_only`;
  unknown host: `test_render_actual_data_unknown_host_yields_empty_devices`
  and `test_build_actual_unknown_host_reports_named_error`.
- CLI wiring: `test_actual_cli_passes_detail_and_host_through`.

No collection, ingest, or Nautobot model change was made (plan non-goal).
