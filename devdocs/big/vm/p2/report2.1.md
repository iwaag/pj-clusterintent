# Step 1 — Implement and freeze the normalized observation contract

Status: `complete` for local code/tests. Live acceptance is deferred to Steps 8/9.

## 1. What changed

`nodeutils/proxmox_inventory.py` was rewritten to emit the nested `facts.proxmox` shape defined
in `devdocs/big/vm/p2/plan.md` Section 5.2, replacing the old flat/raw structure described in
Section 4.1:

- Added `PROXMOX_SCHEMA_VERSION = "nodeutils.proxmox.v1"` and the semantic collection limits from
  Section 5.2 (`LIMIT_NODES=64`, `LIMIT_QEMU_GUESTS=512`, `LIMIT_LXC_GUESTS=512`,
  `LIMIT_CONFIG_INTERFACES_PER_GUEST=64`, `LIMIT_AGENT_INTERFACES_PER_GUEST=256`,
  `LIMIT_ADDRESSES_PER_AGENT_INTERFACE=64`, `LIMIT_STORAGE_SCOPES=128`,
  `LIMIT_VZTMPL_ITEMS_PER_STORAGE=2048`, `LIMIT_ERRORS_PER_SCOPE=128`).
- `classify_cluster_identity()` explicitly derives `name`, `name_source`
  (`proxmox_cluster_name`/`standalone_node_fallback`), and `identity_value` from
  `/cluster/status`, never inferring the source later from spelling.
- `normalize_mac()` normalizes to lowercase colon form and returns `(mac_or_none, is_valid)`; an
  invalid non-empty MAC is reported (`invalid_mac_raw`), never silently dropped or guessed.
- `parse_qemu_net_config()` / `parse_lxc_net_config()` replace the old single `config_interfaces()`
  overwrite path: QEMU config MACs are now correctly extracted from model-prefixed NIC strings
  (`virtio=<MAC>,...`), and config/agent interface collections are kept separate instead of the
  old "agent replaces config wholesale" behavior.
- `join_qemu_interfaces()` joins config and agent evidence only on one unique normalized MAC;
  duplicate-MAC or config-only/agent-only entries remain in their source collection and in
  `unmatched`, never guessed by name/order.
- `parse_rootfs()` parses LXC `rootfs` (`storage:volume,size=<N><unit>`) independently of
  aggregate `maxdisk`/`disk`; a missing/unsupported grammar returns `None`, which the guest
  normalizer turns into partial `rootfs` section evidence rather than falling back to `disk_gb`.
- `_ErrorSink` and `apply_limit()` give every bounded collection a deterministic sort key,
  bounded/omitted error tracking, and a `truncated_collection` error instead of silent generic
  truncation.
- `normalize_qemu_vm()` / `normalize_lxc_container()` now build the full per-guest `observation`
  block (`state`, `last_attempted_at`, `evidence_observed_at`, `omitted_error_count`, `errors`,
  per-section state) and omit unrestricted `raw` payloads entirely.
- `collect_proxmox_inventory()` builds the full nested `collection` envelope (platform-level
  section states for `cluster_identity`, `node_list`, `qemu_guest_lists`, `lxc_guest_lists`,
  `storage_inventory`), isolates one bad guest's config-read failure or malformed-normalization
  exception to that guest (recorded as a bounded error, platform marked `partial`) without
  dropping its list-level identity, and adds the new `storage_content` collection (vztmpl-only,
  fetched per storage that advertises `vztmpl` in its content types — this also lays the read path
  Step 2 extends at the helper boundary).
- `nodeutils_collect.py:build_inventory_report()` now excludes `facts.proxmox` from the generic
  `bounded_value()` pass and re-attaches it verbatim afterward, so the semantic per-collection
  limits above are the only bounding applied to it — the generic 200-item/200-key bounder can no
  longer silently truncate a valid 512-guest or 2048-template list before the final 2 MiB
  fail-closed size check (which still applies to the whole report).

