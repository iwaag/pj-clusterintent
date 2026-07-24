# Step 4 — Unambiguous agdnsmasq mapping

Status: complete.

Synthesizes Step 2 (live Proxmox evidence) and Step 3 (live Nautobot evidence). Join key is not
`name == agdnsmasq` alone: platform scope (single-node cluster `aghub-proxmox`), guest kind
(`lxc`), VMID (`108`), and normalized MAC (`bc:24:11:23:dc:b7`) all agree with the existing
Nautobot Device and DesiredEndpoint records for `agdnsmasq`.

## Frozen mapping row

```text
DesiredNode agdnsmasq (id 27818c12-fe15-4c9f-83d0-7949523f6c33)
  -> proposed DesiredComputePlatform: slug "aghub-pve", control_node=aghub,
     config.cluster_name="aghub-proxmox" (derived uniquely: single-node cluster, node_count=1)
  -> observed Nautobot Cluster candidate: NONE YET (0 Cluster rows live; platform creation in
     Phase 3 will create Cluster via ingest, not by hand)
  -> proposed DesiredComputeInstance: instance_kind=container, vcpus=1, memory_mb=512,
     root_disk_gb=8 (from config_rootfs "local-lvm:vm-108-disk-0,size=8G", NOT from disk_gb=7.78)
  -> observed Proxmox node + guest_type + VMID: aghub / lxc / 108
  -> observed Nautobot VirtualMachine candidate: NONE YET (0 VM rows live; created by Phase 2
     ingest from this same observation)
  -> one primary DesiredEndpoint: id 27818c12-fe15-4c9f-83d0-7949523f6c33,
     ip_address=192.168.0.2, mdns_name=agdnsmasq.local, dns_name=agdnsmasq.home.arpa
  -> desired/proposed MAC + observed config MAC: bc:24:11:23:dc:b7 (observed only; not yet
     desired state — labeled "operator confirmation required" per plan §Step4)
  -> effective bridge: vmbr0 (instance override none; would come from platform
     default_bridge="vmbr0", derivable uniquely from this guest's only NIC)
  -> derived NIC slot: net0 (execution mechanism, not stored as intent)
```

The `DesiredNode` id `27818c12-fe15-4c9f-83d0-7949523f6c33` (re-confirmed directly against the
saved Step 3 evidence) is distinct from the Device id
`36178882-1229-4aa1-9e50-faa7cb41188d` (`realized_device`) — the two-layer identity the roadmap
describes: one logical `DesiredNode`/guest-OS identity, one Device-level actual link, and (once
Phase 3 exists) one separate compute-instance actual link.

## Ambiguity check

- Endpoint candidates for `agdnsmasq`: exactly 1 (`primary`, MAC-bearing NIC via observed config).
  Zero or multiple would have unmet the exit criterion; neither occurred.
- Guest candidates: exactly 1 LXC named `agdnsmasq`, VMID `108`, on the only node (`aghub`) in the
  only cluster (`aghub-proxmox`). No duplicate VMID, no duplicate name, no cross-cluster ambiguity
  (single-node cluster).
- MAC uniqueness: `bc:24:11:23:dc:b7` appears exactly once across all 9 observed guests (Step 2
  data); no collision with any other guest's configured or agent-reported MAC.
- Cluster membership: unambiguous because there is exactly one Proxmox node/cluster in this
  environment; Phase 2 must still implement matching by stable Cluster identity rather than
  hard-coding this single-cluster assumption.

## Disposable LXC fixture (forward check only)

The plan requires the same rule applied to the Phase 5 disposable-LXC fixture's endpoint. No
fixture exists yet (out of scope for Phase 1 to create). The enumerable requirement is recorded so
Phase 5 cannot skip it: a disposable-LXC creation needs its own dedicated `DesiredNode`,
exactly one `primary` `DesiredEndpoint` with a canonical desired MAC and non-empty `mdns_name`
(none of which may reuse `agdnsmasq`'s), a free VMID, and a template reference confirmed to exist
via the Phase 2 storage-content path (still unverified, per Step 2 §6).

## Gate evaluation

One unambiguous platform/instance/NIC mapping row is frozen; zero or multiple candidates would
have blocked this step, and neither occurred. Step 4 gate passed.

## Discrepancies

None affecting the mapping. Noted a labeling slip during drafting (endpoint id vs. node id) and
corrected it in this same report rather than re-querying — no live state was touched.
