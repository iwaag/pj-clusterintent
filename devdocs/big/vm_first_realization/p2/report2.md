# Phase 2 — Step 2 report: narrow nintent writer

Status: **complete locally, not deployed**.

Commit `0eae8a0` adds GET/detail-PATCH-only collections for compute platforms
and instances. Each permits exactly its realized relation/source pair, rejects
other mutation keys, and uses model validation for ordered platform-before-VM
linking and identity checks. The fast suite passed: **236 tests, 14 expected
Nautobot skips**. Deployment needs the operator push specified in Step 6.
