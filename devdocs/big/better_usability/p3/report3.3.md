# Phase 3 Step 3.3 — nintent default batch

Parent: [plan.md](plan.md), Step 3.3.

## Changed defaults (all four sites, one nintent commit)

| Site | File:line | Old | New |
|---|---|---|---|
| model field | `models.py` `DesiredNode.lifecycle` | `default=LIFECYCLE_PLANNED` | `default=LIFECYCLE_ACTIVE` |
| Quick Add initial | `forms.py` `DesiredHostQuickAddForm.lifecycle` | `initial=DesiredNode.LIFECYCLE_PLANNED` | `initial=DesiredNode.LIFECYCLE_ACTIVE` |
| host creation operation | `operations/hosts.py` `create_desired_node_with_primary_endpoint()` | `lifecycle: str = "planned"` | `lifecycle: str = "active"` |
| strict YAML loader | `loaders.py` `DesiredNodeEntry.lifecycle` dataclass default and `_normalize_desired_node_entry`'s `_choice(..., "planned")` fallback | `"planned"` | `"active"` |

`DesiredIPRangeEntry.lifecycle` (`loaders.py`, a separate model/field with the same vocabulary) and
`DesiredService.lifecycle` (`models.py`, default `proposed`) were confirmed untouched — both are
explicitly out of scope per the plan's Decision 5 and Out of scope section.

Regular `DesiredNodeForm` (`forms.py`) sets no `initial` for `lifecycle`, so it inherits the model
default automatically once the model field default changed; no separate edit was needed there, per
plan Step 3.3 item 5. REST `POST /nodes/` omission likewise inherits the model default through the
existing serializer with no runtime code change.

## Migration

`migrations/0012_desired_node_lifecycle_default_active.py`: a single `AlterField` on
`desirednode.lifecycle` changing only `default` (`"planned"` → `"active"`); choices and
`max_length` are unchanged. No `RunPython`, bulk update, trigger, or data operation — verified by
inspection and matches Decision 4 exactly. Live `makemigrations --check --dry-run`/`sqlmigrate`
verification against the running Nautobot happens in Step 3.7, since Nautobot/Django are not
installed in the local dev environment (confirmed: `import nautobot` fails locally; the local
suite tests model/loader/operation logic through Django-free fakes, matching
`README_DEV.md`'s documented limitation).

## Tests

Added lifecycle-default coverage to the existing fake-Django/pure-Python suite (no new test
infrastructure):

- `tests/test_operations_hosts.py`: omitted-lifecycle creation now asserts
  `result.desired_node.lifecycle == "active"`; new
  `test_create_desired_node_with_primary_endpoint_preserves_explicit_planned_lifecycle` asserts an
  explicit `"planned"` request is not overridden.
- `tests/test_loaders.py`: `test_loader_defaults_service_host_accepted_actual_types` now also
  asserts the omitted-lifecycle YAML node normalizes to `"active"`; new
  `test_loader_preserves_explicit_planned_desired_node_lifecycle` asserts an explicit `planned`
  YAML value survives normalization unchanged.

Full nintent suite: `uv run python -m unittest discover -s nautobot_intent_catalog/tests -p
'test_*.py'` — **91 passed** (89 baseline + 2 new), no regressions.

## Docs

Grepped `nintent/README.md` and `nintent/CONCEPT.md` for prose claiming nodes default to
`planned`, require manual promotion, or require an operational-config row — found none to correct.
Existing YAML examples with explicit `lifecycle: approved`/`active` remain accurate as written;
updating them to demonstrate the *omitted* normal-path form is Step 3.6's explicit responsibility
(plan.md Step 3.6 item 4), not duplicated here.

## Result

All four independent `DesiredNode.lifecycle` default sites now agree on `active`, every explicit
value (`planned`, `approved`, `deprecated`, `retired`) remains preserved end to end, and the
migration changes only the Django-level default with no data operation. No live Nautobot rebuild
happened in this step — deployment is Step 3.7, after Step 3.4's broader creation-path matrix and
Step 3.5's drift/reconcile isolation tests land on top of this batch.
