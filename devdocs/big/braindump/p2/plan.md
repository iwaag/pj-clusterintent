# Braindump Phase 2 Implementation Plan: Deterministic nctl Diary Access

Parent: [roadmap.md](../roadmap.md) — Phase 2.

Contracts:

- [Phase 0 plan](../p0/plan.md) — authoritative domain and safety boundary;
- [Phase 1 plan](../p1/plan.md) — authoritative nintent implementation contract; and
- [Phase 1 GraphQL handoff](../p1/report1.6.md) and
  [live rollout report](../p1/report1.8.md) — authoritative deployed API names and behavior.

Status: proposed; implementation has not started.

## Goal

Make nctl the deterministic, typed interface for the current exchange diary so an external AI
agent or a human can:

- list Braindumps with review presence and timestamps;
- show one complete Braindump/review pair;
- create and update a Braindump from literal text or a UTF-8 file;
- delete a Braindump only after explicit confirmation;
- create or replace the one current Alignment Review; and
- deliberately delete only the current review when returning a Braindump to the unreviewed state.

Reads use the Phase 1 GraphQL schema. Writes use the Phase 1 REST ViewSets. Every successful write
is confirmed by a fresh GraphQL read before nctl reports success. The prose remains an opaque
string throughout; nctl does not parse, classify, execute, summarize, or turn it into desired
state.

This phase changes nctl only. It adds no nintent model, migration, endpoint, Job, webhook, worker,
LLM runtime, prompt framework, scheduler, dashboard integration, or `nctl serve` route.

## Current state (as of 2026-07-21)

- Phase 1 is complete and live. The local Nautobot 3.1.3 instance runs nintent `0.9.0` at commit
  `aa5a052fdef07e7749b501b6c016eff2fbe10271`; migration
  `0014_braindump_exchange_diary` is applied.
- The deployed REST collections are exactly:

  ```text
  /api/plugins/intent-catalog/braindumps/
  /api/plugins/intent-catalog/alignment-reviews/
  ```

- The deployed GraphQL fields are `braindump_document`, `braindump_documents`,
  `alignment_review`, and `alignment_reviews`. A Braindump exposes optional
  `alignment_review`; GraphQL serializes authorship choices as `USER_DIRECT` and
  `AGENT_TRANSCRIBED`.
- Live Phase 1 checks proved exact Unicode/multiline storage, review replacement by PATCH,
  duplicate-review rejection, review-only deletion, Braindump cascade deletion, and an unchanged
  `nctl drift` result.
- nctl is at commit `f211c9ec70c02141b8180f95132c7541a9b00cc1`. Its focused test command is:

  ```bash
  uv run --project nctl pytest -q nctl/tests
  ```

  It currently passes 617 tests with one existing Starlette deprecation warning.
- `nctl_core.nautobot.NautobotClient` already provides GraphQL reads and REST GET/PATCH/POST plus
  connection/auth error types. It does not yet provide REST DELETE.
- `nctl_core.output.Envelope`, Pydantic result models, human renderers, and thin Typer commands are
  the established command boundary. `nctl lifecycle` is the closest write pattern: resolve by
  GraphQL, write a narrow REST PATCH, refetch by GraphQL, and fail closed on mismatch.
- `SourceSnapshot` intentionally contains only deterministic desired, actual, and observed inputs.
  It must remain unchanged by this feature.
- Existing desired typed models do not carry `last_updated`; actual freshness is split across
  per-device `last_seen`, service observation times, and nodeutils `collected_at`; and
  `SourceSnapshot.fetched_at` records fetch time rather than evidence update time. There is no
  cheap, correct cluster-wide desired/actual update watermark to compare to a review.

## Decisions taken head-on

### 1. Freeze one CLI spelling, with no aliases

Add a `braindump` Typer sub-application with exactly these commands:

```text
nctl braindump list [--json]
nctl braindump show ID [--json]
nctl braindump create --title TITLE --authorship AUTHOR (--body TEXT | --file PATH) [--json]
nctl braindump update ID [--title TITLE] [--authorship AUTHOR] [--body TEXT | --file PATH] [--json]
nctl braindump delete ID [--yes] [--json]
nctl braindump review ID (--summary TEXT | --file PATH) [--json]
nctl braindump review-delete ID [--yes] [--json]
```

