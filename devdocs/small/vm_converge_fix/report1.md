# Step 1 Report — Two-layer realization documentation

Status: complete.

Updated the current user-facing documentation without changing the VM roadmap contract.

- `nctl/README.md` now states that `Device` is the managed guest-OS/nodeutils realization
  (`DesiredNode.realized_device`) and `VirtualMachine` is the Proxmox compute realization
  (`DesiredComputeInstance.realized_vm`). It explicitly permits both objects for one guest and
  links the detailed VM roadmap.
- `nintent/README.md` now prevents `accepted_actual_types: [virtual_machine]` from being read as
  the guest-OS realization choice for a compute-backed node; that node must select `device`.

No model, schema, ledger, or desired-state row was changed by this step.

