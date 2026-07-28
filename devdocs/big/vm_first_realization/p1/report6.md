# Phase 1 — Step 6 report: verification

Status: **complete**.

- `nctl` ordinary suite: **988 passed**.
- Compute conformance gate: **1 passed**.
- Focused compute evaluator/classification/module-boundary tests: **43 passed**.
- Live `nctl drift --host agdnsmasq` showed two distinct targets: `node` is `unknown` from stale
  guest-OS evidence; `compute_instance` is matched at VMID 108 with `match_basis=vmid` and only
  non-informational `compute_instance_not_linked`.
- Cluster dry plan `01KYMCGTXFN1VJYTGRV9A12XBG` and host dry plan
  `01KYMCGVET7V252B6J5M148XDT` each had zero compute actions; neither made a Proxmox call.
- dnsmasq render digest remains p0's `305e17dc3be75f208eb18728b16fb8e44e8a28389504727cb6580dc1d71bb9a1`.

The Nautobot runtime gate was not needed: nintent/nauto runtime behavior was unchanged; this
phase used the existing Import Job only to apply the approved seed. Phase 0 remains blocked only
on the unrelated, operator-confirmed new-guest fixture record.