`raw`, `resources`, `networks`, and per-guest `raw` are no longer collected or emitted, matching
the Section 5.2 "not part of `nodeutils.proxmox.v1`" list; the old `/cluster/resources` and
`/nodes/{node}/network` reads were dropped from the collection path since nothing in the frozen
schema consumes them.

## 2. Fixtures used

Two golden fixtures are exercised directly from the live Phase 1 baseline captured in Step 0:

- QEMU `aghaos` (VMID 102) — config-slot MAC `02:7b:67:47:0d:fd` joins to the
  `qemu-guest-agent` interface `enp0s18` reporting `192.168.0.234/24`.
- LXC `agdnsmasq` (VMID 108) — `rootfs=local-lvm:vm-108-disk-0,size=8G` parses to
  `{storage: local-lvm, volume: vm-108-disk-0, size_gb: 8.0}`; `net0` config
  (`hwaddr=BC:24:11:23:DC:B7,ip=192.168.0.2/24`) creates one config-only-eligible interface
  candidate without needing guest-agent data (LXC has no agent evidence in this schema).

Both are asserted by name in `tests/test_proxmox_inventory.py::CollectProxmoxInventoryFixtureTests`.

A clustered-identity fixture (`{"type": "cluster", "name": "prod-cluster"}`) and the live
standalone case (`{"type": "node", "name": "aghub"}`, no cluster row) are both covered in
`ClusterIdentityTests`, proving `name_source` provenance is explicit rather than inferred.

## 3. Tests

`tests/test_proxmox_inventory.py` was rewritten (37 tests, all passing): MAC normalization,
QEMU/LXC interface parsing (including invalid-MAC and DHCP-token cases), rootfs parsing
(including the missing-size and malformed-grammar cases), the join matrix (unique/config-only/
agent-only/duplicate-MAC), cluster-identity classification, the bounded-limit helper
(truncation + error recording), the error sink's bounded/omitted-count behavior, and two
end-to-end fixture-backed collection tests: the positive `agdnsmasq`/`aghaos` case, and a
one-malformed-guest isolation case (an LXC config-read failure keeps that guest's list-level
identity, omits its `rootfs`, marks the platform `partial`, and leaves the unrelated QEMU guest
untouched).

`tests/test_pvesh_helper_integration.py` was updated for the new call shape (no more
`/cluster/resources` assertion; `cluster.nodes` renamed to `cluster.observed_node_names`; added a
schema-version assertion) — still exercises the real allowlisted helper source end-to-end.

```
$ uv run --project nodeutils pytest nodeutils/tests/ -q
54 passed in 1.81s
```

## 4. What Step 1 does not yet cover

- The exhaustive Section 8.2 scenario matrix (201-item generic boundary, semantic-limit boundary
  at exactly 512/2048/etc., >2 MiB fail-closed, multi-generation merge) is deferred to Step 7's
  full verification pass, per the plan's sequencing; Step 1's gate only requires the schema
  fixtures, join positives, cluster provenance, and non-silent-truncation behavior, which are
  covered above.
- The `/nodes/{node}/storage/{storage}/content` helper allowlist entry does not exist yet on the
  installed `aghub` helper; Step 1's `storage_content` collection code path is exercised only
  against mocked `run_pvesh` fixtures. Step 2 adds and proves the real helper boundary.
- No live deployment or ingest changed; this step is local-code-only per Section 3.3.

## Gate

Schema fixtures validate exactly (`aghaos` join, `agdnsmasq` rootfs+interface), cluster
provenance is explicit and tested for both branches, the semantic limiter records
`truncated_collection` instead of silently dropping data and is proven not to pass through the
generic bounder, and unknown/malformed guest data is isolated to that guest without losing
sibling guests or list-level identity.

Proceeding to Step 2 (storage-content helper boundary).