`AUTHOR` is exactly `user_direct` or `agent_transcribed`. Create requires it explicitly; there is
no CLI default that could silently misstate provenance. Update preserves omitted fields and
requires at least one supplied change. `--body`/`--file` and `--summary`/`--file` are mutually
exclusive, and the relevant pair requires exactly one value.

`review ID` means “set the current review for this Braindump,” not “create a review history row.”
It creates when the review is missing and replaces the existing row when present. `review-delete`
is included because the frozen Phase 0 nctl boundary requires review deletion and because a
supported way to return a document to the normal unreviewed state is part of the two-model
lifecycle. It deletes by Braindump ID; callers never have to discover and pass the review UUID.

No `edit`, `set`, plural `braindumps`, old-name alias, or alternate top-level command is added.

### 2. Keep input exact and non-executable

Literal input is accepted exactly as received from Typer. File input uses
`Path.read_text(encoding="utf-8", errors="strict")`; it does not strip a trailing newline,
normalize line endings, remove a BOM, render Markdown, interpolate variables, invoke a shell, or
interpret prompt-like content.

Before any network write, nctl rejects:

- empty or whitespace-only title, body, or summary;
- an authorship outside the two allowed values;
- both literal and file input, or neither when prose is required;
- an update with no changed field supplied;
- an unreadable file or invalid UTF-8; and
- a malformed Braindump UUID.

Validation may inspect `value.strip()` to decide emptiness but must pass the original accepted
string to REST. No maximum length, language rule, syntax rule, hostname/service lookup, semantic
consistency check, or feasibility check is added beyond nintent's existing contract.

`--file` is the preferred path for multiline or shell-sensitive prose. Documentation examples do
not encourage embedding secrets in command-line arguments, process lists, reports, or Git.

### 3. Use a separate typed GraphQL reader, not `SourceSnapshot`

Add `nctl_core.sources.braindump` with two pinned queries:

```graphql
query ListBrainDumps {
  braindump_documents {
    id
    title
    body
    authorship
    created
    last_updated
    alignment_review {
      id
      summary
      created
      last_updated
    }
  }
}
```

```graphql
query ShowBrainDump($id: ID!) {
  braindump_document(id: $id) {
    id
    title
    body
    authorship
    created
    last_updated
    alignment_review {
      id
      summary
      created
      last_updated
    }
  }
}
```

Parse UUIDs as canonical strings, timestamps as timezone-aware `datetime`, and authorship enum
names back to the lower-case domain vocabulary. Preserve `body` and `summary` byte-for-byte at the
Python string boundary. A null singular result is `braindump_not_found`; a null nested review is a
normal state.

The new reader is called only by Braindump operations. Do not import it into
`nctl_core.sources.snapshot`, drift comparators/registry, reconcile classification/planning,
production composition, dashboard generation, Ansible rendering, status checks, or serve
snapshots.

### 4. Define the minimum timestamp attention hint

Every list/show result computes exactly one non-persisted attention value:

| Value | Condition |
|---|---|
| `unreviewed` | no review row exists |
| `needs_attention` | `review.last_updated < braindump.last_updated` |
| `review_present` | a review exists and is not older than the Braindump |

`review_present` does not mean aligned, valid, fresh enough, approved, or converged. It says only
that a current review row exists and is not older than its own Braindump.

Do not add the optional broader desired/actual comparison in this phase. Current source types do
not expose a trustworthy common update watermark: `fetched_at` is merely the read time, desired
objects omit update times, and actual observation times are per-source and may already be stale.
Adding all of that would widen deterministic source contracts and still would not prove semantic
relevance to one Braindump. nctl instead displays the diary timestamps; the external agent runs
`nctl drift --json` separately and reads its actual/observation evidence before composing a review.
This is the explicit “otherwise display timestamps and leave judgment to the agent” branch of the
roadmap.

### 5. Pin typed data shapes and output envelopes

Use shared nested models:

```text
AlignmentReviewRecord
  id, summary, created, last_updated

BrainDumpRecord
  id, title, body, authorship, created, last_updated,
  review_present, attention, alignment_review
```

