# First Proxmox Guest Realization — Phase 3 Step 1 Report

Status: **complete** (confirmed wish recorded; no desired rows, Ansible run, or Proxmox call).

On 2026-07-28 (JST), the operator explicitly confirmed the fixture and selected
**retain** as its Phase 5 disposition. `nctl braindump create` recorded the
user-direct Braindump `9cda91ef-9d86-4667-b61b-771a146f54b7`, titled
`Confirmed wish: retain agfixture LXC VMID 109`.

| Field | Confirmed value |
|---|---|
| node slug/name | `agfixture` |
| node type / accepted actual type / lifecycle | `service_host` / `virtual_machine` / `approved` |
| platform / VMID | `aghub-pve` / `109` |
| template / rootfs storage / bridge / unprivileged | `local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst` / `local-lvm` / `vmbr0` / `true` |
| vCPU / memory / root disk | `1` / `512 MiB` / `8 GiB` |
| endpoint | primary static `192.168.0.9`, `bc:24:11:00:01:09` |
| DNS / mDNS / dnsmasq generation | `agfixture.home.arpa` / `agfixture.local` / `false` |
| initial access | manual Proxmox-console bootstrap after Phase 4 creation |
| disposition | retain |

The wish explicitly permits Phase 3 desired-state and dry-plan work only. It does
not authorize a Proxmox create/start call; Phase 4 remains the first mutation
boundary.
