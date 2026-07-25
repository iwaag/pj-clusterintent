# Phase 2 Step 2 — Contract nintent REST and IntentSource GraphQL

Parent: [plan.md](plan.md) — Step 2.

This step contracts nintent's REST API to the three retained mutation collections and removes GraphQL exposure from `IntentSource`.

## 1. Work Completed

### `nintent` Model & GraphQL
- Removed `@extras_features("graphql")` decorator from `IntentSource` in `nautobot_intent_catalog/models.py`.
- Retained `@extras_features("graphql")` on all 11 consumer-backed models.

### REST Serializers (`api/serializers.py`)
- Deleted `DesiredServiceSerializer`, `DesiredEndpointSerializer`, `DesiredComputePlatformSerializer`, and `DesiredComputeInstanceSerializer`.
- Replaced `fields = "__all__"` with explicit field tuples across all retained serializers:
  - `DesiredNodeSerializer`: fields `("id", "name", "slug", "node_type", "lifecycle", "role", "realized_device", "realized_device_source", "created", "last_updated")`; read-only fields `("id", "name", "slug", "node_type", "role", "created", "last_updated")`; writable fields `("lifecycle", "realized_device", "realized_device_source")`.
  - `BrainDumpDocumentSerializer`: fields `("id", "title", "body", "authorship", "created", "last_updated")`; read-only fields `("id", "created", "last_updated")`; writable fields `("title", "body", "authorship")`.
  - `AlignmentReviewSerializer`: fields `("id", "braindump", "summary", "created", "last_updated")`; read-only fields `("id", "created", "last_updated")`; create writable `("braindump", "summary")`; PATCH writable `("summary",)`.
- Implemented strict `_check_allowed_mutation_keys` validation: mutation requests supplying unknown, system, or read-only keys are rejected deterministically with 400 Bad Request.

### REST ViewSets & Router (`api/views.py`, `api/urls.py`)
- Deleted `DesiredServiceViewSet`, `DesiredEndpointViewSet`, `DesiredComputePlatformViewSet`, and `DesiredComputeInstanceViewSet`.
- Removed their four router registrations from `api/urls.py` (`services`, `endpoints`, `compute-platforms`, `compute-instances`).
- Explicitly restricted HTTP methods on retained ViewSets:
  - `DesiredNodeViewSet`: `http_method_names = ["get", "patch", "head", "options"]`; POST, PUT, DELETE, bulk PATCH, bulk DELETE return 405 Method Not Allowed.
  - `BrainDumpDocumentViewSet` & `AlignmentReviewViewSet`: `http_method_names = ["get", "post", "patch", "delete", "head", "options"]`; PUT, bulk PATCH, bulk DELETE return 405 Method Not Allowed.

## 2. Test Verification

- **`nintent` Unit Tests:** 227 tests collected, 222 passed, 5 skipped (Django/Nautobot runtime guarded).
- **Static Contract Assertions (`test_p2_contract.py`):** Verified absence of deleted serializers/ViewSets, absence of `fields = "__all__"`, and removal of GraphQL registration on `IntentSource`.

## 3. Gate Status

Step 2 gate passed cleanly. Restructured REST ViewSets/serializers and GraphQL exposure are in place. Proceeding to Step 3.
