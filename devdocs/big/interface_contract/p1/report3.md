# Phase 1 Step 3 — Make top-level YAML validation closed

Parent: [plan.md](plan.md), Step 3.

## 1. Loader change

`nintent/nautobot_intent_catalog/loaders.py`:

- Added `CANONICAL_ROOTS`, one immutable 9-tuple in the plan's canonical order.
- After the two existing obsolete-alias checks (`service_repositories`,
  `desired_node_operational_configs`, unchanged, still returned with their specific messages),
  added a closed check: any other top-level key not in `CANONICAL_ROOTS` returns a single
  deterministic `"Unknown top-level root(s): ..."` error before any section is normalized —
  matching Step 1's `ClosedRootValidationTests`.
- Missing known roots are unaffected: `_list_section()` already treats an absent key as `[]`,
  so omission remains a no-op.

## 2. DNS/mDNS implicit-synthesis removal

`nintent/nautobot_intent_catalog/importers.py`: `desired_endpoint_defaults()` no longer calls
`default_dns_name()`/`default_mdns_name()` for a primary/primary endpoint with an omitted name.
An omitted `dns_name`/`mdns_name` now stays `None` unconditionally — matching plan Section 4.3's
"an omitted optional name must not acquire a hidden Quick-Host-Add-era default during import."
Removed the now-unused `from .names import default_dns_name, default_mdns_name` import.
`names.py` itself is unchanged (still used by the Quick Host Add operation, out of Phase 1
scope, deleted in Phase 3).

Updated the one pre-existing test that asserted the old synthesis behavior
(`test_primary_desired_endpoint_defaults_missing_names_from_resolved_node`, renamed to
`test_primary_desired_endpoint_defaults_omitted_names_stay_omitted`) to assert the new
omission-stays-omitted contract instead.

## 3. Verification

`python3 -m unittest discover -s nautobot_intent_catalog/tests`: 209 tests, 4 errors — exactly
the Step 4 ownership-split functions (`desired_node_update_fields`,
`desired_service_entry_update_fields`, `desired_service_entry_locked_fields`), still not yet
defined. Both of Step 3's own targets
(`test_unknown_top_level_root_is_rejected_even_with_every_known_root_present` and the endpoint
DNS/mDNS omission tests) now pass, along with everything from Steps 1-2. `python3 -m unittest
discover -s tests` (nauto): 110 tests, `OK`, unaffected.

## Gate

Satisfied: exactly the nine roots are accepted; the two obsolete aliases and an arbitrary
unknown root all fail closed with their own tests passing; no error path performs a write (the
loader remains pure/read-only throughout). Proceeding to Step 4.
