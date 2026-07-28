# P3 Step 8 — Boundary proofs and full matrix

Status: partially complete.

- All offline required gates passed: nctl **970 passed**, compute conformance
  **1 passed**, nintent Django-free **236 passed / 14 expected skips**, nauto
  **110 passed**, nodeutils **54 passed**, Ansible helper **4 passed**, OpenSSH
  conformance **2 passed**, Ansible conformance **1 passed**, and privileged
  helper integration **1 passed**.
- The Nautobot runtime `--keepdb` gate did not reach application tests. During
  test database setup PostgreSQL raised `duplicate key value violates unique
  constraint "pg_type_typname_nsp_index"` for `dcim_module`; the staged source
  revisions and `makemigrations --check --dry-run` both completed first.
- `--clean` was run to recreate only the test-owned `test_nautobot` database,
  then `--keepdb` was retried. In this environment both attempts stop after
  migration checking before producing the runtime test result. This is outside
  the Phase 3 diff and prevents the two required runtime proofs from being
  claimed.

The phase stops here under the plan's runtime-gate stop condition. Steps 9–10
and the final report must wait for a healthy local runtime gate; no completion
state is inferred from the offline green matrix.
