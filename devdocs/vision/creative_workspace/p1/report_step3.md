# Step 3 — nauto ingest

## Changes (`nauto` `2f453f1`)

- `seed/home_cluster.yaml`: added an `observed_workspaces` JSON custom field entry for
  `dcim.device`, next to `observed_services` (weight `262`, the next free slot after `261`).
- `jobs/ingest_nodeutils_inventory.py`'s `build_custom_fields`:
  - reads `facts.get("workspaces")` (matching where the nodeutils Step 1 collector promoted it —
    sibling to `facts.services`, not nested inside it) and writes it verbatim to the
    `observed_workspaces` custom field.
  - also carries it into `inventory_raw_json.facts.workspaces`, alongside the existing
    `inventory_raw_json.facts.services`, for the same always-available-raw-blob reason.
  - No normalization beyond what nodeutils already did — pure ledger transport, per the plan.

## Deviations from the plan

None. The plan explicitly left the choice of `inventory_raw_json.facts.services` vs. "its own raw
key" to this step; picked "its own raw key" (`facts.workspaces`) since that is where the collector
actually put it (sibling to `services`, not inside it).

## Tests

`nauto` ordinary gate:

```
$ python3 -m unittest discover -s tests
Ran 112 tests in 0.020s
OK
```

New cases in `tests/test_ingest_nodeutils_inventory_job.py::BuildCustomFieldsWorkspaceTest`:
`observed_workspaces` passes through unmodified into both the custom field and the raw JSON blob
when `facts.workspaces` is present; the custom field is absent (compacted away) when no workspace
was observed.

The runtime ingest test (`tests_runtime/test_ingest_runtime.py`) via the Nautobot runtime gate is
deferred to Step 5, per the plan's "Tests" note for this step.
