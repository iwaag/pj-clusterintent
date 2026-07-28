# First Proxmox Guest Realization — Phase 3 Step 0 Report

Status: **complete** (read-only baseline; no Proxmox, Ansible, Nautobot, or desired-state write).

Run date: 2026-07-28 (JST).

## Revision and deployed-state tuple

| Component | Revision | State |
|---|---:|---|
| superproject | `ca65d6a` | clean |
| nctl | `70002cc` | clean |
| nintent | `0eae8a0` | clean |
| nauto | `6f2fbeb` | clean |
| nodeutils | `775ed7f` | clean |
| ansible_agdev | `66b31c8` | clean |

All three Nautobot containers were healthy. The installed `nautobot-intent-catalog`
package resolves to nintent `0eae8a0985f9c0cb66c4c0065055592dde3c9110`, equal to
the checkout. Its baked `/opt/nautobot/intent_sources.yaml` SHA-256 is
`bc520010af8ee7c81cfd4f5927b69199e4d3a376f13ff2b4326478141e5f42a6`, equal to
`nauto/seed/intent_sources.yaml` at the checkout. All nintent migrations through
`0016_remove_reconciliation_dashboard_surfaces` are applied.

## Freshness and collision baseline

`nctl status` reports the `aghub` dump as 16.0 hours old, inside the plan's 72-hour
refresh threshold, so no additional nodeutils collection was needed. The current
cluster evidence remains the Phase 0 one-node `aghub-proxmox` platform with existing
VMIDs 100–108; VMID 109 has no seed occurrence. The Phase 3 candidate IP
`192.168.0.9` is in the intended `network-infra` static pool and the candidate MAC
`bc:24:11:00:01:09` has no occurrence in the desired seed. These are collision
checks only, not authorization to create a guest.

## Drift and render baseline

At `2026-07-28T14:20:51Z`, `nctl drift --json` succeeded: 13 targets total,
9 converged, 3 unknown, and 1 drifting. `compute_instance/agdnsmasq` is converged,
with its linked VMID-108 realization summary. No fixture row or compute-create
action exists.

| Render | SHA-256 |
|---|---|
| dnsmasq | `305e17dc3be75f208eb18728b16fb8e44e8a28389504727cb6580dc1d71bb9a1` |
| hosts-intent | `955b730efee369eb79c1e365920e8c452c480aa685d4eb9062a5c1cf668e707f` |
| production | `3eb553f371d028d1eb7ca5b64062cb65797cc734926527c8d3a4b38a8500557f` |

## Result

The environment is suitable for the Phase 3 implementation steps. Step 1 remains
an explicit operator-authority boundary: the candidate guest identity, resources,
network identity, and final disposition must be confirmed before a Braindump wish
or any desired-state row is written.
