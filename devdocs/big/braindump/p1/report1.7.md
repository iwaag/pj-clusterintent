# Step 1.7 — Test the complete model, UI, REST, GraphQL, and isolation contract

Status: complete.

## Change

New `nintent/nautobot_intent_catalog/tests/test_braindump.py`, guarded by the same
`try/except ImportError` pattern as `models.py` so local Django-free discovery stays unaffected.
33 test methods across four `TestCase`/`APITestCase` classes:

- `BrainDumpModelTests` (13 tests): authorship has no model default; Unicode/multiline round trip;
  accepted surrounding whitespace not rewritten (title/body and summary); empty/whitespace-only
  title/body rejected (4 subcases); multiple Braindumps may share a title; whitespace-only summary
  rejected; missing review means unreviewed; one-review-per-Braindump enforced at the database level
  (`IntegrityError` inside `transaction.atomic()`); update replaces rather than appends;
  review-only deletion preserves its Braindump; Braindump deletion cascades to its review; neither
  model carries a reconciliation-status-like field.
- `BrainDumpViewTests` (10 tests): list/detail/add/edit/delete routes and permissions; review
  add/edit/delete, parent binding, return-URL, and duplicate-add-redirects-to-edit handling; UI
  initial authorship is `user_direct` but `agent_transcribed` is explicitly selectable; missing
  review renders `Unreviewed`; both panels render with their correct headings; `<script>` in both
  `title` and `summary` renders escaped (`&lt;script&gt;...`) and `{{ template_injection }}` in
  `summary` renders as inert literal text.
- `BrainDumpAPITests` (10 tests): create/read/list/update/delete for each collection; POST without
  authorship, with an unknown authorship choice, and with whitespace-only body all return 400;
  review POST against an unknown Braindump UUID returns 400; duplicate review creation returns 400
  without changing the existing row; PATCH replaces the review and preserves omitted fields/exact
  accepted text; cascade and review-only deletion are observable through subsequent API reads.
- `BrainDumpGraphQLTests` (2 tests): the pinned `braindump_documents { ... alignment_review { ... } }`
  query returns multiple independent documents, exact prose (including Unicode), and correctly
  represents a missing review as `null` rather than an error; the reverse-direction
  `alignment_reviews { ... braindump { id } }` query exposes the related Braindump's `id`.

## Environment fixes required to run Nautobot's test runner

Two pre-existing environment gaps blocked `nautobot-server test` and had to be resolved before any
test could run; neither is caused by or specific to this feature:

1. **`nautobot` Postgres role lacked `CREATEDB`.** `nautobot-server test` provisions its own
   disposable database and failed with `permission denied to create database`. **Paused and asked
   the user**, who approved granting it. Applied via the `admin` superuser:

   ```sql
   ALTER ROLE nautobot CREATEDB;
   ```

   This is a one-time, reversible (`ALTER ROLE nautobot NOCREATEDB;`) change to a local-only dev
   Postgres role; it grants no access to any other service and was not reverted, since Step 1.8
   will need to run this same test command again.

2. **`ALLOWED_HOSTS` didn't include the test client's host.** Nautobot's own `TestCase`/`APITestCase`
   base classes issue requests with `HTTP_HOST: nautobot.example.com` (confirmed via a one-off
   `@override_settings(DEBUG=True)` probe that exposed the underlying `DisallowedHost` exception,
   otherwise hidden behind a generic 400 page since `DEBUG=False` in this container). The container's
   configured `NAUTOBOT_ALLOWED_HOSTS` (`localhost 127.0.0.1 0.0.0.0 agstudio.local`) doesn't include
   it. Worked around by passing `nautobot.example.com` (and `testserver`, for completeness) via
   `docker exec -e NAUTOBOT_ALLOWED_HOSTS="... nautobot.example.com"` for the test invocation only —
   no persistent config file or running-container environment was changed.

## A Nautobot 3.1 behavior discovered while writing the list-view test

`ObjectListView.get()` in this Nautobot version renders the table against `self.queryset.none()`
on an ordinary page load and only serves real rows on an htmx follow-up request
(`self.queryset if htmx_request else self.queryset.none()`, where `htmx_request` is
`request.headers.get("HX-Request", False)`). This is Nautobot's own async-list-loading pattern, not
a bug in this feature's `BrainDumpDocumentListView`/`BrainDumpDocumentTable`. Diagnosed by
reproducing the empty table directly (`table.rows` was `0` even though
`BrainDumpDocument.objects.select_related("alignment_review").count()` was `1` with the identical
`LEFT OUTER JOIN` SQL that the class-level `queryset` produces) and confirmed by reading
`ObjectListView.get()`'s source. Fixed by sending `HTTP_HX_REQUEST="true"` in
`test_list_view_shows_braindump`; the other view tests (detail, add, edit, delete, review workflow)
were unaffected since they don't render through `ObjectListView`.

## Verification

```
uv run --project nintent python -m unittest discover -s nintent/nautobot_intent_catalog/tests
Ran 98 tests in 0.020s
OK
```

```
docker exec -e NAUTOBOT_ALLOWED_HOSTS="... nautobot.example.com" nautobot-nautobot-1 \
  nautobot-server test nautobot_intent_catalog.tests.test_braindump
Ran 33 tests in 3.483s
OK
```

(Run with all Step 1.1–1.7 files `docker cp`'d into the container, exactly as in prior steps, then
reverted to the committed `HEAD` state afterward; `nautobot-server check` and
`makemigrations --check --dry-run` both came back clean post-revert. `nautobot-server test`
provisions, migrates, and destroys its own disposable `test_nautobot` database each run — the live
dev database was never touched, migration `0014` remains unapplied there.)

### Repository isolation re-check

Re-ran the Step 1.1 name-collision search now that the full implementation exists:

```
grep -rIn --include="*.py" -iE "BrainDumpDocument|AlignmentReview|braindump|alignment_review" nctl
```

No output. Also confirmed no reference to either model in `nintent/nautobot_intent_catalog/jobs*`,
`nintent/nautobot_intent_catalog/operations/`, or `ansible_agdev/`. Diary CRUD has no import, signal,
Job, nodeutils, or Ansible path — matching the plan's isolation requirement — and this was proven
directly by the passing `BrainDumpGraphQLTests`/`BrainDumpAPITests`/`BrainDumpModelTests`, none of
which touch `nctl drift`, reconcile, or any Job/Ansible code path.

## Verification summary gate status

Per the plan's "Verification summary": gates 1 (local suite), 2 (migration state check — done in
Step 1.2 and re-confirmed here), 3 (Django/Nautobot model/form/view/REST/GraphQL tests), 5
(escaping/Unicode checks), 6 (review uniqueness and both deletion directions), and 7 (static
isolation evidence) are now satisfied. Gates 4 (live smoke after Git-based rebuild) and 8 (database
backup, live cleanup, rollback readiness) remain for Step 1.8.
