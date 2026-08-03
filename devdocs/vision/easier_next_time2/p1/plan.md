# Easier Next Time 2 — Phase 1 Plan

Status: planned 2026-08-04. Implements Phase 1 of
[`../roadmap.md`](../roadmap.md): `WorkflowEpisode` model + REST API +
read-only GUI in nintent, deployed and live-verified on the scratch Nautobot.

## Goal and exit criteria

Add `WorkflowEpisode(title, status, raw_data)` with migrations, a dedicated
REST API (CRUD + forward-only status transitions + per-namespace writes, with
top-level namespace / `schema_version` validation), and a read-only list/detail
GUI, all in one coordinated change.

Exit (fixed by the roadmap):

- Model, API, and GUI work on the scratch Nautobot.
- An episode created via the API is visible in the GUI list and detail.
- Forward-only status transitions and rejection of invalid namespaces are
  proven by tests.

## Fixed constraints (everything else is implementer's discretion)

1. Only `title` / `status` / `raw_data` beyond `PrimaryModel` fields. No other
   column, no matter how tempting (roadmap decision 1).
2. Status vocabulary `candidate` / `selected` / `resolved` / `dismissed`;
   transitions forward-only: `candidate → selected → resolved | dismissed`,
   plus `candidate → dismissed` (decisions 2–3).
3. `raw_data` validation is a closed top-level set only:
   `schema_version` + `report` / `assessment` / `references` / `resolution`.
   Sub-fields free-form (decision 4).
4. Writes never replace the whole `raw_data`; each write API touches only its
   namespace (decision 5).
5. GUI is strictly read-only — no add/edit/delete buttons, no status buttons
   (decision 7).
6. No secrets in `raw_data`; `references` holds stable IDs, not local paths;
   no transcript/ops-evidence bodies copied in; no import of the 3 old local
   episodes (decisions 8 and environment rules).
7. Happy path only — no offline-draft fallback machinery (decision 6).
8. No backward compatibility work; policy.md/README_DEV text rewrite is
   Phase 3, not here.

Field naming inside namespaces, exact URL paths, action names, template
layout, and whether transition logic lives in the model or the viewset are
all free choices — fix them by what reads best against the Braindump
precedent.

## Precedent map (shortest path: copy Braindump's shape)

Braindump is the same species — non-desired-state model, dedicated API,
read-only GUI. Concrete anchors in `nintent/nautobot_intent_catalog/`:

| concern | precedent |
|---|---|
| model | `BrainDumpDocument`, `models.py:978` — status choices as class constants, `clean()` for non-empty title, `get_absolute_url` |
| serializer | `BrainDumpDocumentSerializer`, `api/serializers.py:18` — note `_check_allowed_mutation_keys` guarding unknown keys; reuse that idea for namespace validation |
| API viewset + custom actions | `BrainDumpDocumentViewSet`, `api/views.py:135`; `@action(detail=True, methods=["post"], url_path="complete")` at `api/views.py:184` is exactly the transition-endpoint pattern, including `select_for_update()` + status precondition check |
| API routing | `api/urls.py:9` router registration |
| GUI views | `views.py:217` (list) / `views.py:229` (detail) |
| table / filterset | `tables.py:219`, `filters.py:225` |
| URL + nav | `urls.py:57`, `navigation.py:20` |
| template | `templates/nautobot_intent_catalog/braindumpdocument.html`; `desiredworkspace.html` is the newest minimal-GUI example (creative_workspace p2ex) |
| tests | `tests/test_braindump.py`, factories in `tests/factories.py` |
| migration numbering | latest is `0028_...`; yours will be `0029_workflowepisode.py` |

## Design hints (advice, not requirements)

- **Model**: `title = CharField(255)`, `status = CharField(choices, default="candidate")`,
  `raw_data = JSONField(default=dict, blank=True)`. Put the allowed-transition
  map as a class-level dict (`{"candidate": {"selected", "dismissed"}, "selected": {"resolved", "dismissed"}}`)
  so tests and the API share one owner for the rule.
- **Transitions as API actions**: `@action(detail=True, url_path="select")`,
  `resolve`, `dismiss`. Follow the Braindump `complete` action verbatim:
  `select_for_update()`, check current status against the transition map,
  return 400/409 with a message naming the current status on violation.
  Plain `PATCH` of `status` through the standard serializer should be
  rejected (make `status` read-only in the serializer) so transitions have
  exactly one route.
