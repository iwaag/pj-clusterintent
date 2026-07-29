# Step 3 Report — Executable node-link planning

Status: complete.

`nctl` now shares `NODE_LINK_CANDIDATE_FIELD_BY_OBJECT_TYPE` between planner and ledger executor.
The only automatic `DesiredNode` link type is `dcim.device -> realized_device`.

When evaluation finds a unique `virtualization.virtualmachine`, planning emits bounded manual-review
evidence instead of a `link_actual_node` action. The explanation names
`DesiredComputeInstance.realized_vm` as the correct compute link. The executor's existing
fail-closed unsupported-type validation remains in place as defense in depth.

Added a planner regression test proving a VM-only candidate produces no automatic node-link action.
The existing device-action and executor rejection coverage remains part of the focused suite.

