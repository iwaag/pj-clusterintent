# Step 2.3 — Add exact text input and Braindump create/update core operations

Status: complete.

## 1. What was added

- `nctl/src/nctl_core/braindump.py`: input resolution/validation (`resolve_text_input`,
  `validate_authorship`, `validate_braindump_id`), no-print operations
  (`list_braindumps`/`show_braindump`/`create_braindump`/`update_braindump`), the typed output
  record shapes from Decision 5 (`BrainDumpRecord`, `BrainDumpListItem`,
  `AlignmentReviewRecord`), and the four CLI-facing envelope builders
  (`build_braindump_list`/`show`/`create`/`update`) that never raise, following the
  `nctl_core.lifecycle` pattern.
- `nctl/tests/test_braindump.py`: 29 operation-level tests.
- `nctl/src/nctl_core/nautobot.py`: `rest_patch`/`rest_post` now share a `_raise_for_auth` check
  (401/403 -> `NautobotAuthError`), matching the existing `graphql()` convention. Previously only
  `graphql()` distinguished auth failures; REST writes returned the raw response, which would have
  made `create`/`update` misclassify 401/403 as an ordinary write rejection. This is the "as needed
  for consistent REST error handling" change the plan anticipated for this step.

## 2. REST payload examples (synthetic text only)

Create sends exactly:

```json
POST /api/plugins/intent-catalog/braindumps/
{"title": "T", "body": "B", "authorship": "agent_transcribed"}
```

Update sends only explicitly supplied fields, e.g. a title-only update:

```json
PATCH /api/plugins/intent-catalog/braindumps/{id}/
{"title": "new"}
```

## 3. Operation-level test coverage (29 tests, all passing)

- `resolve_text_input`: literal path, UTF-8 file path (including exact trailing-newline
  preservation), both-provided and neither-provided conflict, whitespace-only rejection, missing
  file, invalid UTF-8;
- `validate_authorship`/`validate_braindump_id`: both authorship values, unknown value rejected,
  UUID canonicalization, malformed UUID rejected;
- `list_braindumps`: compact projection (no `body` field) with review presence/ID/attention;
- `show_braindump`: not-found raises before any further work, malformed ID rejected *before* the
  GraphQL fetch (asserted via a fetch that raises `AssertionError` if called), full record returned;
- `create_braindump`: exact REST JSON body, blank-title rejected before any request, 400 mapped to
  `braindump_validation_failed`, 500 mapped to `braindump_write_rejected`, 403 mapped to
  `NautobotAuthError`, post-write GraphQL mismatch raises `BraindumpConfirmationMismatchError`
  without claiming success;
- `update_braindump`: no-fields-supplied rejected before any fetch, omitted-field PATCH semantics,
  no-op when the stored representation already matches (`changed=False`, zero PATCH calls), unknown
  ID raises, confirmation mismatch fails closed, validation failure mapped, and connection failure
  propagates `NautobotConnectionError` unchanged.

GraphQL reads are monkeypatched at the `fetch_braindump_show`/`fetch_braindump_list` call sites
(same technique as `test_lifecycle_contract.py`'s `fetch_desired_snapshot` patching), isolating
these REST-contract tests from GraphQL response shape, which is already covered by
`test_sources_braindump.py`.

## 4. Full suite and isolation

```
uv run --project nctl pytest -q nctl/tests
668 passed, 1 warning in 5.32s
```

639 (Step 2.2 total) + 29 new = 668.

```
rg -n "import braindump|nctl_core.braindump" nctl/src
```

Only the self-referential docstring mention in `sources/braindump.py` — no drift/reconcile/
production/dashboard/serve import of the new module.

## Discrepancies

None beyond the anticipated `nautobot.py` auth-handling fix, which is in scope per plan.md's Step
2.3 change list ("as needed for consistent REST error handling"). Proceeding to Step 2.4.
