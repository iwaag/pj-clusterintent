# Phase 2 Step 7 — Documentation, compatibility searches, and schema audit

Parent: [plan.md](plan.md) — Step 7.

This step performs documentation updates, active/historical compatibility reference classification, query digest re-verification, and database schema audit.

## 1. Work Completed

### Current Documentation Updates
- Updated `nintent/README.md` to state that Nautobot GraphQL is the canonical domain read path.
- Documented only the three retained REST mutation collections (`nodes`, `braindumps`, `alignment-reviews`), exact allowed methods, writable field constraints, and 400 Bad Request error behavior for unallowed or unknown keys.
- Documented the deletion of `services`, `endpoints`, `compute-platforms`, and `compute-instances` REST collections (`404 Not Found`).

### Compatibility Searches & Classification
- Re-ran repository-wide searches across active code, tests, and configuration for removed symbols (`DesiredServiceViewSet`, `DesiredEndpointViewSet`, `DesiredComputePlatformViewSet`, `DesiredComputeInstanceViewSet`, `fields = "__all__"`).
- Confirmed zero active code occurrences of `fields = "__all__"` in `nintent` REST serializers.
- Confirmed zero active `rest_get` callers in `nctl/src/` outside the 4 classified Job/method protocol lines.

### Query Digest Audit
- Re-computed normalized SHA-256 digests for all 4 pinned GraphQL queries:
  - `DESIRED_QUERY`: `e6e34a9f6dd1a561f6a446e7ac464dc62b9566c989d96df0d3561cbfded17357`
  - `ACTUAL_QUERY`: `f2b8808491d5cc80f5cbe65cfc05841bb18d82ad13cdbeee3f50a97c234e879a`
  - `LIST_QUERY`: `e276ec2a13eebe7fc0e416e9ff08d785bb6a122d14a006e020afa0f048f2c19d`
  - `SHOW_QUERY`: `003a5ffec0e00c7abb0a8a6e85af355abb2a34599bc845ff35e9cbd7b4aebe70`
- Confirmed 100% match with Phase 0 report7 digests.

### Database Schema Audit
- Confirmed migration state remains through `0016_remove_reconciliation_dashboard_surfaces`.
- Confirmed `makemigrations nautobot_intent_catalog --check --dry-run` reports zero pending changes.

## 2. Gate Status

Step 7 gate passed cleanly. Proceeding to Step 8 (Coordinated commits and final report).
