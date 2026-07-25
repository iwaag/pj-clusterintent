# Step 0 — Safety preflight and current contract snapshot

Status: `complete`.

Raw evidence: `.local/vm-p3/20260725-step0/` (private, mode 0700/0600).

## 1. Revision and dirty-state check

`git status --short` on the superproject is clean. `git submodule status` matches the plan's
Section 4.1 manifest exactly:

| Repository | Revision | Matches plan manifest |
|---|---|---|
| `ansible_agdev` | `339d361b0d60b5c4e45dc1adccb3b44fdaf7b162` | yes |
| `nauto` | `251b056549f1b01f604b42b486fdc12d667db521` | yes |
| `nctl` | `fd9cb878a1cdab9a436e7d125d2e5697badc1fc4` | yes |
| `nintent` | `ad9d36397d23c269ad748e13acbccc532fa29f52` | yes |
| `nodeutils` | `3a0fdf9817d970935847aafd46c35bf07133c20c` | yes |

No source-changed audit is required before Step 1.

## 2. Nautobot/Django/PostgreSQL versions

`docker exec nautobot-nautobot-1 nautobot-server version` -> Nautobot `3.1.3`, Django `5.2.14`.
`docker exec my_postgres_db psql -U nautobot -d nautobot -c 'select version();'` ->
`PostgreSQL 15.17 on aarch64-unknown-linux-musl`. Both match Section 4.1.

## 3. Migration state

`nautobot-server showmigrations nautobot_intent_catalog` -> latest applied is
`[X] 0014_braindump_exchange_diary`, matching Section 4.2's stated baseline.
`nautobot-server makemigrations nautobot_intent_catalog --check --dry-run` -> `No changes detected
in app 'nautobot_intent_catalog'`, exit 0.

## 4. Current DesiredNode/DesiredEndpoint rows for `aghub`/`agdnsmasq`

| Row | Key fields |
|---|---|
| DesiredNode `aghub` | `id 7462b4ee-fb3b-4fa0-a89e-d9e1ded61387`, `lifecycle=approved`, `node_type=device`, `realized_device=fcebe565-...` (`derived`), `realized_vm=None` |
| DesiredNode `agdnsmasq` | `id 27818c12-fe15-4c9f-83d0-7949523f6c33`, `lifecycle=active`, `node_type=service_host`, `realized_device=36178882-...` (`override`), `realized_vm=None` |
| DesiredEndpoint `primary` (agdnsmasq) | `id 0dea1561-bfb7-4058-8ba7-c71d18666cad`, `endpoint_type=primary`, `ip_policy=static`, `ip_address=192.168.0.2`, `dns_name=agdnsmasq.home.arpa`, `mdns_name=agdnsmasq.local`, `generate_dnsmasq=True` |

Total live rows: 5 `DesiredNode`, 5 `DesiredEndpoint`.

**Discrepancy from the Section 5.11 seed illustration**: the live endpoint's `ip_policy` is
currently `static`, not the seed's proposed `dhcp_reserved`. This is a real field change the Step 9
review must present to the operator explicitly, not an unrelated diff to silently overwrite.

## 5. Legacy `DesiredNode.realized_vm` assertion

`DesiredNode.objects.exclude(realized_vm__isnull=True).count()` == **0** across all 5 rows. The
zero-legacy-link precondition required before the Step 8 destructive cutover already holds today.

## 6. Actual Cluster/VM identity and freshness (Phase 2 ledger, read-only reread)

- Cluster `aghub-proxmox`, `id 0ef3f747-b905-42f7-82d8-7e8572e9b63d`, `last_updated
  2026-07-24T18:30:22Z`.
- VirtualMachine `agdnsmasq`, `id 935f0b6f-5926-41e2-80db-bfa4b637cfce`, cluster `aghub-proxmox`,
  `proxmox_guest_type=lxc`, `proxmox_vmid=108`, `proxmox_node=aghub`, `last_updated
  2026-07-24T18:30:22Z`. VM count under the cluster: 9. Matches Section 4.3 exactly.
- `nctl actual --json` (read-only, no live Proxmox call) shows `agdnsmasq`: `vcpus=1`,
  `memory=512`, `disk=8`, `rootfs {storage: local-lvm, volume: vm-108-disk-0, size_gb: 8.0}`,
  `net0` MAC `BC:24:11:23:DC:B7` (canonical `bc:24:11:23:dc:b7`), bridge `vmbr0`. These are the
  exact `vcpus`/`memory_mb`/`root_disk_gb`/`mac_address` values proposed in the Section 5.11 seed,
  confirming the seed was transcribed correctly from Phase 2 evidence.

## 7. GraphQL/REST schema probe

- GraphQL `__schema.queryType.fields` contains `desired_node(s)`, `desired_endpoint(s)`,
  `desired_service(s)`, `desired_dependency(s)`, `desired_service_placement(s)`,
  `desired_node_operational_override(s)`, `desired_ip_range(s)` — **no** `desired_compute_platform`
  or `desired_compute_instance` roots exist yet, matching Section 4.2's "there are no desired
  compute models" baseline.
- REST `GET /api/plugins/intent-catalog/compute-platforms/` -> `404`.
- REST `GET /api/plugins/intent-catalog/compute-instances/` -> `404`.
- Plugin API root exposes only `alignment-reviews`, `braindumps`, `endpoints`, `nodes`, `services`.

## 8. nctl baseline

- There is no standalone `nctl desired` CLI command; desired-layer data is exposed only through
  `drift`, `actual`, and `render`. `nctl_desired_before.stderr` records the `No such command
  'desired'` error as evidence this was checked, not assumed.
- `nctl drift --json` -> `ok=true`, `errors=[]` (`nctl_drift_before.json`, 34236 bytes).
- `nctl actual --json` -> `ok=true` (`nctl_actual_before.json`, 9980 bytes).
- `nctl render production` sha256 `d4d5cf7e...2ae2738`.
- `nctl render hosts-intent` sha256 `ea4e7650...96538862bbf62`.
- `nctl render dnsmasq` sha256 `305e17dc...6580dc1d71bb9a1`.
- Managed known_hosts sha256 `7cba6b73...0457932f8`.

Full digests are recorded in `manifest.txt` for exact before/after comparison at Step 12.

## 9. Active migration/import Job check

`JobResult.objects.filter(status__in=['PENDING','RUNNING']).count()` == 0. No conflicting job is
running.

## 10. Secret hygiene

The Nautobot token was read only from `.local/secrets` (git-ignored, 40 bytes) via `cat`/curl
`Authorization` header and never echoed into a report, manifest, or command argv shown here.

## Gate

Starting state, exact live GraphQL/REST shape, DesiredNode/DesiredEndpoint/actual-ledger baseline,
zero-legacy-link precondition, and rollback revisions all match the plan's Section 4 assumptions
except the noted `ip_policy` discrepancy, which is flagged for the Step 9 seed review rather than
silently reconciled here. No live state was changed.

Proceeding to Step 1.
