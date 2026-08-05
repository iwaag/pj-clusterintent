# Plan: detailed actual-state export (`nctl actual --detail`)

Goal (from [braindump.txt](braindump.txt)): beyond the basic desired/actual
views the state bundle already exports, provide *some* way to obtain richer
per-node detail — GPU, memory, running containers, and everything else
nodeutils collects — for consumers such as pj-agdev. Light-weight is fine;
existence of the mechanism is the point.

## Design decisions already made (conversation, 2026-08-05)

- The detail data **already lives in Nautobot**: nauto's ingest stores the full
  nodeutils `facts` dict as-is in the `inventory_raw_json` Device custom field
  ([nauto/README.md](../../../nauto/README.md), lines 61–83). No collection or
  ingest change is needed. This is a reader-side feature only.
- The documented rule "nctl never reads `inventory_raw_json`" is **demoted to a
  recommendation**: deterministic processing (drift, planning) keeps reading
  only the allowlisted columns; display/export paths may pass the raw facts
  through. Owner's decision — do not re-litigate.
- Secrets handling is **out of scope**: nodeutils facts contain no credentials
  and current Nautobot data holds none. Do not build an allowlist/redaction
  layer for this feature.
- Backward compatibility is **not required** (project-wide breaking-change
  phase). No dual readers, aliases, or compat envelopes.
- Fine-grained field filtering is deliberately deferred; the only volume
  controls are the detail switch itself and optional host scoping.

## Useful facts discovered while planning

- `fetch_actual_snapshot` already fetches `_custom_field_data` wholesale and
  stores it in `ActualDevice.facts`
  ([sources/actual.py:537-545](../../../nctl/src/nctl_core/sources/actual.py)),
  so `inventory_raw_json` is already in memory after every fetch. The
  "never read" boundary is enforced only at consumption time
  (`read_actual_facts` allowlist, comments at lines 87–101, 127–129, 183–186,
  384–386). No GraphQL query change is needed.
- The current `nctl.actual.v1` output renders **only** the Proxmox
  observer→cluster→guest graph
  ([actual_render.py](../../../nctl/src/nctl_core/actual_render.py));
  plain Devices and their facts are absent from the output entirely. So this
  feature adds a `devices` section, not just extra fields on existing rows.
- The raw dict is at `facts["inventory_raw_json"]["facts"]` per Device (nauto
  stores the nodeutils `facts` dict under that key, nothing cherry-picked).
- CLI wiring: `actual` command at
  [cli/main.py:240-254](../../../nctl/src/nctl_core/cli/main.py); envelope
  helpers in `output.py`; the `build_*`/`render_*_data` split in
  `actual_render.py` is the house pattern — keep it so fixture-snapshot tests
  stay cheap.
- Test gate: `cd nctl && uv run pytest -q --durations=20`. Existing tests to
  imitate: `nctl/tests/test_cli_actual.py`, `nctl/tests/test_sources_actual.py`.

## Steps

### Step 1 — `nctl actual --detail` with a devices section

Add to `nctl actual`:

- `--detail`: include a `devices` list in the envelope data. Each entry:
  device identity (id, name, serial, platform), the existing allowlisted
  `ActualFacts`, and `facts_raw` = the `inventory_raw_json.facts` dict passed
  through unchanged (absent/null when the device has no raw inventory).
- Optional positional `HOST` argument to scope output to one device by name —
  the volume control for large clusters. Applying it to the existing cluster
  graph too is fine but not required.
- Also include the `devices` section (identity + allowlisted facts, no
  `facts_raw`) without `--detail` if that feels more coherent — implementer's
  choice; the required behavior is only that `--detail` yields the raw facts.

Envelope/schema: no compatibility constraint. Either extend `nctl.actual.v1`
additively or bump to `nctl.actual.v2` — pick one, update the schema constant
and any tests that pin it, and state the choice in the report. A
`detail_level` field in the data or header is a nice-to-have for consumers.

Text (non-`--json`) rendering: a short per-device summary line is enough;
dumping raw facts as text is not useful. Requiring `--json` for `--detail` is
also acceptable — say so in `--help` if you do.

Tests (nctl ordinary gate): a fixture snapshot with `inventory_raw_json`
present proves passthrough (GPU/memory/container keys arrive unmodified);
one case proves the non-detail output stays free of `facts_raw`; one case
covers HOST scoping and unknown-host behavior (empty result with a named
error or empty list — either, but deliberate).

### Step 2 — reword the "never reads" policy

Update the two places that state the strict rule:

- [nauto/README.md](../../../nauto/README.md) line ~82: replace "since `nctl`
  never reads `inventory_raw_json` (documented policy)" with the new stance:
  deterministic processing reads only allowlisted columns (recommended);
  display/export paths may read the raw store.
- Comments in `sources/actual.py` (module docstring context and lines ~183,
  ~384) and the `read_actual_facts` docstring: same rewording where they claim
  the raw blob "can never leak" / "is never read". Keep the Proxmox strict
  models exactly as they are — their `extra="forbid"` validation is unrelated
  to this policy and stays.

Historical reports under `devdocs/small/minimize_nauto/` are history — leave
them untouched.

### Step 3 — bundle composition: optional `actual_detail.json`

Extend [nctl/docs/state-bundle.md](../../../nctl/docs/state-bundle.md): an
optional fifth payload file `actual_detail.json` produced by
`nctl actual --json --detail`, listed in `manifest.json` `contents` like the
others (its `schema` from its own envelope header). The manifest is already
per-file self-describing, so `nctl.bundle.v1` stays; a bundle without the
detail file remains valid. Note the size caveat: composers may prefer host-
scoped detail files on large clusters.

### Step 4 — verification and report

- `cd nctl && uv run pytest -q --durations=20` green.
- If the local Nautobot scratch stack (`.local/localenv_memo.md`) is up, run
  `nctl actual --json --detail` against it once and confirm a real device's
  GPU/memory/container facts appear; paste a trimmed excerpt into the report.
  If the stack is down, say so — fixture tests carry the proof (this is a
  read-only command; there is no live mutation to verify).
- Write `report.md` in this directory: schema choice made, files touched,
  gate output, and the acceptance statement — "a consumer can now obtain
  per-node detail beyond the basic facts via `nctl actual --detail`, and a
  state bundle can carry it."

## Non-goals

- No new collection, ingest, or Nautobot model changes.
- No field-level filtering options, no redaction layer, no pagination.
- No `nctl bundle` command; bundling stays a documented composition.
- No pj-agdev-side work (its interactive-query direction is tracked in
  `pj-agdev/devdocs/todo_done.md`).
