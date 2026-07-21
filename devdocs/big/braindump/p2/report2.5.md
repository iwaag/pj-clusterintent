# Step 2.5 — Add the thin Typer command group and human renderers

Status: complete.

## 1. What was added

- `nctl/src/nctl_core/cli/main.py`: a `braindump` Typer sub-application registered on `app`, with
  exactly the seven commands from plan.md Decision 1 (`list`, `show`, `create`, `update`, `delete`,
  `review`, `review-delete`). Callbacks are limited to parsing, the confirm/`--json` gate, loading
  config, one core-builder call, `emit`, and exit-code selection — no business logic.
- `nctl/src/nctl_core/braindump.py`: seven human renderers
  (`render_braindump_{list,show,create,update,delete,review,review_delete}_text`); `show` prints
  **User-originated Braindump** and **AI Alignment Review** as separate labeled sections with body/
  summary printed as raw unmodified text blocks (never reformatted, indented, or truncated).
  `build_braindump_create`/`update`/`review` now accept literal-or-file parameters directly and
  call `resolve_text_input` internally, so the CLI layer never touches file I/O or mutual-exclusion
  logic itself (plan.md's "keep file reading in a testable core helper" requirement).
- `_confirm_destructive` in `cli/main.py`: the shared confirmation gate for `delete`/
  `review-delete` (plan.md Decision 7) — `--json` requires `--yes` as a pre-envelope usage error;
  human mode prompts via `typer.confirm` and treats a decline or EOF (`typer.Abort`/`EOFError`) as
  "no write, exit 2".
- `nctl/tests/test_cli_braindump.py`: 33 CLI tests.

## 2. `--help` output

```
$ nctl braindump --help
Commands:
  list           List Braindumps with review presence, timestamps, and the attention hint.
  show           Show one Braindump and its current Alignment Review.
  create         Create a Braindump from literal text (--body) or a UTF-8 file (--file).
  update         Update title, authorship, and/or body; omitted fields are preserved unchanged.
  delete         Delete a Braindump; its current review, if any, is cascade-deleted with it.
  review         Create or replace the current Alignment Review for a Braindump (at most one
                 current row).
  review-delete  Delete only the current review, returning the Braindump to the unreviewed state.
```

## 3. Representative output (synthetic data, mocked core boundary)

Human `show`, unreviewed:

```
User-originated Braindump
  id: 11111111-1111-1111-1111-111111111111
  title: my title
  authorship: user_direct
  ...
  body:
  my body

AI Alignment Review
  Unreviewed
```

JSON `list`:

```json
{"schema": "nctl.braindump.list.v1", "generated_at": "...", "ok": true,
 "data": {"items": [], "count": 0}, "errors": []}
```

## 4. CLI/core separation and test coverage (33 tests, all passing)

Every CLI test mocks the corresponding `build_braindump_*` core builder (per plan.md's "Mock the
core boundary in CLI-only tests" instruction) and asserts either the exact kwargs the CLI passed
through or the rendered/JSON output and exit code — business logic (input resolution, REST
payloads, race recovery, confirmation) remains covered exclusively by Steps 2.2-2.4's tests.

Covered: literal and `--file` modes for `create`/`review` (asserting the CLI passes a `Path` object
for `--file` and `None` for the unused variant); JSON parseability for `list`/`create`/`delete`;
mutual-exclusion (`input_conflict`), missing/invalid file (`input_file_error`/
`input_file_invalid_utf8`), whitespace-only (`invalid_text`), and no-fields-supplied
(`no_update_fields`) all mapped to exit 2 via mocked error envelopes; an invalid `--authorship`
choice value rejected by Typer's own choice validation before any core call; usage (2), failure
(1), and success (0) exit codes across `show`/`create`/`update`; declined (`input="n\n"`) and EOF
(`input=""`) confirmation prompts on both `delete` and `review-delete`, each asserted via a core
builder that raises `AssertionError` if called, proving no request is made; and `--json` without
`--yes` failing before any core call with empty stdout, versus `--json --yes` succeeding normally.

## 5. Full suite and isolation

```
uv run --project nctl pytest -q nctl/tests
721 passed, 1 warning in 5.05s
```

688 (Step 2.4 total) + 33 new = 721.

```
grep -rln "nctl_core.braindump" nctl/src
nctl/src/nctl_core/braindump.py
nctl/src/nctl_core/cli/main.py
nctl/src/nctl_core/sources/braindump.py
```

Only the Braindump module family itself and its CLI registration point — no drift/reconcile/
production/dashboard/serve/Jobs/nodeutils/Ansible import.

## Discrepancy note

plan.md's Decision 8 error-code table lists `review_conflict` under the "target state" tier
alongside `braindump_not_found`. The implemented `create_or_replace_review` (Step 2.4) resolves
every uniqueness conflict internally via the bounded race-recovery path and never surfaces a
client-visible conflict error, so `review_conflict` is a reserved code with no current emitter.
This does not affect any exit criterion; noted here for Step 2.7's documentation pass.

Proceeding to Step 2.6.