`alignment_review` is null when unreviewed. `review_present` is retained as an explicit transport
fact even though it can be inferred, because list consumers should not need to interpret null
nesting. The list result may use a compact `BrainDumpListItem` that omits `body` and review
`summary`, but it must retain IDs, title, authorship, both document timestamps, review presence,
review ID/update time, and attention. Show and all confirmed create/update/review results return
the full `BrainDumpRecord`.

Freeze one envelope per public command:

| Command | Schema | `data` contract |
|---|---|---|
| list | `nctl.braindump.list.v1` | `items`, `count` |
| show | `nctl.braindump.show.v1` | `braindump` |
| create | `nctl.braindump.create.v1` | `braindump`, `changed` |
| update | `nctl.braindump.update.v1` | `braindump`, `changed` |
| delete | `nctl.braindump.delete.v1` | `id`, `title`, `deleted`, `review_deleted` |
| review | `nctl.braindump.review.v1` | `braindump`, `action` (`created` or `replaced`) |
| review-delete | `nctl.braindump.review_delete.v1` | `braindump`, `deleted`, `review_id` |

An absent review makes `review-delete` an idempotent successful no-op with `deleted: false` and a
null `review_id`; it is not an error. Create always returns `changed: true` because duplicate
titles are valid and create never guesses an existing identity. Update may return `changed: false`
when the stored representation already equals all requested fields and no REST write is needed.
The review command always performs a POST or PATCH, even when summary text is identical, because
invoking it records a new current evaluation and must advance `last_updated` for freshness.

The standard wrapper remains `{schema, generated_at, ok, data, errors}`. Human output is rendered
only from the same typed data. JSON mode emits exactly one JSON document on stdout; diagnostics
belong on stderr.

### 6. Confirm every write by GraphQL

The REST write paths are fixed:

```text
POST   /api/plugins/intent-catalog/braindumps/
PATCH  /api/plugins/intent-catalog/braindumps/{braindump_id}/
DELETE /api/plugins/intent-catalog/braindumps/{braindump_id}/

POST   /api/plugins/intent-catalog/alignment-reviews/
PATCH  /api/plugins/intent-catalog/alignment-reviews/{review_id}/
DELETE /api/plugins/intent-catalog/alignment-reviews/{review_id}/
```

Create sends exactly `title`, `body`, and `authorship`. Update sends only explicitly supplied
fields. Review create sends exactly `braindump` and `summary`; replacement PATCH sends only
`summary`.

After a successful POST/PATCH, refetch the Braindump through GraphQL and compare every requested
field exactly, including whitespace and newlines. Do not claim success from the REST response
alone. After DELETE, refetch and require absence of the target row/review. A mismatch returns a
command-scoped confirmation error and never fabricates a successful result.

Review create-or-replace is a bounded client-side operation over ordinary REST:

1. GraphQL-show the Braindump and inspect its optional review.
2. If present, PATCH its UUID.
3. If absent, POST a new review.
4. If that POST receives the known one-to-one uniqueness conflict because another writer won the
   race, refetch once and PATCH the now-current review.
5. Refetch once more and confirm its Braindump ID and exact summary.

Do not add retries for arbitrary validation errors, an nintent upsert action, locks, version
fields, ETags, history rows, or last-write conflict storage. The local single-operator scope makes
the single bounded uniqueness-race recovery sufficient.

### 7. Make destructive confirmation explicit and machine-safe

`braindump delete` warns that the current review will cascade. `review-delete` warns that the
Braindump will remain but become unreviewed. In human mode, omission of `--yes` triggers a Typer
confirmation prompt naming the target Braindump UUID; declining or EOF performs no REST request.

`--json` is non-interactive: destructive commands require `--yes`, otherwise they fail as a usage
error before loading config or contacting Nautobot. `--yes` never broadens the target; the command
still deletes only the exact UUID supplied. There is no bulk delete, title-based delete, wildcard,
or recursive client-side selection.

Confirmation stays in the CLI wrapper; the reusable `nctl_core` delete operation receives an
already-authorized exact target and never prompts or prints.

### 8. Keep errors command-scoped and prose out of diagnostics

Use stable error codes at these boundaries:

