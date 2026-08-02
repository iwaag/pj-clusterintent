# Step 1 — Widen `inventory_raw_json`

## Change

`nauto/jobs/ingest_nodeutils_inventory.py` `build_custom_fields`:
`inventory_raw_json["facts"]` now stores the full `report["facts"]`
dict as-is instead of cherry-picking
`hardware/gpu/disk/network/software/services/workspaces`. This adds
the previously-dropped `cpu`, `memory`, `os_name`, `os_version`,
`kernel_version`, `architecture`, `system` keys. `identity` unchanged.

Before:
```python
"inventory_raw_json": {
    "identity": identity,
    "facts": {
        "hardware": facts.get("hardware"),
        "gpu": gpu,
        "disk": disk,
        "network": network,
        "software": facts.get("software"),
        "services": services,
        "workspaces": workspaces,
    },
},
```

After:
```python
"inventory_raw_json": {
    "identity": identity,
    "facts": facts,
},
```

## Test fix

`tests/test_ingest_nodeutils_inventory_job.py::BuildCustomFieldsWorkspaceTest::test_observed_workspaces_absent_when_no_hints_configured`
asserted `inventory_raw_json["facts"]["workspaces"] == {}` when the
report had no `workspaces` key. That relied on the old code's forced
default; raw pass-through now omits the key entirely when absent.
Changed assertion to `assertNotIn("workspaces", ...)`.

## Verification

- Confirmed no other test in `tests/` inspects
  `inventory_raw_json`'s shape.
- Confirmed `nctl`/`nintent` never read `inventory_raw_json` (only
  mentioned in `nctl_core/sources/actual.py` comments explaining why
  it's excluded) — this change has no cross-component impact.
- `python3 -m unittest discover -s tests` (run from `nauto/`): **112
  passed**, 0 failures, 0 errors.

## Not yet live

This is a code-only change. No live ingest run performed yet — deferred
to Step 3's re-run, per plan ordering (raw data widened before any
column deletion).
