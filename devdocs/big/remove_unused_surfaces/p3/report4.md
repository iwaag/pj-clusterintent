# Phase 3 Step 4 — Run local tests and structural deletion checks

Parent: [plan.md](plan.md) Step 4.

Executed 2026-07-25.

## 1. Complete local nintent suite

`python3 -m unittest discover -s nautobot_intent_catalog/tests` (from `nintent/`): **187 passed**,
unchanged since Step 0 — no Django-free fixture/loader test touched the removed fields.

## 2. Focused source-level structural checks

Ran targeted greps for each named surface from plan §7 Step 4.2; every one returned zero matches:

| Surface | Command target | Result |
|---|---|---|
| Model constants | `RECONCILIATION_` in `models.py` | 0 matches |
| Model fields | `reconciliation_status`\|`reconciliation_checked_at` in `models.py` | 0 matches |
| Filter fields | `reconciliation_status` in `filters.py` | 0 matches |
| Table fields/badge helper | `reconciliation_status`\|`RECONCILIATION_BADGE`\|`_render_reconciliation_status` in `tables.py` | 0 matches |
| Template text | `Reconciliation`\|`dashboard_url`\|`view dashboard` in both detail templates | 0 matches |
| URL names | `dashboard` in `urls.py` | 0 matches |
| Navigation labels | `dashboard`\|`Dashboard` in `navigation.py` | 0 matches |
| App settings | `dashboard_url` in `__init__.py` | 0 matches |
| Views | `dashboard` in `views.py` | 0 matches |

## 3. `git diff --check`

Clean (exit 0) — no whitespace-error/conflict-marker regressions across the Step 2/3 commit range.

## 4. Changed-file inventory matches plan §5.1/§5.2 exactly

```
 nautobot_intent_catalog/__init__.py                                      |  2 +-
 nautobot_intent_catalog/api/serializers.py                               |  4 +-
 nautobot_intent_catalog/filters.py                                       |  2 -
 nautobot_intent_catalog/migrations/0016_remove_..._surfaces.py (added)   | 33 ++
 nautobot_intent_catalog/models.py                                        | 46 ----
 nautobot_intent_catalog/navigation.py                                    | 25 +-
 nautobot_intent_catalog/tables.py                                        | 34 ----
 templates/nautobot_intent_catalog/desirednode.html                       | 13 --
 templates/nautobot_intent_catalog/desiredservice.html                    | 13 --
 nautobot_intent_catalog/urls.py                                          |  1 -
 nautobot_intent_catalog/views.py                                         | 30 --
```

11 files touched (10 edits + 1 addition) — an exact match to plan §5.1 (`0016` addition) and §5.2
(the ten named edit targets: `models.py`, `api/serializers.py`, `filters.py`, `tables.py`, both
detail templates, `views.py`, `urls.py`, `navigation.py`, `__init__.py`). No file outside this list
was touched; `forms.py`, `api/views.py`, `api/urls.py`, compute/Braindump source, and both `0009`/
`0010`/`0015` migrations remain untouched, matching plan §5.5.

## 5. nctl unchanged

`nctl` HEAD remains `7a0f2cf035179fbea5deed4cacb05573f8c8dffa`, clean — byte-for-byte identical to
the Step 0 baseline. No correction was required.

## Gate

Local tests pass, the diff is clean, and the active source/config token set contains no unexplained
match outside the migration/test exceptions defined in Step 7's later, broader search. Step 4 gate
met.
