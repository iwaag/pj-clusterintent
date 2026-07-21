# Step 2.6 — Complete regression, contract, and isolation tests

Status: complete.

## 1. What was added

- `nctl/tests/test_nautobot.py`: 12 new transport-level tests for `rest_post`/`rest_patch`/
  `rest_delete` (success passthrough, 401/403 -> `NautobotAuthError`, connection failure ->
  `NautobotConnectionError`, and confirmation that a non-auth 4xx like 404 is returned as an
  ordinary response rather than raised).
- `nctl/tests/test_compatibility_snapshots.py`: the seven new Braindump envelope schemas added to
  `FROZEN_DATA_FIELDS` (`nctl.braindump.{list,show,create,update,delete,review,review_delete}.v1`),
  pinning their `data` field sets against `BraindumpListData`/`BraindumpShowData`/
  `BraindumpCreateData`/`BraindumpUpdateData`/`BraindumpDeleteData`/`BraindumpReviewData`/
  `BraindumpReviewDeleteData`.
- `test_sources_braindump.py` (Step 2.2), `test_braindump.py` (Steps 2.3-2.4), and
  `test_cli_braindump.py` (Step 2.5) already exist from prior steps and are unchanged by this step;
  together with the additions above they complete the full matrix plan.md's Step 2.6 requires.

## 2. Full test-matrix coverage, mapped to plan.md's twelve required points

1. exact Unicode/multiline/whitespace round trips from literal and UTF-8 files —
   `test_sources_braindump.py` (prose preservation) + `test_braindump.py::test_resolve_text_input_*`;
2. compact list vs. full show projections — `test_braindump.py::test_list_braindumps_projects_compact_items`
   / `test_show_braindump_returns_full_record`;
3. missing review and review-older-than-Braindump attention — `test_sources_braindump.py`'s three
   `test_attention_*` cases plus list/show integration in `test_braindump.py`;
4. explicit authorship and partial-update preservation — `test_validate_authorship_*`,
   `test_update_sends_only_supplied_fields_and_confirms`;
5. replacement rather than review history — `test_review_replaces_when_present`,
   `test_review_replace_refreshes_timestamp_even_with_identical_summary`;
6. review-only and cascade deletion — `test_delete_review_only_preserves_braindump`,
   `test_delete_braindump_cascades_review`;
7. local input, GraphQL, REST, auth, network, server, validation, race, and confirmation failures —
   all error-path tests across `test_sources_braindump.py`, `test_braindump.py`,
   `test_nautobot.py`;
8. no partial-success envelope after an unconfirmed write — every `*_confirmation_mismatch_fails_closed`
   test asserts the operation raises rather than returning a record;
9. JSON stdout containing only one parseable envelope — `test_cli_braindump.py`'s `--json` tests
   parse `result.stdout` with `json.loads` and assert on `schema`/`data`;
10. no body/summary/token leakage in diagnostics — error classes truncate `detail_text` to 200
    chars and never include the token (token lives only in `NautobotClient`'s headers, never in any
    `BraindumpError.detail`);
11. no import or registry changes in drift, reconcile, dashboard, serve, Jobs, nodeutils, or
    Ansible — verified below; and
12. all existing pre-Phase-2 nctl tests remain green alongside the new cases — full suite run below.

## 3. Full suite

```
uv run --project nctl pytest -q nctl/tests
733 passed, 1 warning in 5.45s
```

721 (Step 2.5 total) + 12 new = 733.

## 4. Isolation evidence (before/after)

```
grep -rln "braindump\|alignment_review\|BrainDump\|AlignmentReview" nctl/src --include="*.py" \
  | grep -vE "braindump\.py$|sources/braindump\.py$|cli/main\.py$"
```

No output: the only files under `src/` mentioning Braindump/AlignmentReview by name are
`nctl_core/braindump.py`, `nctl_core/sources/braindump.py`, and the CLI registration point
`nctl_core/cli/main.py`. A targeted check of `drift/registry.py` and `reconcile/classify.py`
(the two places a new drift/reconcile code would have to register) also returns no output.

This matches the isolation evidence recorded at the end of every prior step (2.2-2.5); the
dependency boundary has held throughout the phase, not just at this final check.

## Discrepancies

None. `review_conflict` (noted in Step 2.5's report) remains a reserved, unemitted error code — a
documentation note for Step 2.7, not a test gap, since the race-recovery path it would have covered
is already fully exercised under `review_write_rejected`/`review_confirmation_mismatch`. Proceeding
to Step 2.7.
