# Phase 2 — Step 4 report: action handler

Status: **complete locally**.

The handler re-derives and compares the plan-pinned candidate before writing.
Its ledger writer PATCHes platform then instance through the canonical API,
refetches both rows through GraphQL, refuses replacement links, and preserves
`mutated=true` after any successful PATCH if later confirmation fails. No
Proxmox client or mutation path was added.
