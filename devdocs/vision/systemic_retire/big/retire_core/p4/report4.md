# Phase 4 Step 4 — surface-test inversion

Status: complete.

Replaced Phase 3's inert-capability assertions with positive contracts: the destroy handler is registered, the CLI exposes `--allow-destroy`, the bounded playbook exists, and the creation playbook remains free of destroy verbs. The durable reconcile-data field contract was updated for `allow_destroy`.

Focused validation passed (59 tests across executor/destroy/surface/conformance), followed by the full nctl suite (1005 passed), compute conformance (1 passed), and Ansible conformance (3 passed).
