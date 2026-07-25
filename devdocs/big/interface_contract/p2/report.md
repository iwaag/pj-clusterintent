# Phase 2 Final Report: Contract REST and Canonicalize Confirmation Reads

Parent: [plan.md](plan.md)
Parent Roadmap: [roadmap.md](../roadmap.md)

- **Status:** `implemented, not deployed`
- **Execution Window:** 2026-07-26T00:15:00+09:00 — 2026-07-26T00:30:00+09:00
- **Evidence Directory:** `.local/interface-contract/p2/20260726_001500/`

## 1. Executive Summary

Phase 2 successfully contracted nintent's REST API to the three retained mutation collections, removed GraphQL exposure from `IntentSource`, and converted `nctl`'s `execute_link_actual_node` reconciler to use canonical GraphQL snapshot reading and post-write confirmation.

Key accomplishments:
1. **Contracted REST API:** Deleted `services`, `endpoints`, `compute-platforms`, and `compute-instances` REST collections (`404 Not Found`).
2. **Explicit Fields & Method Restrictions:**
   - `nodes`: GET (incidental), PATCH (detail only: `lifecycle`, `realized_device`, `realized_device_source`). POST, PUT, DELETE return `405 Method Not Allowed`.
   - `braindumps`: GET, POST, detail PATCH, detail DELETE. PUT returns `405 Method Not Allowed`.
   - `alignment-reviews`: GET, POST, detail PATCH, detail DELETE. PUT returns `405 Method Not Allowed`.
   - Replaced all `fields = "__all__"` with explicit field lists and strict `_check_allowed_mutation_keys` validation (returns 400 Bad Request for unallowed/unknown keys).
3. **GraphQL Canonical Reads:**
   - Removed `@extras_features("graphql")` from `IntentSource` model. Retained GraphQL registration for all 11 other models.
   - Updated `nctl`'s `execute_link_actual_node` to perform GraphQL snapshot pre-read, exact two-field PATCH, and GraphQL snapshot refetch confirmation.
   - Reduced domain-object `rest_get` calls in `nctl/src/` to **0**.
4. **Verification:**
   - **291/291** Nautobot runtime tests passed under disposable database.
   - **954/954** `nctl` tests passed.
   - **0** pending Django database migrations (`0016` intact).

## 2. Revisions & Submodule Status

| Component | Final Revision | State |
|---|---|---|
| superproject | `473a672` (to be updated with final pointer commit) | Clean |
| `nintent` | `e94eac2` | Clean |
| `nctl` | `8175f26` | Clean |
| `nauto` | `2635e648469d6e6bad87af113f7427b878b0a387` | Clean |

## 3. Route, Method, and Serializer Matrix

| Collection | Endpoints | Final Methods | Writable Fields |
|---|---|---|---|
| `nodes` | `/api/plugins/intent-catalog/nodes/<uuid>/` | GET (incidental), PATCH | `lifecycle`, `realized_device`, `realized_device_source` |
| `braindumps` | `/api/plugins/intent-catalog/braindumps/` | GET, POST, PATCH, DELETE | `title`, `body`, `authorship` |
| `alignment-reviews` | `/api/plugins/intent-catalog/alignment-reviews/` | GET, POST, PATCH, DELETE | `braindump` (create), `summary` (create/patch) |
| `services` | Deleted (`404 Not Found`) | None | None |
| `endpoints` | Deleted (`404 Not Found`) | None | None |
| `compute-platforms` | Deleted (`404 Not Found`) | None | None |
| `compute-instances` | Deleted (`404 Not Found`) | None | None |

## 4. GraphQL Query Digest Manifest

All 4 pinned GraphQL query SHA-256 digests in `nctl_core` match Phase 0 report7:

- `DESIRED_QUERY`: `e6e34a9f6dd1a561f6a446e7ac464dc62b9566c989d96df0d3561cbfded17357`
- `ACTUAL_QUERY`: `f2b8808491d5cc80f5cbe65cfc05841bb18d82ad13cdbeee3f50a97c234e879a`
- `LIST_QUERY`: `e276ec2a13eebe7fc0e416e9ff08d785bb6a122d14a006e020afa0f048f2c19d`
- `SHOW_QUERY`: `003a5ffec0e00c7abb0a8a6e85af355abb2a34599bc845ff35e9cbd7b4aebe70`

## 5. Verification Evidence Summary

- **Phase 2 Step 0 (`report0.md`):** Recaptured boundary, baseline revisions, query digests, and test suite counts.
- **Phase 2 Step 1 (`report1.md`):** Added executable contract tests in `test_p2_contract.py` and updated `test_reconcile_ledger.py`.
- **Phase 2 Step 2 (`report2.md`):** Contracted nintent REST ViewSets/serializers and IntentSource GraphQL.
- **Phase 2 Step 3 (`report3.md`):** Updated `nctl` `execute_link_actual_node` to GraphQL snapshot pre-read and refetch confirmation.
- **Phase 2 Step 4 (`report4.md`):** Local tests (227 nintent, 954 nctl) and `git diff --check` passed cleanly.
- **Phase 2 Step 5 (`report5.md`):** Nautobot runtime tests (291/291) passed against disposable database.
- **Phase 2 Step 6 (`report6.md`):** Cross-component non-repetition and GraphQL confirmation proved.
- **Phase 2 Step 7 (`report7.md`):** Documentation updated; zero schema migration required.

## 6. Handoff to Phase 3

Phase 2 is complete (`implemented, not deployed`). The contracted REST API and GraphQL read paths are ready for Phase 3 (Make the nintent human UI read-only).
