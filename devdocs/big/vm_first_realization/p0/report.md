# First Proxmox Guest Realization — Phase 0 Report

Status: **blocked only on the operator-confirmed fixture record**. All read-only rechecks and the vocabulary/actuator decisions are complete. No desired-state, Nautobot, Ansible, Proxmox, or source-code write occurred.

Run date: 2026-07-28 (JST).

## Revision and deployed image

| Component | Revision | State |
|---|---:|---|
| superproject | `cc20614` | only the untracked roadmap/report directory |
| nctl | `1ca0e74` | clean |
| nintent | `4f46bc8` | clean |
| nauto | `6dab422` | clean |
| nodeutils | `775ed7f` | clean |
| ansible_agdev | `66b31c8` | clean |

The running Nautobot, worker, and scheduler containers were healthy. The baked build information
is nintent `84ac0b125c996bcc9c821252c34e84ca967c64f0` and nauto
`1c78af8bdbfc69cafdc293b4082f866de9f271b0`; the baked seed checksum verified.

The nintent delta to checkout HEAD has two test-only commits, touching only
`tests/test_desired_node_link_http.py`; it has no model, migration, API, or compute-contract
change. The nauto delta adds runtime tests/docs and a six-line job-testability adjustment, with no
seed-contract or Proxmox-model change needed here. No image rebuild was warranted.
All migrations through `0016_remove_reconciliation_dashboard_surfaces` are applied.

## Fresh Proxmox observation

`aghub.local` accepted a non-interactive strict-host-key SSH connection using its generated
`HostKeyAlias` and nctl-managed known-hosts file. From it, the read-only
`/usr/local/libexec/nodeutils-pvesh-read` boundary successfully ran
`uv run nodeutils collect --proxmox enabled --format json` at `2026-07-28T09:01:12Z`.

The platform is the one-node cluster `aghub-proxmox` (node `aghub`) and bridge `vmbr0`.

| Kind | VMID | Name | State |
|---|---:|---|---|
| QEMU | 100 | infra | stopped |
| LXC | 101 | agansible | running |
| QEMU | 102 | aghaos | running |
| LXC | 103 | agprome | stopped |
| LXC | 104 | aggrafana | stopped |
| QEMU | 105 | agk3s | running |
| LXC | 106 | agnomad | stopped |
| LXC | 107 | agkeadhcp | stopped |
| LXC | 108 | agdnsmasq | running |

Fresh `vztmpl` availability on storage `local` is exactly:

- `local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst`
- `local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst`

`local-lvm` is evidenced as the existing LXC rootfs storage, while template content is correctly
reported only on `local`. The old illustrative Debian template is unavailable: the fixture must
use one of the two exact Ubuntu strings above and `local-lvm` for rootfs storage.

## Fixture record — not yet frozen

No confirmed Braindump wish or operator confirmation identifying a new disposable guest was
available in the task or desired state. Phase 0 must not manufacture intent for real hardware, so
the following values remain deliberately **unconfirmed**: guest name/slug, unused VMID, selected
template, vCPU, memory, root disk, endpoint IP/MAC/DNS/mDNS, and final keep-or-manually-destroy
disposition. `local-lvm` and `vmbr0` are observed candidates, not confirmation.

This is the sole unmet exit condition. Inventing an IP, MAC, VMID, or real-hardware cleanup policy
would violate the confirmed-proposal authority boundary.

## DHCP decision

**The fixture will use a non-DHCP-reservation/static IP policy.** `agdnsmasq.local` remains
unreachable by the accepted local-environment baseline and has stale current observation. A DHCP
reservation would make the creation proof depend on a dnsmasq deploy that cannot be positively
exercised.

Thus Phase 3 will set a non-reserved/static endpoint policy, request no dnsmasq record, and have
no `dnsmasq_config` action dependency. It still must preflight platform freshness and endpoint,
VMID, MAC, and IP collisions. Initial network setup remains part of the explicit manual-console
bootstrap.

