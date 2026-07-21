# Step 1.5 — Add complete REST CRUD for both models

Status: complete.

## Changes

- `nintent/nautobot_intent_catalog/api/serializers.py`:
  - `BrainDumpDocumentSerializer(NautobotModelSerializer)` — `fields = "__all__"`; `title`/`body`
    redeclared as `serializers.CharField(trim_whitespace=False)` (title also carries
    `max_length=255`) so DRF does not trim accepted prose before it reaches the model;
    `authorship` redeclared as `serializers.ChoiceField(choices=BrainDumpDocument.AUTHORSHIP_CHOICES)`
    with no serializer-level default, so it is required on create (PATCH still may omit it,
    per DRF's normal partial-update handling).
  - `AlignmentReviewSerializer(NautobotModelSerializer)` — `fields = "__all__"`; `braindump` is a
    plain `serializers.PrimaryKeyRelatedField` (UUID in/out, not a nested write); `summary` disables
    `trim_whitespace` for the same reason as above.
- `nintent/nautobot_intent_catalog/api/views.py`: `BrainDumpDocumentViewSet` and
  `AlignmentReviewViewSet`, both ordinary `NautobotModelViewSet` (full CRUD), with
  `select_related("alignment_review")` / `select_related("braindump")` querysets and the Step 1.3
  filter sets.
- `nintent/nautobot_intent_catalog/api/urls.py`: registered exactly
  `router.register("braindumps", views.BrainDumpDocumentViewSet)` and
  `router.register("alignment-reviews", views.AlignmentReviewViewSet)`.

No upsert endpoint, bulk action, LLM action, desired-state conversion endpoint, or special approval
route was added — both viewsets are plain resource CRUD, matching the plan.

## Why no custom `create`/`update` override

`NautobotModelSerializer`'s MRO includes `ValidatedModelSerializer`, whose `validate()` builds an
in-memory instance and calls `instance.full_clean()` before save. This means the model's `clean()`
(Step 1.2 — rejects whitespace-only `title`/`body`/`summary` without rewriting accepted text) runs
automatically on every REST write; no serializer-level re-implementation of that rule was needed.
The same `full_clean()` call also runs `validate_unique()`, which is what turns a duplicate
`AlignmentReview.braindump` POST into DRF's ordinary validation-error response rather than a raw
database `IntegrityError` — again with no custom code.

## Verification

Local Django-free suite (REST code lives behind the same Django import, unaffected but re-run):

```
uv run --project nintent python -m unittest discover -s nintent/nautobot_intent_catalog/tests
Ran 98 tests in 0.016s
OK
```

Live checks inside the Nautobot 3.1.3 dev container (all nine changed/added Python files `docker
cp`'d in temporarily, then reverted to committed `HEAD` — same method as prior steps; no migration
applied):

```
reverse("plugins-api:nautobot_intent_catalog-api:braindumpdocument-list")
  -> /api/plugins/intent-catalog/braindumps/
reverse("plugins-api:nautobot_intent_catalog-api:alignmentreview-list")
  -> /api/plugins/intent-catalog/alignment-reviews/
```

Both match the plan's pinned paths exactly. Field-level serializer inspection (no data bound, no DB
access):

```
BrainDumpDocumentSerializer().fields["title"].trim_whitespace       -> False
BrainDumpDocumentSerializer().fields["body"].trim_whitespace        -> False
BrainDumpDocumentSerializer().fields["authorship"].required         -> True
BrainDumpDocumentSerializer().fields["authorship"].choices.keys()   -> ['user_direct', 'agent_transcribed']
AlignmentReviewSerializer().fields["summary"].trim_whitespace       -> False
AlignmentReviewSerializer().fields["braindump"]                     -> PrimaryKeyRelatedField
```

`nautobot-server check` reported no issues both before and after this step's temporary file copy.

### Deferred to Step 1.7: behavioral REST tests need a migrated database

An attempt to exercise `BrainDumpDocumentSerializer(data=...).is_valid()` directly (to prove
whitespace-only input is rejected end-to-end) failed with
`ProgrammingError: relation "nautobot_intent_catalog_braindumpdocument" does not exist` — Django's
`full_clean()` calls `validate_unique()` unconditionally, which queries the database for every
model (including the implicit primary-key uniqueness check) regardless of whether the model
declares its own unique fields. Since migration `0014` is deliberately not applied to the live dev
database until Step 1.8, this class of test cannot run safely here. Full behavioral REST
coverage — create/read/list/update/delete, missing/unknown authorship, whitespace-only rejection,
duplicate-review 409/400, PATCH partial-update semantics, and cascade/review-only deletion
visibility — is Step 1.7's job, using Nautobot's own disposable per-test-run database.

Container state was restored to the committed `HEAD` afterward; `nautobot-server check` and
`makemigrations --check --dry-run` both came back clean.
