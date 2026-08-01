# Creative Workspace — Phase 2 Step 1: Actual-state reader

nctl `159fe8b`.

## What changed

`ActualFacts` (`nctl/src/nctl_core/sources/actual.py`) gains `observed_workspaces: dict[str,
dict[str, Any]] | None`, read from the `observed_workspaces` Device custom field via the same
allowlist mechanism as every other actual fact (`ACTUAL_FACT_FIELDS`). The dict-of-dicts pass-through
logic used by `observed_services` (drop non-dict entries, drop empty/`None` keys, shallow-copy each
surviving entry) is now shared as `_dict_of_dicts` (renamed from `_observed_services`, which the new
field also calls) — no divergent behavior between the two fields, per the plan's "mirroring the
`observed_services` pass-through exactly."

No change to `ACTUAL_QUERY`: Device custom fields already arrive wholesale via `_custom_field_data`.

## Tests

`tests/test_sources_actual.py`:
- Round-trip: `observed_workspaces` present and well-formed survives `read_actual_facts` unchanged
  (added to the existing allowlist test).
- Absent field → `None` (existing missing-values test extended).
- Malformed entries dropped: empty-string key, `None` key, and a non-dict value are all excluded,
  leaving only the one well-formed entry.
- Non-mapping `observed_workspaces` value (e.g. a list) → `None` for the whole field, not a crash.

## Gate

`uv run pytest -q` in `nctl/`: **1111 passed** (up from 1109 in Phase 1's Step 5 baseline — the two
new tests beyond the extended existing ones).

## Deviations

None. `_observed_services` renamed to `_dict_of_dicts` since it's now shared by two fields; this is
a pure rename with no behavior change, not a deviation from the plan's instruction to reuse the
`observed_services` pass-through.