## Frozen compute vocabulary

All codes target `compute_instance` (platform evidence is attached to the affected instance).

| Code | Severity | Classification |
|---|---|---|
| `compute_platform_missing` | error | manual_review |
| `compute_platform_observation_stale` | error | observe, then manual_review if incomplete |
| `compute_platform_ambiguous` | error | manual_review |
| `compute_instance_missing` | error | create only for an approved, fully preflighted fixture |
| `compute_instance_candidate_ambiguous` | error | manual_review |
| `compute_instance_not_linked` | warning | ledger_link only for one re-derived candidate |
| `compute_realized_instance_missing` | error | manual_review; never recreate from a vanished link |
| `compute_identity_conflict` (scope/node/VMID/kind) | error | manual_review |
| `compute_power_state_mismatch` | warning | start only for desired running / actual stopped |
| `compute_endpoint_mac_conflict` | error | manual_review |
| `compute_primary_endpoint_ambiguous` | error | manual_review |
| `waiting_for_manual_initial_access` | info | resumable terminal; no repeated create/start |
| `compute_resource_mismatch` | warning | unsupported |
| `unexplained_compute_guest` | info | manual_review; no delete/stop |

Configured-versus-agent interface joining, QEMU disk comparison, multi-NICs, allocation, and all
destructive or resource-mutation operations are deferred: no placeholder code or action is added.

## Actuator and privilege boundary

The chosen mechanism is a narrowly scoped new `ansible_agdev` playbook, invoked only by a new
registered nctl compute handler against the exact generated-inventory target `aghub`:
`ansible-playbook -i <operation inventory> <compute playbook> --limit aghub`.

It will use argv-form `ansible.builtin.command`, `become: true`, and absolute
`/usr/sbin/pct` commands: status/preflight, `pct create <intent-pinned arguments>` only after
fresh absence/collision validation, then `pct start <vmid>` only for that identified guest.
SSH trust remains the nctl HostKeyAlias/known-hosts policy; login and become credentials remain
the existing private key and Ansible vault. Root on `aghub` is the explicit boundary because
Proxmox create/start requires it.

There is no generic shell input, no Proxmox credential in nintent, no expansion of the read-only
`nodeutils-pvesh-read` helper, and no stop/delete/resize/migrate command.

## Behavioral baseline

At `2026-07-28T09:02Z`, `uv run --project nctl nctl drift --json` succeeded with 5 unknown,
5 converged, and 1 drifting targets. There are zero desired compute rows, zero compute drift codes,
zero compute actions, and no Proxmox write path.

| Read-only artifact | SHA-256 |
|---|---|
| dnsmasq render | `305e17dc3be75f208eb18728b16fb8e44e8a28389504727cb6580dc1d71bb9a1` |
| hosts-intent render | `7153c0675e8337f5c3db09167cefd27ddbdf0b3dcc27ea21c5a0762adf546570` |
| production render | `d6bf1e970b20fe86c872442f5ae9d3a1c583e40b0a7a855b466b078714245637` |

The production render includes only `aghub`; `agdnsmasq` remains excluded by stale guest-OS
observation. The fresh Proxmox report was not ingested, so the Nautobot ledger did not change.

## Read-only guarantee and remaining input

Only inspection, container/migration reads, strict SSH verification, the read-only nodeutils
collection, nctl drift, and nctl renders ran. No Ansible playbook, `nctl reconcile`, Nautobot
write/Job, seed import, Docker rebuild, `pct`, or pvesh write endpoint ran. The only repository
addition is this report.

To complete Phase 0, confirm one disposable LXC record: name/slug, unused VMID, one template from
the observed list, `local-lvm`, `vmbr0`, vCPU, memory MiB, root disk GiB, unused IP, MAC, DNS,
mDNS, and keep or manual-destroy after Phase 5. The completed checks need not be repeated unless
the platform observation has become stale.

