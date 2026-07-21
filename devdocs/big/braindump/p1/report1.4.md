# Step 1.4 — Add the paired UI, routes, template, and navigation

Status: complete.

## Changes

- `nintent/nautobot_intent_catalog/views.py`: added
  `BrainDumpDocumentListView`/`View`/`EditView`/`DeleteView` (standard
  `ObjectListView`/`ObjectView`/`ObjectEditView`/`ObjectDeleteView`, queryset
  `select_related("alignment_review")` on the list/detail views), and
  `AlignmentReviewAddView`/`EditView`/`DeleteView`:
  - `AlignmentReviewAddView` binds the parent Braindump in `alter_obj()` from the
    `braindump_pk` URL kwarg (the form has no `braindump` field, so a review can never be
    misattached), and overrides `dispatch()` to redirect to the existing review's edit route
    (with an info message) if one is already present, rather than creating a second row or
    letting a race reach the form.
  - `AlignmentReviewDeleteView` overrides `get_return_url()` to use `obj.braindump.get_absolute_url()`
    directly (via the still-present `braindump_id` in memory), since after `obj.delete()` the base
    `GetReturnURLMixin` logic — which checks `obj.present_in_database and obj.pk` — no longer finds a
    usable `pk` to call `obj.get_absolute_url()` through.
  - `AlignmentReviewEditView` needs no override: the form has no `braindump` field, and
    `AlignmentReview.get_absolute_url()` (Step 1.2) already points at the related Braindump, so the
    base `get_return_url()` logic handles it.
- `nintent/nautobot_intent_catalog/urls.py`: added the 8 pinned route names exactly as specified —
  `braindumpdocument_list/_add/(detail)/_edit/_delete` under `braindumps/`, and
  `alignmentreview_add` (parent-scoped, `braindumps/<braindump_pk>/review/add/`),
  `alignmentreview_edit`/`_delete` (review-UUID-scoped, `braindumps/review/<pk>/...`).
- `nintent/nautobot_intent_catalog/navigation.py`: one `Braindumps` `NavMenuItem` added to the
  existing `Intent Catalog` nav group; no separate review item.
- New `nintent/nautobot_intent_catalog/templates/nautobot_intent_catalog/braindumpdocument.html`:
  two panels — "User-originated Braindump" (title, authorship, created/updated, body) and "AI
  Alignment Review" (review's own updated time, summary, edit/delete actions, or an "Unreviewed"
  message with an add action). Both `body` and `summary` render inside a
  `<div style="white-space: pre-wrap;">` with plain Django variable interpolation — no `|safe`
  filter anywhere in the template.
- `nintent/nautobot_intent_catalog/tests/test_templates.py`: added `braindumpdocument.html` to the
  expected default-template set.

## Verification

Local Django-free suite (unaffected — all new code is inside the existing `try/except ImportError`
Django guard):

```
uv run --project nintent python -m unittest discover -s nintent/nautobot_intent_catalog/tests
Ran 98 tests in 0.017s
OK
```

Live checks inside the Nautobot 3.1.3 dev container (all seven changed Python files plus the new
template `docker cp`'d in temporarily, then reverted to committed `HEAD` — same method as Steps 1.2
and 1.3; no migration applied):

- `nautobot-server check` → `System check identified no issues (0 silenced)`.
- All 8 pinned route names `reverse()` to the expected paths:

  ```
  braindumpdocument_list    -> /plugins/intent-catalog/braindumps/
  braindumpdocument_add     -> /plugins/intent-catalog/braindumps/add/
  braindumpdocument         -> /plugins/intent-catalog/braindumps/<uuid>/
  braindumpdocument_edit    -> /plugins/intent-catalog/braindumps/<uuid>/edit/
  braindumpdocument_delete  -> /plugins/intent-catalog/braindumps/<uuid>/delete/
  alignmentreview_add       -> /plugins/intent-catalog/braindumps/<uuid>/review/add/
  alignmentreview_edit      -> /plugins/intent-catalog/braindumps/review/<uuid>/edit/
  alignmentreview_delete    -> /plugins/intent-catalog/braindumps/review/<uuid>/delete/
  ```

- Rendered `braindumpdocument.html` via `render_to_string()` with unsaved `BrainDumpDocument`/
  `AlignmentReview` instances (pk explicitly assigned, no DB writes) containing an adversarial
  payload: `title = "<script>alert(1)</script> title"`, `summary = "Review says:
  <script>alert(2)</script> {{ template_injection }}"`, and `body` mixing multiline text, HTML,
  shell-looking text (`$(rm -rf /)`), and Japanese/English Unicode.

  Results:
  - `<script>alert(1)</script>` / `<script>alert(2)</script>` never appear raw in the output;
    `&lt;script&gt;alert(1)&lt;/script&gt;` and `&lt;script&gt;alert(2)&lt;/script&gt;` do — both
    fields are escaped.
  - The literal string `{{ template_injection }}` appears unevaluated in the output — Django does
    not re-parse stored prose as template syntax.
  - `white-space: pre-wrap;` appears exactly twice (body panel, summary panel); the multiline text
    and Unicode content are preserved in the rendered HTML.
  - The review panel correctly shows the review's `last_updated`, escaped `summary`, and both edit
    and delete links pointing at the right review UUID.

- Rendering a Braindump **without** an attached review (no manual cache set on the reverse
  one-to-one accessor) raised `ProgrammingError: relation
  "nautobot_intent_catalog_alignmentreview" does not exist` — expected, since migration `0014` is
  deliberately not applied to this database yet (per Steps 1.2–1.4's "do not migrate the live
  database" constraint). The "Unreviewed" branch's Django logic was reviewed by inspection (an
  `{% if review %} ... {% else %}Unreviewed...{% endif %}` on `object.alignment_review`, matching
  the reverse-`OneToOneField`'s standard `RelatedObjectDoesNotExist`-swallowing default-manager
  behavior used elsewhere in this app). Full functional proof of the "Unreviewed" path — and of the
  real HTTP GET/POST cycle through these views — requires a migrated database and is deferred to
  Step 1.7, which uses Nautobot's own disposable per-test-run database (never the live dev
  database).

Container state was restored to the committed `HEAD` afterward; `nautobot-server check` and
`makemigrations --check --dry-run` both came back clean.
