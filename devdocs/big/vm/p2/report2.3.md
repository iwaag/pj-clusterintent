# Step 3 — Add Nautobot prerequisites and strict ingest parsing

Status: `complete` for local code/tests. The seed job's dry run against the live Nautobot
instance is deferred to Step 8 (Section 3.3 requires separate approval for that live action).

## 1. Seed prerequisite extensions

`nauto/seed/home_cluster.yaml`:

- `cluster_types: [{name: "Proxmox VE", slug: proxmox-ve}]`.
- Two new VM roles: `virtual-machine`, `lxc-container` (content type
  `virtualization.virtualmachine`).
- Extended the existing `Active` status to also apply to
  `virtualization.virtualmachine` (in addition to its current `dcim.device`/`dcim.location`
  scope), and added new `Offline` and `Unknown` statuses scoped to
  `virtualization.virtualmachine`. Because `SeedHomeCluster.ensure_object()` replaces the full
  `content_types` M2M set on every run, the YAML lists the complete union of content types a
  status must apply to, not just the addition.
- 21 new `proxmox_*` custom fields matching Section 5.4 exactly: 9 on `virtualization.cluster`
  (`proxmox_observer_device_id`, `proxmox_identity_source`, `proxmox_scope_key`,
  `proxmox_observed_at`, `proxmox_observation_state`, `proxmox_observation_detail`,
  `proxmox_observed_node_names`, `proxmox_node_count`, `proxmox_storage_content`), 7 on
  `virtualization.virtualmachine` (`proxmox_guest_type`, `proxmox_vmid`, `proxmox_node`,
  `proxmox_status`, plus the shared `proxmox_observed_at`/`proxmox_observation_state`/
  `proxmox_observation_detail`, `proxmox_lxc_rootfs`, `proxmox_interface_evidence`), and 6 on
  `virtualization.vminterface` (`proxmox_config_slot`, `proxmox_guest_interface_name`,
  `proxmox_bridge`, `proxmox_interface_source`, `proxmox_observed_at`, `proxmox_presence`,
  `proxmox_managed_ip_evidence`). `proxmox_observed_at` is one shared CustomField applied to all
  three content types (same semantic: "evidence time for this object's own identity-level
  observation"); `proxmox_observation_state`/`proxmox_observation_detail` are likewise shared
  between Cluster and VirtualMachine. All detail/evidence fields use Nautobot's `json` custom
  field type per the plan's "closed bounded JSON" language; `proxmox_vmid`/`proxmox_node_count`
  use `integer`; the rest use `text`.

`nauto/jobs/seed_home_cluster.py`: added `ensure_cluster_types()`, following the same
get-or-create/update-diff pattern already used for `ensure_manufacturers()` etc., and wired it
into `run()` between roles and manufacturers. No other Job behavior changed — `dry_run` still
logs planned changes without writing, exactly as for every other seeded object type, satisfying
"add dry-run diffs for prerequisite objects; do not hide content-type changes" (the M2M `.set()`
call already logs `Would update {fields} relationships` under `dry_run=True`).

`nauto/seed/nodeutils_ingest.yaml`: added

```yaml
proxmox:
  schema_version: nodeutils.proxmox.v1
  max_future_skew_seconds: 300
```

matching Section 5.3's server-side-owned future-skew policy (default 300s, not host-supplied).

## 2. Strict `nodeutils.proxmox.v1` parser (ORM-free)

Added `nauto/jobs/proxmox_ingest.py`, containing only pure functions/dataclasses — no Django
import, no Nautobot model access:

- `validate_proxmox_facts(facts, *, received_at, max_future_skew_seconds=300)` returns a
  `ProxmoxValidationResult`. `valid=False` means the whole Proxmox subtree for that report is
  rejected (Section 5.3's "invalid shared platform identity" rule — no virtualization writes at
  all for that report): unsupported/missing `schema_version`, an unknown envelope or `cluster`
  key, a naive/unparseable/beyond-skew `observed_at`, or an unclassifiable cluster identity
  (`name_source` not in `{proxmox_cluster_name, standalone_node_fallback}`, or a missing
  `name`/`identity_value`).
- When the envelope and cluster identity are valid, each `qemu_vms`/`lxc_containers`/
  `storage_content` item is validated independently via `_validate_guest()` /
  `_validate_storage_scope()`: an unknown key, invalid `vmid`/`node`, malformed `interfaces`
  envelope, or malformed `rootfs` shape isolates only that item (dropped from the returned
  candidate list, recorded as a bounded closed-code error, platform `state` becomes `partial`) —
  sibling guests and storage scopes are unaffected.
- `parse_aware_utc_timestamp()` rejects naive timestamps and normalizes `Z`/offset forms to UTC;
  future skew is computed against the caller-supplied `received_at` (the eventual ingest Job's
  receipt time), matching Section 5.3's "future timestamp within the allowance is retained as its
  true observation time, not clamped" — the function returns the true parsed time, not
  `received_at`.
- QEMU guests correctly cannot carry a `rootfs` key at all (it is not in `_QEMU_KEYS`), so a QEMU
  guest with `rootfs` present is rejected via the generic unknown-key check — directly enforcing
  "QEMU root/boot disk is absent from this schema."

## 3. Tests

`nauto/tests/test_proxmox_ingest.py` (18 new tests) covers: missing/unknown `schema_version`,
unknown top-level key, naive timestamp, future-within-skew retained as true time,
future-beyond-skew rejected, `Z`-suffix normalization, missing/unknown cluster `name_source`,
unknown cluster key, valid LXC guest accepted, QEMU guest with a `rootfs` key rejected, invalid
`vmid` isolates only that guest, malformed `rootfs` isolates only that guest, valid/invalid
storage-content scopes (missing `volid`, wrong `content_type`), and a combined one-bad-guest
isolation case proving an unrelated valid QEMU guest and valid storage scope survive alongside a
`vmid=None` LXC guest that is dropped.

```
$ cd nauto && python3 -m unittest discover -s tests
Ran 32 tests — OK
```

## 4. What Step 3 does not yet cover

- No ORM write exists yet; `ingest_nodeutils_inventory.py` is unchanged. Step 4 wires
  `proxmox_ingest.validate_proxmox_facts()` into the actual Cluster/VM upsert path.
- The seed YAML additions have not been applied to the live Nautobot database — that dry-run +
  approval is Step 8's live action, not this step's.

## Gate

Pure tests prove the exact report-to-candidate contract (envelope/cluster validity, per-item
isolation, closed error codes) and beyond-skew rejection, entirely before any ORM write is added.

Proceeding to Step 4 (idempotent Cluster and guest upsert).
