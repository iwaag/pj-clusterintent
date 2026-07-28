# P4 Step 8 — Re-proof and measurement

Status: partially complete.

- Re-captured renders and envelopes. The dnsmasq content digest remained `ac1f19a564bc1342d97741d4b2b9525b3259f78fb37bf997d7ee29c200ae99ec`; hosts-intent and production diffs contain only their declared generated timestamp, generation ID, and generation-dependent report-path fields.
- Named manifest proofs all passed: `dnsmasq-convergence`, `non-dhcp-ipam-convergence`, `desired-mac-safe-stop`, `compute-inert`, `deterministic-rendering`, `unmanaged-no-delete`, `reconcile-host-scope`, `reconcile-dry-plan`, and `operation-evidence-reader`.
- Offline matrix passed: nctl **973**, compute conformance **1**, nintent Django-free **236 / 14 expected skips**, nauto **110**, nodeutils **54**, Ansible helper **4**, OpenSSH conformance **2**, Ansible conformance **1**, and privileged-helper integration **1**.
- Measurement after: nctl has 166 tracked Python files, 17,458 non-test lines, 77 test files, and 973 collected cases. The three additional cases are the pure-drift boundary parameterizations.
- Runtime `--keepdb` reached 299 tests but failed 49 UI cases after its test database disappeared (`OperationalError: database "test_nautobot" does not exist`). The `--clean` attempt completed staging/migration checking and database cleanup but did not produce application-test results. This is environmental/runtime-gate evidence, not a substituted pass.
- Manifest rows still point to existing named tests; `deterministic-rendering` was updated with its canonical owner.
