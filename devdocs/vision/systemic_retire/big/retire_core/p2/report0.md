# Retire core Phase 2 — Step 0 baseline

Date: 2026-07-30

## Status: complete

- Superproject baseline: `22bde35`; submodules: nauto `3bd1820`, nctl `49f4355`, nintent
  `7c88023`, nodeutils `775ed7f`, ansible `aa8f9f4`.
- Scratch Nautobot was healthy and its `/opt/nautobot/build_info.json` recorded nauto `3bd1820`
  and nintent `7c88023`.
- Cluster `aghub-proxmox` was `proxmox_observation_state=complete`. Its ten known VMs (including
  `agfixture`) all had `proxmox_observed_at=2026-07-28T15:02:26+00:00` and no
  `proxmox_presence` key.
- `nctl drift --json` baseline summary was `drifting=2`, `converged=9`, `unknown=4`; agfixture's
  compute realization summary had no actual presence field.

No write was performed in this step.