| Boundary | Codes |
|---|---|
| local input | `invalid_braindump_id`, `invalid_authorship`, `invalid_text`, `input_conflict`, `no_update_fields`, `input_file_error`, `input_file_invalid_utf8` |
| target state | `braindump_not_found`, `review_conflict` |
| REST validation/write | `braindump_validation_failed`, `review_validation_failed`, `braindump_write_rejected`, `review_write_rejected`, `braindump_delete_rejected`, `review_delete_rejected` |
| transport/API | `nautobot_token_error`, `nautobot_connection_error`, `nautobot_auth_error`, `nautobot_graphql_error`, `nautobot_server_error` |
| post-write check | `braindump_confirmation_mismatch`, `review_confirmation_mismatch`, `delete_confirmation_mismatch` |

Malformed command input or an unknown target exits 2. In JSON mode, missing destructive
confirmation is an ordinary pre-envelope usage error: stdout stays empty and the diagnostic goes
to stderr, matching nctl's existing config/usage convention. Declining an interactive prompt also
performs no write. A command that reached Nautobot but failed authentication, transport,
validation, write, race recovery, or confirmation exits 1. Success exits 0. A missing review on
show/list/review-delete is normal.

Error detail may contain field names, HTTP status, target UUID, and a short sanitized server error,
but it must not copy the API token, full body, full summary, request headers, or arbitrary stored
prose. None of these codes enters `drift.registry`, reconcile classification, dashboard health, or
event-log actuation semantics. A diary API failure affects only the invoked diary command.

## Reader, writer, and side-effect matrix

| Surface | Reads | Writes | Required behavior |
|---|---|---|---|
| `sources.braindump` | GraphQL Braindump/review fields | none | typed enum/timestamp normalization; exact prose |
| `nctl_core.braindump` list/show | typed diary reader | none | attention hint only; no printing |
| `nctl_core.braindump` create/update | GraphQL confirmation | REST Braindump POST/PATCH | narrow payload; exact refetch confirmation |
| `nctl_core.braindump` review | GraphQL relation/current row | REST review POST/PATCH | one current row; bounded race recovery |
| `nctl_core.braindump` deletes | GraphQL pre/post state | exact REST DELETE | cascade/review-only behavior confirmed |
| Typer `braindump` commands | core envelopes | none directly | parse, confirm, call core, render, choose exit |
| human output | envelope data | none | separate Braindump and AI-review headings; preserve multiline prose |
| JSON output | envelope data | none | stable schemas; opaque body/summary strings |
| `SourceSnapshot`/drift/reconcile | none from diary | none | unchanged and independently available |
| dashboard/serve/Jobs/nodeutils/Ansible | none from diary | none | no route, task, event, render, or actuation path |

## Step 2.1 — Freeze the baseline, commands, and live API handoff

Before editing nctl:

1. record the nctl commit, Python version, dependency lock state, and passing focused test count;
2. confirm nintent `0.9.0`, migration `0014`, and the four Phase 1 REST/GraphQL names against the
   running local instance without creating a row;
3. run the Phase 1 pinned list query and singular query against the empty/current live dataset to
   confirm null/multiple-result behavior and enum/timestamp spelling;
4. search nctl for existing runtime `braindump`/`alignment_review` names and confirm there is no
   abandoned client prototype or compatibility shape to preserve;
5. record the final command spellings, schemas, error codes, and the explicit decision not to
   widen `SourceSnapshot`; and
6. capture `nctl drift --json` before implementation for the Step 2.8 isolation comparison.

Do not create or delete live diary rows in this step. A deployed API discrepancy blocks Step 2.2;
revise this plan or Phase 1 rather than adding a guessed fallback reader.

Deliverable: `report2.1.md` with baseline evidence and no token or private diary prose.

## Step 2.2 — Add the typed GraphQL diary reader and attention calculation

Add:

- `nctl/src/nctl_core/sources/braindump.py`; and
- focused tests such as `nctl/tests/test_sources_braindump.py`.

Implement the two queries and typed normalization from Decisions 3–4. Sort list results
deterministically by descending `last_updated`, then title, then ID; do not rely on database
default ordering. Keep the full prose in the typed read record even when the later list envelope
projects it to compact metadata.

Test:

- zero, one, and multiple Braindumps;
- a missing nested review;
- both authorship enum values;
- timezone-aware timestamp parsing and the three attention results;
- Japanese/English/mixed Unicode, multiline text, surrounding whitespace, HTML-looking,
  shell-looking, and prompt-looking strings unchanged;
