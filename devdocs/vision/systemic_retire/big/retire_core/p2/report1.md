# Retire core Phase 2 — Step 1 nauto rule and tests

Date: 2026-07-30

## Status: complete

Committed nauto `6462ebc`.

- Every validated observed guest is freshness-upserted with `proxmox_presence=present`.
- After a complete platform generation only, the matched Cluster's omitted managed guests are
  marked `absent` and receive that generation's `proxmox_observed_at`.
- The sweep skips unmanaged rows, other clusters, newer guest evidence, and already-absent rows;
  it retains VM, interface, IP, device, status, node, and resource evidence.
- A partial platform never runs the sweep; a sweep error turns the platform result partial.

Focused fake-ORM coverage includes complete omission, retained guest evidence, unmanaged and
different-cluster exclusion, partial evidence, reappearance, and already-absent no-op. The pure
module remains Django-free. `python3 -m unittest discover -s tests` passed 112 tests.
