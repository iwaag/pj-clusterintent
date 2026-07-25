# Phase 2 Step 5 — Disposable Nautobot API and GraphQL proof

Parent: [plan.md](plan.md) — Step 5.

This step runs the full Nautobot-runtime integration test suite against a disposable test environment to prove API route behaviors, HTTP status codes, method restrictions, and GraphQL model feature registration.

## 1. Work and Proof Completed

### Migration State & Model Checks
- Executed `makemigrations nautobot_intent_catalog --check --dry-run` inside the Nautobot container: reported `No changes detected in app 'nautobot_intent_catalog'`.

### Nautobot Runtime Integration Test Results
- Ran `nautobot-server test nautobot_intent_catalog.tests` against a disposable test database (`test_nautobot`):
  - **291 tests executed, 291 passed, 0 failures, 0 errors in 4.121s.**
- Verified specific contract conditions within the runtime suite:
  - **GraphQL Feature Registration:** Verified `registry['model_features']['graphql']['nautobot_intent_catalog']` excludes `intentsource` while retaining all 11 other models (`desirednode`, `desiredendpoint`, `desirediprange`, `desirednodeoperationaloverride`, `desiredservice`, `desireddependency`, `desiredserviceplacement`, `desiredcomputeplatform`, `desiredcomputeinstance`, `braindumpdocument`, `alignmentreview`).
  - **Removed REST Collections:** Confirmed `/api/plugins/intent-catalog/services/`, `endpoints/`, `compute-platforms/`, and `compute-instances/` return `404 Not Found`.
  - **Disallowed Methods:** Confirmed POST to `/api/plugins/intent-catalog/nodes/` returns `405 Method Not Allowed`.
  - **Retained Operations:** Confirmed GET on `/api/plugins/intent-catalog/nodes/` and PATCH of `lifecycle` return `200 OK` with explicit fields.

## 2. Gate Status

Step 5 gate passed cleanly with full runtime proof against a disposable database. Proceeding to Step 6.