- unknown singular ID returning null;
- GraphQL errors, authentication rejection, malformed response data, and connection failure; and
- deterministic list sorting independent of server order.

Do not touch `sources/snapshot.py`, desired/actual/observed models, or any deterministic consumer.

Deliverable: `report2.2.md` with the pinned query fixtures, normalized types, and freshness boundary.

## Step 2.3 — Add exact text input and Braindump create/update core operations

Change:

- `nctl/src/nctl_core/nautobot.py` only as needed for consistent REST error handling; and
- new `nctl/src/nctl_core/braindump.py`.

Implement reusable input resolution/validation and these no-print operations/builders:

- list and show;
- create from exact title/authorship/body;
- partial update of title/authorship/body; and
- full GraphQL confirmation of successful writes.

Keep file reading in a testable core helper rather than in Typer callback logic. The CLI passes a
literal or `Path`; core resolves exactly one source and returns a structured input error. Avoid a
generic text abstraction that implies executable documents or affects other commands.

Mock the real `NautobotClient` with `respx` and prove exact REST JSON bodies, omitted-field PATCH
semantics, no-op update behavior, successful refetch confirmation, server validation mapping,
401/403, 404, 5xx, timeout/connect failure, and confirmation mismatch. Assert that error objects do
not contain the token or complete prose payload.

Deliverable: `report2.3.md` with REST payload examples using synthetic text only and operation-level
test results.

## Step 2.4 — Implement review create-or-replace and both delete operations

Extend `nctl_core.braindump` and `NautobotClient` with:

- REST DELETE wrapped with the same connection-error behavior as the existing methods;
- review POST/PATCH selection by the GraphQL relation;
- the single bounded uniqueness-race recovery from Decision 6;
- Braindump DELETE with post-delete absence confirmation; and
- review-only DELETE by Braindump ID with post-delete confirmation.

Test review creation, replacement in the same row, identical-summary timestamp refresh, missing
review no-op deletion, review-only deletion preserving the Braindump, Braindump cascade deletion,
unknown target, duplicate POST race recovery, race recovery failure, validation rejection,
authorization/server/connection failure, and every post-write mismatch.

No test may delete a non-synthetic live row. Unit tests use mocked HTTP; live destructive behavior
is reserved for one uniquely titled Step 2.8 smoke row.

Deliverable: `report2.4.md` with create/replace/delete state transitions and failure evidence.

## Step 2.5 — Add the thin Typer command group and human renderers

Change `nctl/src/nctl_core/cli/main.py` to register one `braindump` sub-application and the exact
commands from Decision 1. Keep callback work limited to:

1. parse arguments/options;
2. enforce the interactive/`--json` confirmation boundary;
3. load config;
4. call one core builder;
5. pass the returned envelope to `emit`; and
6. select exit 0/1/2 from the stable error classification.

Human rendering requirements:

- list shows ID, title, authorship, Braindump update time, review presence/update time, and
  attention without interpreting prose;
- show labels **User-originated Braindump** and **AI Alignment Review** separately, includes both
  timestamps/authorship, and prints body/summary with their newlines unchanged;
- an absent review is visibly `Unreviewed`;
- create/update/review render confirmed IDs/actions/timestamps rather than echoing an assumed
  success; and
- delete renderers state exactly which resource was confirmed absent and whether cascade/review
  deletion occurred.

Add CLI tests with `typer.testing.CliRunner` for every command, both literal/file modes, JSON
parseability, mutual exclusion, authorship choices, missing/invalid file, whitespace-only input,
update-with-no-fields, usage/failure/success exit codes, declined confirmation, EOF, and `--json`
requiring `--yes`. Mock the core boundary in CLI-only tests so business behavior remains covered in
Steps 2.2–2.4.

Deliverable: `report2.5.md` with `--help` output, representative human/JSON output, and CLI/core
separation evidence.

## Step 2.6 — Complete regression, contract, and isolation tests

Add or update:

- `nctl/tests/test_braindump.py` for core operation contracts;
- `nctl/tests/test_cli_braindump.py` for CLI behavior;
- `nctl/tests/test_nautobot.py` for DELETE/REST transport behavior; and
- `nctl/tests/test_compatibility_snapshots.py` for the seven new public envelope data shapes.

The complete test matrix must cover:

