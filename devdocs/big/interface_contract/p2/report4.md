# Phase 2 Step 4 — Local and static verification

Parent: [plan.md](plan.md) — Step 4.

This step runs local test suites, static checks, diff checks, and query digest validations to ensure clean code quality and contract compliance before disposable container testing.

## 1. Static Verification Results

- **`nintent` Unit Tests:** 227 tests collected, 222 passed, 5 skipped (`cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests`).
- **`nctl` Test Suite:** 954 passed in 6.18s (`cd nctl && uv run pytest`).
- **`git diff --check`:** Clean across superproject, `nintent`, and `nctl`.
- **GraphQL Digests:** All 4 pinned query digests match Phase 0 report7 values (`DESIRED_QUERY`: `e6e34a9f...`, `ACTUAL_QUERY`: `f2b88084...`, `LIST_QUERY`: `e276ec2a...`, `SHOW_QUERY`: `003a5ffe...`).
- **REST Registration:** Exactly 3 router registrations in `nintent/nautobot_intent_catalog/api/urls.py` (`nodes`, `braindumps`, `alignment-reviews`).
- **Serializer Contracts:** Zero occurrences of `fields = "__all__"` in active `nintent` REST serializers.
- **`rest_get` Classification:** 0 domain-object REST GET callers in `nctl/src/`. Exactly 4 protocol/method occurrences remain.
- **Schema & Model Integrity:** No database migration files generated or modified; model fields and Django migration history remain through `0016`.

## 2. Gate Status

Step 4 gate passed cleanly. Proceeding to Step 5 (Disposable Nautobot API and GraphQL proof).
