# P0 Step 11 — behavior-preservation baseline

Status: partially complete.

Recovery attempt (user-authorized): `service_scripts-redis-1` answered `PONG`; the three local
Nautobot services were restarted and became healthy. HTTP thereafter returned `302`, and the
read-only dnsmasq render succeeded (5 DNS records, 4 DHCP reservations, 1 range; bytes retained
at `artifacts/render/dnsmasq-records.conf`). No desired/actual data, real node, or Proxmox state
was changed.

- Passed baseline gates: nctl 967/967; nintent 227 tests with the expected 14 skips; nauto 110/110; nodeutils 54/54; Ansible helper 4/4; OpenSSH conformance 2/2; Ansible conformance 1/1; privileged-helper integration 1/1.
- User-authorized repair replaced the detached runner with synchronous status/output collection. `--clean` passed 290 tests in 51.838 s and `--keepdb` passed 290 tests in 47.366 s; both emitted only six existing RawSQL `models.W045` warnings. The repair is commit `8950837`.
- The Redis connection-reset baseline failure is repaired and dnsmasq bytes are retained. The runtime measurement entry point is still pending rerun, so this step is partially complete rather than complete.
