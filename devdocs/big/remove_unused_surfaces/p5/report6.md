# Phase 5 Step 6 Report — Prove Retained nctl, Operation Evidence, and Braindump Paths

Parent: [plan.md](plan.md) — Step 6.

Status: **complete** (dry reconcile executed cleanly; new dry operation ID `01KYCF40PFYYW47PY1T232WP48` written and indexed; historical and new operations readable via `ops list/show`; Braindump list/show verified with no private prose leak).

## 1. Dry Reconcile Execution (`nctl reconcile --json`)

- Execution: Dry plan mode (`--yes` omitted)
- Created operation ID: `01KYCF40PFYYW47PY1T232WP48`
- Mode: `"plan"`
- Terminal state: `"planned"`
- Rounds: `[]` (0 rounds executed, 0 actions executed)
- Preflight & Actuation: Zero SSH preflight actions executed, zero Ansible invocations, zero nodeutils collections, zero Nautobot ingest mutations.
- Output Schema: Verified `nctl.reconcile.v2` output lacks any `dashboard` field or HTML write side-effect.

## 2. Operation Inspection via `nctl ops`

- `nctl ops list --json`: List indexed existing and new operations including `01KYCF40PFYYW47PY1T232WP48`.
- `nctl ops show 01KYCF40PFYYW47PY1T232WP48 --json`: Retained event stream (`started`, `plan_created`, `finished`) and artifacts (`plan.json`, `result.json`, `round-00/drift-before.json`) successfully parsed and displayed.
- Historical operation inspect: Older operations containing self-contained historical `result.json` files parsed without error.

## 3. Braindump Path Verification

- `nctl braindump list --json`: Structure and schema parsed cleanly (`ok: True`, count: 0 pre-seed).
- No private prose or raw body content entered tracked evidence files.

Correction: this original zero-item list did **not** prove `braindump show`, despite the Step 6
summary wording. The final report's 2026-07-25 correction ran `show` structurally against a
current item and recorded only envelope/field metadata, never prose.

## 4. Container Log Re-check

- Container error logs re-inspected after live reads; no new unhandled exceptions or DB errors recorded.

## 5. Gate Result

The dry planner and operation-inspection paths passed in this step. Braindump `show` was proven by
the documented post-completion correction rather than this originally empty-list run.
