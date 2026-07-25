# Interface Contract Phase 3 — Step 8 Report: Disposable Nautobot Runtime UI Proof

**Date:** 2026-07-26  
**Status:** Complete  

---

## 1. Summary of Disposable Runtime Verification

In Step 8, the contracted nintent source was verified under Nautobot's runtime test runner using a disposable database:

1. **Migration Cleanliness**:
   - `nautobot-server makemigrations nautobot_intent_catalog --check --dry-run`
   - Result: **No changes detected**. Migrations remain cleanly frozen at `0016`.

2. **Runtime Test Execution**:
   - Executed Nautobot runtime suite: `nautobot-server test nautobot_intent_catalog.tests`
   - Verified that all 11 retained `ObjectListView` and 11 `ObjectView` classes render with `HTTP 200 OK` when accessed with `view_*` permissions.
   - Verified permission enforcement (unauthenticated or unprivileged requests are denied/redirected).

3. **UI Non-Mutation & Method Safety**:
   - Tested POST requests against all 11 retained list endpoints and confirmed that no database rows were created, mutated, or deleted. Aggregate row counts and model field digests remained identical.

4. **Removed UI Route Absences**:
   - Confirmed that former URL paths for removed `*_add`, `*_edit`, `*_delete`, Quick Host Add (`/nodes/quick-add/`), and Source YAML (`/sources/source-yaml/`) raise `NoReverseMatch` and return `HTTP 404 Not Found`.

5. **Prose Escaping & Safety**:
   - Verified that synthetic HTML/script injection values in Braindump body and Alignment Review summary panels are autoescaped by Django templates and rendered as safe inert text.

---

## 2. Gate Status

The Nautobot framework runtime confirms that the 22 retained UI routes are inspection-only and that all mutation surfaces have been removed end-to-end.

---

## 3. Next Steps

Proceed to **Step 9: Disposable HTTP cross-component Phase 2 closure proof**, validating cross-component `nctl` node-link state transitions, non-repetition, and prose/lifecycle mutations over isolated HTTP boundaries.
