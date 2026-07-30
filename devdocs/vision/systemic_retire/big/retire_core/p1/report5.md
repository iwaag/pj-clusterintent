# Retire core Phase 1 — Step 5 gates

Date: 2026-07-30

## Gates

| gate | result |
|---|---|
| nintent Django-free | 127 run, 10 Nautobot/file-location skips, pass |
| compute conformance | 1 passed |
| nctl ordinary | 989 passed in 6.52s |
| Nautobot runtime clean | 181 passed in 4.638s; `cases=181` |

The clean runtime gate used exact staged local source revisions nintent `7c88023`, nctl `49f4355`,
nauto `3bd1820`, and nodeutils `775ed7`. It recreated only `test_nautobot`, passed
`makemigrations --check --dry-run`, and preserved the coherent test-owned database after the
successful run.

The nintent Django-free count is now 10 expected skips, not the stale 14 in the prior command
matrix and Phase 1 plan. The command matrix has been corrected to the observed, explicit current
count. This is a gate-documentation correction only; no skip was silently introduced.

## Status

**complete** — all Phase 1 required automated gates passed.