- **Per-namespace writes**: one `@action(detail=True, url_path="report")`
  (and `assessment` / `references` / `resolution`) that replaces that
  namespace's value wholesale. Whole-namespace replacement is simpler than
  deep merge and sufficient — the caller owns the namespace. Bump/keep
  `schema_version` at top level; reject a request whose body tries to smuggle
  other top-level keys.
- **Namespace validation**: validate on every write path (create + namespace
  actions): top-level keys of `raw_data` must be a subset of
  `{schema_version, report, assessment, references, resolution}` and each
  namespace value must be a dict (`schema_version` an int). A single shared
  helper called from serializer + actions keeps one owner. Don't validate
  sub-fields.
- **Create**: allow `raw_data` (usually just `report` + `references`) in the
  create payload so a self-report is one POST. Status always starts
  `candidate`; ignore/reject client-supplied status on create.
- **GUI**: list columns id/title/status/created/last_updated; default filter
  `candidate` + `selected` (set via the list view's default queryset or
  default filter params — check how you want "show all" to remain reachable).
  Detail template renders four sections (report / assessment / references /
  resolution) plus a raw JSON panel; a simple `{% for %}` over key/value
  pairs per namespace is enough, no pretty-printing infrastructure.
- **GraphQL**: add `@extras_features("graphql")` like the other models —
  free, consistent.

## Test plan

Follow the README_DEV matrix; the interesting Tier A/B surface is small:

- **Tier B (Django-free fast where possible, else runtime gate)**: transition
  table — every allowed transition succeeds, every forbidden one
  (`selected → candidate`, `resolved → *`, `dismissed → *`, self-transition)
  is rejected; namespace validation — unknown top-level key rejected,
  non-dict namespace rejected, valid payload accepted.
- **Tier A (runtime gate)**: API round trip create → select → resolve;
  per-namespace write updates only its namespace (assert the other
  namespaces' values are byte-identical after the write — this is the
  decision-5 guarantee); `PATCH status` rejected; a second `select` on a
  `selected` episode rejected.
- **Tier C**: GUI smoke — list renders, detail renders an episode with all
  four namespaces populated, nav entry resolves. `test_braindump.py` shows
  the existing smoke style.

Gates: nintent Django-free fast suite, then
`./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb` while
iterating, `--clean` once before deployment. The gate wrapper's `cases=`
count must be nonzero for the new tests (README_DEV lesson: zero collected
cases is a silent pass).

## Steps

One report + one commit per step (`p1/report_stepN.md`); pause for the user at
the marked points.

### Step 1 — Model + migration + fast tests

`WorkflowEpisode` in `models.py`, transition map, `clean()` (non-empty title,
namespace validation for direct ORM writes if cheap), migration `0029`.
Django-free fast suite green.

### Step 2 — REST API

Serializer, viewset, transition actions, namespace-write actions, router
registration. Runtime gate `--keepdb` green including the new Tier A/B tests.

### Step 3 — Read-only GUI

List/detail views, table, filterset, template, URL, nav entry. Runtime gate
`--keepdb` green; GUI smoke tests included.

### Step 4 — Final gates

nintent fast suite + runtime gate `--clean` (migration check on fresh
`test_nautobot`). Record `cases=` counts in the report.

### Step 5 — Deploy to scratch Nautobot  **(pause: user pushes)**

Commit in `nintent`, ask the user to push (never push yourself —
`.local/localenv_memo.md`), then:

```bash
cd devenv/nautobot && docker compose --env-file ../.env build --no-cache
```

Check the resolved nintent SHA in the build log — the build can silently
cache a stale commit. Restart the three containers, run
`nautobot-server migrate` inside the container. Scratch migrations/restarts
need no extra approval.

### Step 6 — Live verification + phase report

Against `http://localhost:8000` with the token from `.local/secrets`
(never print the value):

1. POST an episode with a realistic `report` + `references` payload.
2. GET list filtered by status; GET detail.
3. POST `select`, then a namespace write to `assessment`, then `resolve`.
4. Attempt one forbidden transition and one invalid namespace — expect 4xx.
5. Open the GUI list (default filter shows the episode while
   `candidate`/`selected`) and detail; confirm the four sections render.
6. Decide: delete the live smoke episode or keep it as a seed for Phase 2
   smoke — either is fine, say which in the report.

Phase report states exit criteria one by one with evidence, using README_DEV
completion language.

## Out of scope for this phase

nctl command group (Phase 2), agentdocs/policy rewrite (Phase 3), any import
of `.local/evidence/workflow-episodes/`, column promotion, dashboards.