1. exact Unicode/multiline/whitespace round trips from both literal and UTF-8 files;
2. compact list versus full show projections;
3. missing review and review-older-than-Braindump attention behavior;
4. explicit authorship and partial-update preservation;
5. replacement rather than review history;
6. review-only and cascade deletion;
7. local input, GraphQL, REST, auth, network, server, validation, race, and confirmation failures;
8. no partial-success envelope after an unconfirmed write;
9. JSON stdout containing only one parseable envelope;
10. no body/summary/token leakage in diagnostics;
11. no import or registry changes in drift, reconcile, dashboard, serve, Jobs, nodeutils, or
    Ansible; and
12. all existing 617 nctl tests remaining green in addition to the new cases.

Run:

```bash
uv run --project nctl pytest -q nctl/tests
```

Also compare `rg` evidence before/after so Braindump runtime imports are limited to the new source,
core operation, CLI, tests, and documentation. Merely asserting that a test did not actuate is not
enough; the dependency boundary must remain visible in code.

Deliverable: `report2.6.md` with total test count, warnings/skips, contract snapshot results, and
isolation evidence.

## Step 2.7 — Document the public workflow and review the complete diff

Update:

- `nctl/README.md` with command examples, exact authorship meaning, file/literal rules,
  create-or-replace review behavior, confirmation behavior, attention semantics, and the required
  separate `nctl drift --json` read before an agent authors a grounded review;
- `nctl/docs/output-format.md` with all seven envelope schemas and examples containing synthetic
  prose only; and
- `nctl/docs/compatibility.md` with the newly frozen `v1` data models.

State explicitly in the README that a safe external-agent interaction is:

1. `nctl braindump list --json` and relevant `show --json` calls;
2. read all relevant Braindumps, current reviews, `nctl drift --json`, and its desired/actual
   evidence;
3. ask the user about ambiguity or proposed structured changes;
4. write only confirmed user words to a Braindump;
5. publish AI prose with `nctl braindump review`; and
6. use established desired-state/reconcile commands separately only after the required user
   authority exists.

Review the full nctl diff for aliases, prose parsing, hidden defaults, source-snapshot coupling,
LLM/model dependencies, serve routes, and accidental secret/private-text logging. Commit the nctl
change locally only after Step 2.6 is green. Codex does not push.

Deliverable: `report2.7.md` with documentation coverage, final diff review, and local commit ID.

## Step 2.8 — Run live synthetic CRUD, verify isolation, and close the phase

Against the existing local Nautobot instance, with the configured endpoint and token but without
printing the token:

1. verify `list --json` succeeds with zero or current real records without modifying them;
2. create one uniquely titled synthetic Braindump from a UTF-8 file containing Japanese,
   multiline, surrounding whitespace, HTML-looking, shell-looking, and prompt-looking text;
3. show it through GraphQL and compare exact strings/timestamps;
4. update it once from literal input and once from a file while proving omitted fields remain
   unchanged;
5. create a review, replace it in the same row, and verify attention/timestamp behavior;
6. delete only the review and verify the Braindump becomes `unreviewed`;
7. recreate the review, then delete the Braindump with `--yes` and verify the review cascades;
8. exercise one safe failure for unknown ID and one validation failure, with no partial row;
9. confirm no synthetic row remains through nctl and direct supported API reads; and
10. run `nctl drift --json` after the CRUD window and compare schema, target identities, statuses,
    and diff codes to the Step 2.1 baseline, excluding ordinary fetch/generated timestamps.

Do not run `nctl reconcile --yes`, Ansible, a Nautobot Job, a schema migration, an image rebuild, or
any actuation for this feature. No database backup is required for a code-only nctl rollout with a
single synthetic row; rollback is the prior nctl revision plus cleanup through the already verified
Phase 1 API. If cleanup cannot be confirmed, stop and report the exact synthetic UUID instead of
touching any other row.

Re-run the full nctl suite after live smoke. Update the parent repository's nctl submodule pointer
only after all checks pass. Write `report2.8.md` with:

- implemented nctl and deployed nintent revisions;
- final commands, schemas, REST paths, and GraphQL query names;
- full test counts;
- exact-text, attention, replacement, deletion, and error smoke evidence using synthetic content;
- pre/post drift-isolation comparison;
- cleanup confirmation;
- nctl commit and parent submodule pointer; and
- each exit criterion marked pass/fail.

