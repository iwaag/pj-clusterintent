# Phase 1 Step 1 — Freeze tests for the final YAML and ownership rules

Parent: [plan.md](plan.md), Step 1.

## 1. New pure planning engine

Added `nintent/nautobot_intent_catalog/import_plan.py`: a Django-free `plan_upsert()` function
that is the one create/update/unchanged/conflict decision used by every root in both Import and
Analyze (plan Section 5.2/6.2). It takes pre-fetched existing rows as plain dicts (never an ORM
queryset or model instance), so it structurally cannot call `save()`/`update()`/`delete()`/
`bulk_create()` — the preview-performs-no-mutation guarantee (Section 5.2, Step 1 item 10) is
architectural, not merely tested. Also added `unresolved_reference()`, `totals()`, and
`build_artifact()` (the shared versioned JSON artifact shape for both Jobs).

## 2. New tests added

`tests/test_loaders.py`:

- `ClosedRootValidationTests` — all nine known roots accepted together; a genuinely unknown root
  rejected even when every known root is present and valid; both obsolete aliases
  (`service_repositories`, `desired_node_operational_configs`) still rejected with their
  specific messages (Step 1 items 1-2).
- `OmittedRootIsNoOpTests` — a missing known root stays an empty no-op section, no error.
- `EndpointDnsMdnsOmissionTests` — an omitted primary-endpoint `dns_name`/`mdns_name` stays
  `None` through the loader; an explicit name survives normalization unchanged (Step 1 item 5).
- `CanonicalFileIdentityCountTests` — the real checked-in `nauto/seed/intent_sources.yaml` loads
  with zero errors and matches the exact Phase 0 identity set from plan Section 4.2 (Step 1
  item 3): 2 intent sources, 5 nodes, 5 endpoints, 3 IP ranges, 0 compute rows, 6 services, 1
  placement, 0 overrides, and none of the six stale node slugs present.
- `RealizedFieldNeverAcceptedFromYamlTests` — no realized-link/source key is a recognized loader
  dataclass field (Step 1 item 4).

`tests/test_importers.py`:

- `OwnershipSplitTests` — `desired_node_update_fields()` excludes `lifecycle` (create-only,
  Step 1 item 7) and any realized field; `desired_service_entry_update_fields()` is exactly
  `{lifecycle, notes}` and never includes `requirements`/`name`/`slug`/`display_name`/analysis
  fields (Step 1 item 9); `desired_service_entry_locked_fields()` covers
  `name`/`slug`/`display_name`, the fields whose disagreement must block as a conflict rather
  than silently overwrite (Section 5.3).
- `ImportPlanEngineTests` — create/update/unchanged/conflict classification, duplicate-existing-
  rows-as-conflict, a preserved field (`lifecycle`) reported without being compared/changed, a
  locked-field disagreement blocking as `conflict`, and a structural no-mutation-possible
  assertion for the preview path (Step 1 items 6, 8, 10).

## 3. Failing-for-the-intended-reason confirmation

`python3 -m unittest discover -s nautobot_intent_catalog/tests`: 209 tests, 6 failures/errors,
all in the newly added tests and all for the expected reason:

| Test | Failure reason | Fixed in |
|---|---|---|
| `test_unknown_top_level_root_is_rejected...` | loader does not yet reject an unknown root | Step 3 |
| `test_canonical_checked_in_file_matches_exact_confirmed_counts` | checked-in file still has 9 stale nodes / missing `Manual`+`agdnsmasq`/`aghub`/`desired_ip_ranges` | Step 2 |
| `test_desired_node_update_fields_excludes_lifecycle` | `ImportError`, function not yet defined | Step 4 |
| `test_desired_service_entry_update_fields_excludes_operator_and_analysis_fields` | `ImportError` | Step 4 |
| `test_desired_service_entry_locked_fields_covers_identity_display` | `ImportError` | Step 4 |
| `test_desired_service_entry_defaults_never_resets_requirements_field` | `ImportError` | Step 4 |

The remaining 203 tests (187 pre-existing + 16 new engine/omission/alias/no-op tests) pass
unchanged, confirming the new tests describe the retained target contract rather than
duplicating or breaking existing coverage.

## Gate

Satisfied: the new tests describe the Phase 1 target contract (closed roots, no hidden DNS/mDNS
default, exact canonical identity set, ownership-split update fields, pure no-mutation planner),
and every one fails against the pre-Phase-1 implementation for the specific, expected reason.
Proceeding to Step 2.
