# Retire core Phase 2 — Step 3 nctl read and evidence

Date: 2026-07-30

## Status: complete

Committed nctl `13ae1cd`.

- `ProxmoxVirtualMachineFacts.presence` reads only `proxmox_presence`; an untouched VM therefore
  reads `None`, and unrelated custom fields remain excluded.
- `compute_realization_summary.actual.presence` exposes the value as ordinary evidence only.
- No compute matcher, drift code, severity, classification, plan, action, or CLI option changed.
  In particular, an `absent` VM continues to match as a realization until Phase 3.

`uv run pytest -q --durations=20` passed 990 nctl tests, including typed projection and summary
coverage.
