# Phase 4 Step 0 Report

Status: **complete** (read-only baseline).

Revision tuple: superproject `c9065bf`; nctl `d476def`; ansible_agdev `1eec904`; nauto `1b74d88`; nintent `0eae8a0`; nodeutils `775ed7f`.

`nctl status` authenticated to local Nautobot. `aghub` observation was 16.5 hours old and the compute platform remained complete/fresh. The baseline drift names `agfixture` only as a missing compute instance (VMID 109); dnsmasq render contains no fixture reservation.

Using the generated strict-trust production inventory, read-only Ansible reached `aghub` and `become` worked. `/usr/sbin/pct status 109` returned the expected absent-configuration result; `pct list` contained no VMID 109 and no LXC configuration matched `192.168.0.9` or `bc:24:11:00:01:09`. `/usr/bin/pvesh get /nodes/aghub/storage/local/content --content vztmpl --output-format json` confirmed `local:vztmpl/ubuntu-24.04-standard_24.04-2_amd64.tar.zst` is present. No Proxmox write was issued.
