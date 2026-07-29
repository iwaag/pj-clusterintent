# Phase 4 Step 1 Report — Private-document round trip

## Result

Complete. Before deleting the committed seed, the private operator document
was copied to `.local/backups/desired-state-pre-p4-20260730_025947.yaml` and a
PostgreSQL custom-format dump of the scratch Nautobot database was written to
`.local/backups/nautobot-pre-p4-20260730_025947.dump`. Both paths are ignored
local recovery material and were not committed.

## Verification

`uv run --project nctl nctl desired apply -f .local/desired-state.yaml`
completed as a dry run with:

```text
create=0, update=0, delete=0, unchanged=27, conflict=0
```

The private document therefore round-trips exactly to the current database
state. Step 2 may safely remove the Git seed; the database was not changed.
