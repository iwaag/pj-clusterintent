# P0 Step 11 — behavior-preservation baseline

Status: blocked.

Recovery attempt (user-authorized): `service_scripts-redis-1` answered `PONG`; the three local
Nautobot services were restarted and became healthy. HTTP thereafter returned `302`, and the
read-only dnsmasq render succeeded (5 DNS records, 4 DHCP reservations, 1 range; bytes retained
at `artifacts/render/dnsmasq-records.conf`). No desired/actual data, real node, or Proxmox state
was changed.

- Passed baseline gates: nctl 967/967; nintent 227 tests with the expected 14 skips; nauto 110/110; nodeutils 54/54; Ansible helper 4/4; OpenSSH conformance 2/2; Ansible conformance 1/1; privileged-helper integration 1/1.
- Both Nautobot runtime modes still cannot complete: after staging the exact sources and passing `makemigrations --check --dry-run` (`No changes detected`), the detached test runner never leaves its required `test-exit-status` file. A direct process check shows its runner has exited. The runtime measurement has the same gate result. Logs are retained as `runtime-keepdb*.log`, `runtime-clean.log`, `runtime-debug.log`, and `measurement-runtime.log`.
- The Redis connection-reset baseline failure is repaired. The remaining blocker is the runtime-gate harness's detached-runner/result-file protocol. Altering that tracked gate is outside P0's documentation-only authority; the complete root matrix cannot be truthfully captured until a separately authorized gate repair is made.