## Verification summary

Phase 2 is not complete from unit tests alone. Required gates are:

1. the deployed Phase 1 GraphQL/REST handoff matches this plan;
2. all local input paths preserve accepted text exactly and reject invalid input before writes;
3. GraphQL-only reads and REST-only writes are observable in HTTP contract tests;
4. every successful write/delete is confirmed by GraphQL;
5. create-or-replace produces at most one current review;
6. attention is computed only from the paired diary timestamps;
7. human and JSON output are derived from the same typed envelope and keep prose opaque;
8. full nctl regression and compatibility snapshot suites pass;
9. live synthetic CRUD succeeds and is completely cleaned up; and
10. static and live evidence shows drift/reconcile and all actuation paths remain unchanged.

## Out of scope

- Any LLM, model API, prompt template, agent runtime, tool loop, scheduler, daemon, webhook, signal,
  or automatic review trigger inside nctl.
- Parsing body/summary into findings, status, score, confidence, structured requirements,
  desired-state mutations, or reconcile actions.
- Adding diary data to `SourceSnapshot`, drift targets/diffs, reconcile planning/classification,
  dashboard health, status, event artifacts, production inventory, or Ansible variables.
- Treating missing Braindump mentions as evidence that actual services are unwanted.
- A desired/actual global freshness watermark, stored invalidation flag, fingerprint, revision,
  history, archive, diff, merge, lock, or conflict-resolution system.
- Bulk import/export/delete, title-based identity, full-text/semantic search, Markdown rendering,
  attachments, stdin/editor integration, or binary/non-UTF-8 files.
- New nintent models, fields, migrations, API actions, compatibility aliases, or permissions.
- `nctl serve`, dashboard, web UI, voice/3D UI, or other client integration (optional Phase 4).
- Production-grade authentication, document-level authorization, audit signing, encryption, or
  secrets storage.
- Running the Phase 3 live conversational scenarios or mutating structured desired state in this
  implementation phase.

## Exit criteria

- [ ] The final seven CLI commands are implemented exactly once with no aliases or hidden
      authorship default.
- [ ] List/show use the deployed GraphQL schema and expose IDs, authorship, exact prose where
      applicable, timestamps, review presence, and the three-state attention hint.
- [ ] Create/update accept exactly one literal-or-UTF-8-file prose source, preserve accepted text,
      and write only through REST.
- [ ] Review is a confirmed create-or-replace operation that leaves at most one current row and
      refreshes its timestamp even when the text is unchanged.
- [ ] Braindump deletion requires explicit confirmation and confirms cascade deletion; review-only
      deletion preserves the Braindump and makes it visibly unreviewed.
- [ ] Every write/delete is refetched through GraphQL and fails closed on a mismatch.
- [ ] All commands emit documented typed `nctl.braindump.*.v1` envelopes in JSON mode and readable
      output from the same data in human mode.
- [ ] Missing review is normal; unknown ID, invalid input, API/auth/server failures, conflicts, and
      confirmation mismatches have tested stable errors and exit codes.
- [ ] Unicode, multiline, surrounding whitespace, validation, replacement, deletion, race,
      transport, JSON, and CLI/core separation cases are covered by passing tests.
- [ ] Diary code has no import or behavior path into drift, reconcile, dashboard, serve, Jobs,
      nodeutils, Ansible, or actuation.
- [ ] Live synthetic CRUD passes against nintent `0.9.0`, all smoke rows are removed, and pre/post
      deterministic drift content is unchanged.
- [ ] nctl documentation, compatibility snapshots, local commit, parent submodule pointer, and
      `report2.1.md` through `report2.8.md` record the completed implementation without tokens or
      private diary prose.

## Suggested commit order

1. Parent repository: this Phase 2 plan only.
2. nctl: typed GraphQL reader and attention models.
3. nctl: core REST CRUD/review operations and confirmation behavior.
4. nctl: CLI/renderers, complete tests, and documentation as one finished public command surface.
5. Parent repository: verified nctl submodule pointer plus `p2/report2.1.md`–`report2.8.md`.

Intermediate nctl commits may remain local while the phase is in progress. Do not push on the
user's behalf, and do not update the parent submodule pointer to an unverified intermediate state.
