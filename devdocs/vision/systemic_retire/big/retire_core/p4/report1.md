# Phase 4 Step 1 — permission plumbing and refusal

Status: complete.

- Added `nctl reconcile --allow-destroy`, defaulting to false and recorded as `ReconcileData.allow_destroy` operation evidence.
- Threaded the capability only into apply-round execution. Plan mode remains structurally non-mutating regardless of the option.
- A planned `destroy_compute_instance` now stops before dispatch unless the capability is enabled, records a non-mutating failed action, and terminates with `destroy_capability_not_enabled` plus the `--allow-destroy --yes` remediation.
- Added `destroy_compute_instance` to the SSH-required reconciler set. The known pre-existing asymmetry remains: `create_compute_instance` is still absent from that set (F6), intentionally outside this phase.
- Added focused executor tests for terminal refusal/no dispatch and explicit-capability dispatch.

Validation: focused executor and surface tests passed; the complete nctl suite later passed 1005 tests.
