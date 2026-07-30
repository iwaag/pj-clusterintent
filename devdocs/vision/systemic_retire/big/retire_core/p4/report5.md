# Phase 4 Step 5 — live acceptance on agfixture

Status: complete.

The operator approved Step 5 and separately approved the single destroying command.

1. The canonical Desired writer atomically updated exactly two records: `agfixture.lifecycle=retired` and its compute instance `desired_presence=absent` (25 unchanged, no create/delete/conflict).
2. Dry operation `01KYRQS6N4X9NV1V71JZAM27BP` planned one destroy pinned to VMID `109` on `aghub`; `--allow-destroy` dry operation `01KYRQS75JW285QVYXX453M5CY` produced the same plan without mutation.
3. Refusal operation `01KYRQS7TWDN6H316EX2PNR9KG` stopped with `destroy_capability_not_enabled`; its sole action was failed and `mutated=false`.
4. Before destruction, SSH with `~/.ssh/ansible_key` and sudo confirmed `pct status 109` was `running` on `aghub`.
5. Enabled operation `01KYRR92T751HFE65AYTCPGPS0` ran the exact planned `status → stop → destroy → status` sequence for VMID `109`; its playbook artifact confirms no other guest was targeted. An immediate read-only `pct status 109` returned rc 2 (`109.conf` absent).
6. That first operation exposed a controller-evidence ownership defect: the delegated `0600` result was root-owned, so nctl could not read it after destruction. The playbook was corrected to write the controller artifact with `become: false` and the correction was conformance-tested/committed (`ansible_agdev 99a3b2c`).
7. A fresh ordinary control-node observation and Nautobot ingest, operation `01KYRRCZRCAQGMB4SAEHG49ZH8`, succeeded. Its round 1 plan had zero actions and state `converged`; it records the linked VM as `proxmox_presence=absent` while retaining the Desired/Actual records.
8. Repeated enabled reconcile, `01KYRREJYGVQKAF84PEE2M0YYS`, planned and executed no destroy (`rounds=[]`). It records `compute_instance_removal_complete`, with Actual `presence=absent`. The existing planner presents that informational finding as `manual_intervention_required`, even though the scoped target summary is `converged=2`; this is a pre-existing presentation/classification behavior, not a repeat actuation.

F8 is now consumed: `agfixture` was the single disposable fixture and was destroyed exactly once. Phase 5 must either use this evidence as its live acceptance evidence or designate another disposable fixture.
