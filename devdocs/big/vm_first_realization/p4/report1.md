# Phase 4 Step 1 Report

Status: **complete**.

Added Tier A coverage for the create handler: exact pinned `ansible-playbook --limit aghub --extra-vars` invocation, pre-run parameter-drift refusal, and every result-file failure form (missing, malformed, incomplete, or untruthful) preserving `mutated=true`. The full nctl ordinary suite is now **1004 passed** (from Phase 3's 990 baseline).

The static contract also rejects stop, destroy, set, resize, migrate, clone, and qm paths in the bounded create playbook.
