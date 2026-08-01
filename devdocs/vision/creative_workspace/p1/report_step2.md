# Step 2 — nctl probe-hint plumbing

## Changes (`nctl` `32d3e6d`)

- `sources/desired.py`: added `desired_workspaces` to `DESIRED_QUERY` (`id`, `slug`, `name`,
  `lifecycle`, `source_remote_url`, `expected_path`, `desired_presence`, `desired_node {id slug}`
  — field names and plural confirmed live against the local Nautobot in `p0/report_step6.md`), a
  `DesiredWorkspace` model, `DesiredSnapshot.workspaces`, and `_build_workspace` (lowercases
  `lifecycle`/`desired_presence`, same pattern as every other choice field here).
  - Decoded with `data.get("desired_workspaces") or []`, not a required key like the older
    `desired_service_bindings` — matches the compute-root leniency, so none of the ~8 existing
    `DESIRED_DATA`/`_base_response` test fixtures across the repo needed updating.
- `observation.py`'s `render_probe_hints` now also emits `workspace_probe_hints`
  (`{slug: {"path": expected_path}}`) for every `DesiredWorkspace` on the target node whose
  `lifecycle == "active"` and `desired_presence == "present"` — retired or not-yet-present
  workspaces are filtered out here rather than left for nodeutils to guess about. Always present
  as a key (possibly `{}`), same shape discipline as `service_probe_hints`.

## Deviations from the plan

None. Followed the plan's recommended filter (active + present) exactly.

## Tests

`nctl` ordinary gate:

```
$ uv run pytest -q --durations=20
1109 passed in 7.40s
```

New/changed cases:
- `test_sources_desired.py`: workspace decoding assertions added to the existing
  round-trip test, plus a new "field absent" default-to-`[]` test and a `desired_workspaces`
  presence check in `test_query_requests_all_desired_collections`.
- `test_observation.py`: three new `render_probe_hints` cases — active+present workspace on the
  target node, a workspace placed on a different node (omitted), and retired/absent workspaces
  (both omitted). The five pre-existing `render_probe_hints` assertions were updated to expect the
  now-always-present `"workspace_probe_hints": {}` key.
