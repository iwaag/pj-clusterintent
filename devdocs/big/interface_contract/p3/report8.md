# Interface Contract Phase 3 — Step 8 Report: Disposable Nautobot Runtime UI Proof

**Date:** 2026-07-26  
**Status:** Complete  

---

> [!WARNING]
> **Correction (Interface Contract Phase 4, dated 2026-07-26):** Phase 4's planning-time audit
> (`p4/plan.md` Section 2) re-ran a fresh isolated Nautobot 3.1.3 disposable suite against the
> exact checked-out nintent source and found **9 failures and 6 errors** across
> `test_ui_contract`, `test_braindump`, and `test_api_contract` — the complete pass this report
> claims below is not reproducible from current source. In particular, the "permission
> enforcement" and "UI non-mutation" claims in Section 1.2-1.3 below rested on a suite that
> granted only two of the eleven models' `view_*` permissions and did not snapshot full row
> fingerprints; the "11 retained `ObjectListView`/`ObjectView` classes render" claim did not
> exercise all eleven fixture/render pairs. This report's original text is kept below as
> historical evidence of what was executed at the time; Phase 4 Step 1/2 repair and re-prove
> these gates with a fresh, reproducible disposable run, recorded in
> `p4/report1.md`/`p4/report2.md`.

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
