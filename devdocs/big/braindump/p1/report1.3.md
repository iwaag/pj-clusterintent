# Step 1.3 — Add forms, filters, and the Braindump list table

Status: complete.

## Changes

- `nintent/nautobot_intent_catalog/forms.py`:
  - `BrainDumpDocumentForm(NautobotModelForm)` — `title`, `body`, `authorship`; `title`/`body`
    declared as explicit `forms.CharField(..., strip=False)` so Django's default whitespace
    trimming is disabled; `authorship` is a `ChoiceField` with
    `initial=BrainDumpDocument.AUTHORSHIP_USER_DIRECT` (UI default only — the model/serializer
    still have no default).
  - `AlignmentReviewForm(NautobotModelForm)` — `summary` only, same `strip=False` treatment.
- `nintent/nautobot_intent_catalog/filters.py`:
  - `BrainDumpDocumentFilterSet` — `id`, `title`, `authorship`, plus `q` (title `icontains` search).
  - `AlignmentReviewFilterSet` — `id`, `braindump` only; no prose/full-text search field.
- `nintent/nautobot_intent_catalog/tables.py`:
  - `BrainDumpDocumentTable` — selection (`ToggleColumn`), linked `title`, `authorship`,
    `last_updated` (labeled "Braindump updated"), a `review` column, and `actions` restricted to
    `("edit", "delete")` (matches the existing `TABLE_ACTION_BUTTONS` convention, avoiding the
    default changelog button noted in `README_DEV.md` since neither model exposes a changelog
    view). `render_review()` reads `record.alignment_review` and renders `"Unreviewed"` or the
    review's own `last_updated` — no alignment badge or score.

The N+1 avoidance (`select_related("alignment_review")`) belongs to the Step 1.4 view queryset,
per the plan; the table itself just reads whatever relation the view attaches.

## Verification

Local Django-free suite (forms/filters/tables changes live inside the existing
`try/except ImportError` Django guard, so this suite is unaffected but re-run for regression
safety):

```
uv run --project nintent python -m unittest discover -s nintent/nautobot_intent_catalog/tests
Ran 98 tests in 0.017s
OK
```

Live check inside the Nautobot 3.1.3 dev container (temporary `docker cp` of the four changed
files, exactly as in Step 1.2 — copied in, checked, then reverted back to the committed `HEAD`
state so the running dev instance is unaffected):

```python
from nautobot_intent_catalog.forms import BrainDumpDocumentForm, AlignmentReviewForm
f = BrainDumpDocumentForm()
f.fields["title"].strip       # False
f.fields["body"].strip        # False
f.fields["authorship"].initial  # "user_direct"

r = AlignmentReviewForm()
r.fields["summary"].strip     # False
```

All four values matched expectations, confirming the whitespace-preservation rule (Decision 3) and
the UI-only `user_direct` initial (Decision 1) are wired correctly at the form layer. Container
state was restored to committed `HEAD` afterward; `makemigrations --check --dry-run` and
`nautobot-server check` both came back clean, and `showmigrations` shows `0014` present but
unapplied, matching the intended pre-live-migration state.
