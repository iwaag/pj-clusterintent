# P3 Step 1 — Audit and frozen dispositions

Status: complete.

Private evidence: `.local/nctl-modularization/p3/20260728T013700Z/`.

- Re-verified all Section 4.3 findings. The executor dispatches by
  `reconciler_id`; its sole `action_kind` equality is the dnsmasq split in
  `_run_playbook_action`. The roadmap has been corrected accordingly.
- `new_node_baseline` is registered identity metadata only: no classifier or
  planner produces it and the executor has no branch. The Phase 0 action-seam
  evidence now records that it deliberately receives no handler and retains
  the service-default unknown-reconciler failure.
- The audit records every leaving symbol and explicit executor keep, the six-row
  handler table, all 75 executor-test `monkeypatch.setattr` sites, direct
  private-symbol consumers, duplicate scan/alias policy, required-search
  classification, test split, and manifest impact. No patch has an intended
  coverage change; profile loading remains in the executor because existing
  patches must continue to cover both plan construction and regeneration.
- The handler table admits five current action implementations. It records
  `phase` and `needs_client` separately so the bootstrap/service partition and
  shared-client lifetime are reproduced without a second reconciler registry.
- The independent-reason test supports extracting `render_reconcile_text` as a
  presentation module in Step 7; it has a single CLI consumer and makes no
  round decision.
- A planning fact was refuted: the nintent runtime file has **one** direct
  `_execute_action` invocation (line 330) plus its import (line 32), not two
  invocations. The plan now states the exact bounded change. The owning test
  begins at line 309; no other nintent code needs to change.

No production or test behavior changed in this step. The user explicitly
approved the Section 3.4 test-only import/invocation repoint on 2026-07-28;
Step 3 may now make exactly that bounded nintent change, with no image rebuild
or push.
