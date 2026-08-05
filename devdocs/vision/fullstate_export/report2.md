# Report — Step 2: reword the "nctl never reads `inventory_raw_json`" policy

Status: complete (2026-08-06)

The strict rule is demoted to a recommendation, per the owner decision recorded
in [plan.md](plan.md): deterministic processing (drift, planning) keeps reading
only the allowlisted columns; display/export paths (now concretely
`nctl actual --detail`) may pass the raw store through.

## Changes

- `nauto/README.md` (allowlist rationale paragraph, ~line 77–84): replaced
  "since `nctl` never reads `inventory_raw_json` (documented policy)" with the
  new stance — deterministic processing reads only the allowlisted columns
  (recommended practice); display/export paths such as `nctl actual --detail`
  may pass `inventory_raw_json.facts` through as-is.
- `nctl/src/nctl_core/sources/actual.py`:
  - `ACTUAL_FACT_FIELDS` allowlist comment: scoped to deterministic
    processing, with a note that display/export paths may pass the raw store
    through separately.
  - `read_actual_facts` docstring: "can never leak into the exported facts"
    reworded to a boundary on that function, not the whole CLI.
  - Proxmox typed-models block comment (~line 183) and the `proxmox_*`
    allowlist comment (~line 388): "never read here" / "never inspected"
    scoped to the Proxmox readers themselves, noting the separate
    display/export passthrough. The strict `extra="forbid"` Proxmox models
    are unchanged, as the plan requires — their validation is unrelated to
    this policy.

## Not changed

- Historical reports under `devdocs/small/minimize_nauto/` — left untouched
  as history (plan instruction).
- Unrelated "never read" wording in `drift/evaluation_snapshot.py` and
  `drift/comparators.py` (different rules, not about `inventory_raw_json`).

Comment/doc-only changes plus the Step 1 code; the nctl gate is re-run in
Step 4 (already green after Step 1: 1255 passed).
