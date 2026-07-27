# P0 Step 11 — behavior-preservation baseline

Status: blocked.

- Passed baseline gates: nctl 967/967; nintent 227 tests with the expected 14 skips; nauto 110/110; nodeutils 54/54; Ansible helper 4/4; OpenSSH conformance 2/2; Ansible conformance 1/1; privileged-helper integration 1/1.
- Both Nautobot runtime modes stop after the runtime source-path check with `No changes detected` and non-zero status. The runtime measurement repeats the same failure. Logs are retained as `runtime-keepdb.log`, `runtime-clean.log`, and `measurement-runtime.log`.
- Read-only `nctl render dnsmasq` cannot capture bytes: GraphQL returns `nautobot_fetch_failed` because its Redis connection to `host.docker.internal:6379` is reset. `hosts-intent` and `production` artifacts were rendered into the phase-owned directory and hashed; their bytes are retained.
- This is a truthful pre-existing baseline/environment failure, not repaired in P0. Recovering Redis/Nautobot or altering the runtime gate would require a prohibited restart/rebuild or a separate bounded decision. The complete deterministic-artifact baseline therefore cannot be captured safely.
