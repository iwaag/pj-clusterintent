# P3 Step 6 — Test ownership and manifest

Status: partially complete.

- Repointed all affected executor test monkeypatches to their moved handler
  owners; focused action/executor coverage remains green.
- Updated `forced-observation-refresh` to its precise manifested test ID.
- Moved the playbook timestamp-propagation contract to
  `test_reconcile_actions.py`, the direct shared scan-error contract to
  `test_reconcile_ssh_preflight.py`, and the two public Ansible-helper cases
  out of `test_dnsmasq_apply.py`. All moved assertions are unchanged.
- The IPAM action-result matrix and the direct action-boundary evidence cases
  still reside in `test_reconcile_executor.py`; the full physical ownership
  split required by Step 6 is therefore not complete. This report deliberately
  retains `partially complete` rather than treating a green suite as proof of
  that structural criterion.
- Current matrix results: nctl **970 passed**, compute conformance **1 passed**,
  nintent Django-free **236 passed / 14 expected skips**, nauto **110 passed**,
  nodeutils **54 passed**, Ansible helper **4 passed**, OpenSSH **2 passed**,
  Ansible conformance **1 passed**, privileged helper **1 passed**, and runtime
  reuse gate passed.
