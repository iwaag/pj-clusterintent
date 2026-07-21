# Step 2.2 — Add the typed GraphQL diary reader and attention calculation

Status: complete.

## 1. What was added

- `nctl/src/nctl_core/sources/braindump.py`: `LIST_QUERY`/`SHOW_QUERY` (the two pinned queries from
  `p2/plan.md` Decision 3, unchanged), `AlignmentReviewRead`/`BrainDumpRead` Pydantic models,
  `compute_attention` (the three-state hint from Decision 4), and `fetch_braindump_list`/
  `fetch_braindump_show`.
- `nctl/tests/test_sources_braindump.py`: 22 focused tests.

`authorship` is normalized by `.lower()` from Nautobot's `USER_DIRECT`/`AGENT_TRANSCRIBED` enum
names to the domain vocabulary, same convention as `sources/desired.py`. `body`/`summary` are never
touched beyond the Pydantic string boundary. List results are sorted deterministically via three
stable-sort passes (ascending id, then ascending title, then descending `last_updated`), so the
final order is descending `last_updated` with ascending title/id tie-breakers, independent of
server-returned order.

## 2. Test coverage (22 tests, all passing)

- zero, one, and multiple Braindumps;
- missing nested review (normal `unreviewed` state);
- both authorship enum values (`user_direct`, `agent_transcribed`);
- timezone-aware timestamp parsing and all three attention results (`unreviewed`,
  `needs_attention`, `review_present`);
- exact preservation of Japanese/English/mixed Unicode, multiline, surrounding-whitespace,
  HTML-looking, shell-looking, and prompt-injection-looking body/summary strings;
- unknown singular ID returning `None`;
- GraphQL errors, auth rejection (403), and connection failure all propagate the existing
  `NautobotGraphQLError`/`NautobotAuthError`/`NautobotConnectionError` types unchanged;
- malformed response data (missing required field) raises `KeyError` rather than silently
  fabricating a record; and
- deterministic list sort order verified against out-of-order server input.

## 3. Full suite and isolation

```
uv run --project nctl pytest -q nctl/tests
639 passed, 1 warning in 4.61s
```

617 (Step 2.1 baseline) + 22 new = 639. The pre-existing Starlette deprecation warning is unchanged.

```
rg -n "sources.braindump|import braindump" nctl/src
```

No output outside the new file itself — the reader is not imported by `sources/snapshot.py`, drift
comparators/registry, reconcile, production composition, dashboard, Ansible rendering, status, or
serve. Isolation from the deterministic desired/actual/drift domain holds.

## Discrepancies

None. Proceeding to Step 2.3.
