# Step 2.4 — Implement review create-or-replace and both delete operations

Status: complete.

## 1. What was added

- `nctl/src/nctl_core/nautobot.py`: `rest_delete`, sharing the same connection-error and
  `_raise_for_auth` (401/403) handling as `rest_patch`/`rest_post`.
- `nctl/src/nctl_core/braindump.py`:
  - `create_or_replace_review` implementing plan.md Decision 6's five-step bounded operation
    (GraphQL-show, PATCH-if-present/POST-if-absent, single race recovery, final confirmation);
  - `delete_braindump` (cascade delete with pre-delete title/review-presence capture and
    post-delete absence confirmation);
  - `delete_review` (review-only delete by Braindump ID, idempotent no-op when already unreviewed);
  - six new error classes (`ReviewValidationFailedError`, `ReviewWriteRejectedError`,
    `ReviewConfirmationMismatchError`, `BraindumpDeleteRejectedError`, `ReviewDeleteRejectedError`,
    `DeleteConfirmationMismatchError`) completing the plan.md Decision 8 error-code table; and
  - three new envelope builders (`build_braindump_delete`, `build_braindump_review`,
    `build_braindump_review_delete`) and their `BraindumpDeleteData`/`BraindumpReviewData`/
    `BraindumpReviewDeleteData` output shapes.
- `nctl/tests/test_braindump.py`: 20 new operation-level tests appended.

## 2. Race recovery detail

The POST path treats a 400 as a possible uniqueness race only when a refetch shows a review that
did not exist at the initial GraphQL-show: in that case it PATCHes the now-current review UUID
(one bounded retry, matching Decision 6 step 4). A 400 with no review present after the refetch is
treated as a genuine validation failure and raised as `ReviewValidationFailedError` unchanged — the
race path never masks a real rejection.

## 3. Test coverage (20 new tests, all passing)

Review create-or-replace:
- creates when absent (exact POST body: `braindump`, `summary`);
- replaces in the same row when present (exact PATCH body: `summary` only);
- replacement refreshes `last_updated` even with an identical summary string;
- blank summary rejected before any request;
- unknown Braindump ID raises before any write;
- duplicate-POST race recovery patches the now-current review and confirms the caller's summary;
- a genuine validation failure (no review before or after the failed POST) is not misclassified as
  a race;
- race-recovery PATCH failure propagates `ReviewWriteRejectedError`;
- post-write confirmation mismatch fails closed; and
- connection failure propagates `NautobotConnectionError` unchanged.

Deletes:
- Braindump delete captures and returns the title and prior review presence, confirms absence via
  refetch, and reports cascade (`review_deleted=True`) or no-cascade correctly;
- unknown Braindump ID, delete rejection (5xx), and confirmation mismatch (refetch still finds the
  row) all raise the expected errors without claiming success;
- review-only delete removes exactly the review and returns its ID, preserving the Braindump;
- a missing review is an idempotent no-op (`deleted=False`, `review_id=None`, zero DELETE calls);
  and
- unknown Braindump ID, delete rejection, and confirmation mismatch (refetch still shows a review)
  all raise.

## 4. Full suite and isolation

```
uv run --project nctl pytest -q nctl/tests
688 passed, 1 warning in 5.19s
```

668 (Step 2.3 total) + 20 new = 688.

```
rg -n "import braindump|nctl_core.braindump" nctl/src
```

Only the self-referential docstring mention in `sources/braindump.py` — still no
drift/reconcile/production/dashboard/serve import of Braindump code.

## Discrepancies

None. All seven core operations behind the seven planned envelope schemas now exist; no live
DELETE has been exercised (unit tests only, per plan.md's "No test may delete a non-synthetic live
row" instruction — that is reserved for the single Step 2.8 synthetic row). Proceeding to Step 2.5.
