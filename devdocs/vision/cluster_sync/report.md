# Cluster sync implementation report

## autolab-meets-cagent Step 1 — 2026-08-09

`agautolab1` was observed and ingested through nctl, linked to its guest-OS
Nautobot Device, and admitted to production composition. The stale desired
node contract was corrected from `accepted_actual_types: [virtual_machine]`
to `[device]`; its Proxmox `DesiredComputeInstance.realized_vm` remains the
separate compute realization.

Successful reconcile operation: `01KZJ057AHF4YRWRG4TTHZJPYW`. A fresh
host-scoped drift reports node and compute instance both converged, with the
node production result `state: included`. Detailed execution notes are in the
episode's `report1.md` in the developer-documentation repository.

## autolab-meets-cagent Step 2 — 2026-08-09

cagent's boundary now permits recoverable desired-state apply and ordinary
reconciliation while hard-denying `--allow-destroy`, `nctl prune`, braindump
purge/review-delete, and direct Proxmox destroy playbooks. The dedicated
OpenCode process was restarted with the rendered policy.

Human-entrance request `req_9fdce08de7f949c68457b94736d99a32`
successfully committed a 43-operation all-unchanged desired-state re-apply.
Request `req_3962255e3059434091a04bf3c62f19b8` attempted a non-mutating
`--allow-destroy` dry plan and matched the hard deny before execution. Fresh
desired and PostgreSQL backups were taken first; cagent's 92 tests pass.
