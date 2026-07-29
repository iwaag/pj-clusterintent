# Step 8 Report — Deployed idempotency repair and approved-scope dry plan

Status: ready for separate reconcile-apply approval.

## Deployment and repeat-import proof

The local scratch Nautobot image was rebuilt from the pushed nintent revision
`525057f9964de8bdc19d48cef410ad6fde247dc8` and the canonical nauto revision
`629ae11d277e40808592e3e504c4859916c75101`. `build_info.json` and the in-container canonical
YAML SHA were verified after startup.

The repaired `Import Intent Sources` Job then produced:

| mode | JobResult | totals | result |
|---|---|---|---|
| preview (`apply=false`) | `ed893e07-7795-4206-9d98-671b159490dd` | create=0, update=0, unchanged=27, conflict=0 | no changes |
| repeat apply (`apply=true`) | `0165ab20-398d-4725-8a30-20a78730e843` | create=0, update=0, unchanged=27, conflict=0 | committed, confirmation `confirmed`, no mismatches |

The structured artifacts are private under `.local/vm_converge_fix/step8-import-idempotency/`.

## Fresh drift and reconcile dry plan

Fresh drift was captured in `.local/vm_converge_fix/step8-drift-before.json`; the compute target
remains converged on its already-linked VM. The host-scoped dry-plan operation is
`01KYPX4B17913FXWN4QWFN9DYR`.

Its only automatic actions are:

1. `link_actual_node:agfixture`, targeting DesiredNode
   `198723ec-5ffe-4399-9e17-9ad92a958a12` and the exact existing Device
   `9df7fdd8-f21c-45d5-a0f9-e7d81031131d` (`dcim.device`);
2. one `observe_node` action for `agfixture` to refresh nodeutils evidence.

There is no VirtualMachine node-link candidate and no compute create/start/relink action. The plan
also retains the current manual-review findings `ipam_reconcile_observation_missing` and
`no_realized_object`; these do not authorize an IPAM or guest mutation and must be evaluated from
the post-action fresh drift.

No `nctl reconcile --yes`, direct ledger write, guest mutation, or VM mutation has run in this
step. The next operation is the separately approved host-scoped reconcile apply.
