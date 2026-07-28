# P5 Step 5 — Full matrix, manifest, and measurements

Status: blocked.

Passed before the runtime stop:

- nctl ordinary: **976 passed**; compute conformance: **1 passed**.
- nintent Django-free: **236 run, 14 skipped**; nauto: **110 run**; nodeutils: **54 passed**; Ansible helper: **4 run**.
- OpenSSH conformance: **2 passed**; Ansible conformance: **1 passed**; privileged-helper integration: **1 passed**.
- The eleven nctl-owned named boundary proofs were invoked individually and passed: dnsmasq convergence, non-DHCP IPAM convergence, host scope, dry plan, partial IPAM progress, forced observation refresh, desired-MAC safe stop, compute inertness, deterministic rendering, unmanaged no-delete, and operation-evidence reader.

The runtime wrapper's unlabelled `--keepdb` and `--clean` invocations completed their source-staging and migration checks but did not provide a test case count. A directly named `post-mutation-evidence` runtime proof then exposed the actual blocker: the test-owned `test_nautobot` database cannot be created from the local Nautobot migration set. It first failed on an already-existing `virtualization_vminterface.role_id`; after the permitted `--clean` retry, it failed on already-existing `dcim_interface.vrf_id`. This is local scratch test-DB migration state, not a P5 source change, but it prevents the required runtime cases (including `post-mutation-evidence` and `prose-authority`), mechanical full-MANIFEST execution, final measurements, and final artifact verdict from being truthfully completed.

No source, deployment, or external target was changed while diagnosing this gate. Step 6 must not start until the runtime test-DB setup has a user-approved recovery path.

