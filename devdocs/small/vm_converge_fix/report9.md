# Step 9 Report — Exact-scope convergence apply and verification

Status: complete.

After separate approval of the Step 8 dry plan, the supported command

```text
nctl reconcile agfixture --yes --json
```

completed as operation `01KYPXGNNG5J1Z2QQ4N02NDR71` with state `converged`, no errors, and
`scope_summary: {converged: 2}`. Durable public operation evidence is under
`~/.local/state/nctl/events/01KYPXGNNG5J1Z2QQ4N02NDR71/`; the sanitized command envelope is
retained privately at `.local/vm_converge_fix/step9-reconcile-apply.json`.

## Positive execution evidence

| round | action | result |
|---|---|---|
| 0 | `link_actual_node:agfixture` | linked DesiredNode `198723ec-5ffe-4399-9e17-9ad92a958a12` to existing Device `9df7fdd8-f21c-45d5-a0f9-e7d81031131d` as `realized_device`, source `derived` |
| 0 | `observe_node` | one successful nodeutils collection/ingest for `agfixture`, pinned nodeutils `775ed7fad5110a96186a737147b87d3bf450ced2`, ingest outcome `updated` |
| 1 | `reconcile_ipam:agfixture` | scoped primary endpoint `fb5222a2-e419-475d-822c-5fc3b490ab98` applied with no conflicts, skips, or unresolved endpoints |

The operation did not run a guest create/start/relink action. There was exactly one `observe_node`
collection; no repeated forced observation occurred.

## Independent final verification

A fresh independent `nctl drift --host agfixture --json` is successful and reports exactly two
converged targets:

- node: converged, with only informational `intent_effect_summary`;
- compute instance: converged, with only informational `compute_realization_summary`.

The verified separate links are:

```text
DesiredNode.agfixture.realized_device
  = 9df7fdd8-f21c-45d5-a0f9-e7d81031131d  (Device)

DesiredComputeInstance.agfixture.realized_vm
  = 3a6aa5b1-f128-4d23-82f7-9c97acff3a68  (VirtualMachine, VMID 109)
```

`waiting_for_manual_initial_access`, `actual_node_not_linked`, `no_realized_device`, and
`no_realized_object` are absent from final host-scoped drift. The Device and VirtualMachine remain
independent realization layers; neither existing object was deleted, recreated, or replaced.
