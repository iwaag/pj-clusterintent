# Step 1.2 — Implement the models and the single migration

Status: complete.

## Changes

- `nintent/nautobot_intent_catalog/models.py`: added `BrainDumpDocument` and `AlignmentReview`,
  both `@extras_features("graphql")` `PrimaryModel` subclasses, matching Decision 1 exactly:
  - `BrainDumpDocument`: `title` (`CharField`, max 255), `body` (`TextField`), `authorship`
    (`CharField`, choices `user_direct`/`agent_transcribed`, no default); `Meta.ordering =
    ("-last_updated", "title")`; `__str__` returns `title`; `get_absolute_url()` targets
    `braindumpdocument`; `clean()` rejects whitespace-only `title`/`body` via `.strip()` without
    rewriting the stored value.
  - `AlignmentReview`: `braindump` (`OneToOneField` to `BrainDumpDocument`, `CASCADE`,
    `related_name="alignment_review"`), `summary` (`TextField`); `__str__` identifies the related
    Braindump; `get_absolute_url()` returns the related Braindump's detail URL; `clean()` rejects
    whitespace-only `summary`.
  - Neither model overrides `save()` to call `full_clean()`.
- New migration `nintent/nautobot_intent_catalog/migrations/0014_braindump_exchange_diary.py`.

## Migration generation method

The plan requires generating (not handwriting) the migration inside a real Nautobot 3.1.3
environment. The running dev container installs nintent from GitHub, not a local mount, so the
migration was produced by temporarily copying the local, uncommitted `models.py` into the
container's installed package path (`docker cp`), running
`nautobot-server makemigrations nautobot_intent_catalog --name braindump_exchange_diary` there,
copying the generated file back into the local checkout, and then restoring the container's
installed `models.py` and removing the generated file from the container (via `docker cp` of the
pristine `git show HEAD:...` version) so the live dev instance is left exactly as it was — no
migration was applied to the database at any point.

## Migration review

Confirmed by direct inspection of the generated file:

- exactly two `CreateModel` operations (`BrainDumpDocument`, `AlignmentReview`);
- only the two app fields per model plus the normal inherited `PrimaryModel` fields (`id`,
  `created`, `last_updated`, `_custom_field_data`, `tags`);
- `authorship` is `CharField(max_length=32)` with **no default** in the migration;
- `braindump` is `OneToOneField(..., on_delete=CASCADE, related_name="alignment_review")`;
- no seed/data operation; and
- `dependencies = [('extras', '0142_remove_scheduledjob_approval_required'),
  ('nautobot_intent_catalog', '0013_analysis_provenance_and_generic_endpoint_policy')]`.

### Note: `choices` is absent from the migration file (expected, not a defect)

The generated `authorship` field line is `models.CharField(max_length=32)` — the `choices` tuple
does not appear in the migration, even though the model declares
`choices=AUTHORSHIP_CHOICES`. Investigated directly: Nautobot's own
`nautobot.core.management.commands.makemigrations` overloads `Field.deconstruct` via
`nautobot.core.management.commands.custom_deconstruct`, which strips `EXEMPT_ATTRS = ['choices',
'help_text', 'verbose_name']` from every field before writing migration state. This is Nautobot's
documented, intentional behavior for its own `nautobot-server makemigrations` command, not specific
to this migration — verified by reproducing the same field via the raw
`MigrationAutodetector`/`MigrationWriter` API (which does preserve `choices`) versus the
`nautobot-server makemigrations` CLI (which strips it via the monkeypatch). Choices remain enforced
at the Python/model/form level; this has no effect on the actual `authorship` column, which is a
plain `varchar(32)` in both cases.

## Verification

```
docker exec nautobot-nautobot-1 nautobot-server makemigrations nautobot_intent_catalog --check --dry-run
No changes detected in app 'nautobot_intent_catalog'

docker exec nautobot-nautobot-1 nautobot-server check
System check identified no issues (0 silenced).
```

Both run with the local `models.py` + `migrations/0014_braindump_exchange_diary.py` copied into the
container (temporarily, then reverted — see above). No residual model state; no system check
issues.

Local Django-free suite, run after the model change (unaffected, since the new models live inside
the existing `try/except ImportError` Django guard):

```
uv run --project nintent python -m unittest discover -s nintent/nautobot_intent_catalog/tests
Ran 98 tests in 0.018s
OK
```

The migration was not applied to the live database. The container's installed `models.py` was
restored to the pristine committed (`60a62a6`) version and the generated migration file removed
from the container filesystem before finishing this step; `nautobot-server check` and
`makemigrations --check --dry-run` were re-run against that restored state and both came back clean,
confirming the running dev instance is unaffected.
