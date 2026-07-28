# P3 Step 6 — Test ownership and manifest

Status: partially complete.

- Repointed all affected executor test monkeypatches to their moved handler
  owners; focused action/executor coverage remains green.
- Updated `forced-observation-refresh` to its precise manifested test ID.
- The full physical module split into `test_reconcile_actions.py` and
  `test_reconcile_ssh_preflight.py` remains for the next step; assertions and
  behavior have not been removed.
- Current matrix results: nctl **970 passed**, compute conformance **1 passed**,
  nintent Django-free **236 passed / 14 expected skips**, nauto **110 passed**,
  nodeutils **54 passed**, Ansible helper **4 passed**, OpenSSH **2 passed**,
  Ansible conformance **1 passed**, privileged helper **1 passed**, and runtime
  reuse gate passed.

