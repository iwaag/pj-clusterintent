# P0 Step 6 — compute-contract owner

Status: complete.

- Selected owner/mechanism: nintent-owned semantics with generated conformance fixtures consumed by an ordinary nctl test; this avoids both runtime shared-package coupling and a new persisted wire contract.
- Rejected candidates and their deployment cost are recorded in `contract-decision.md`.
- Surviving predicate: `is_actionable_lifecycle`; nctl's alternate spelling is removed in Phase 1. nctl retains only current-read/actuation-time endpoint selection and integrity safety checks.
- Phase 1 necessarily changes nintent and therefore requires a user-owned push, no-cache Nautobot rebuild, exact build-log revision check, and runtime-gate rerun. Valid compute remains inert throughout.
