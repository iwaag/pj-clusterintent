# Phase 1 — Step 1 report: compute-root seed

Status: **complete**. The operator approved the two declared-but-unobservable values:
`template=local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst` and `unprivileged=true`.
They are declarations, not observed facts; a future change to `unprivileged=false` remains a
separate explicit desired-state change.

- `nauto` commit `6f2fbeb` adds `aghub-pve`, `agdnsmasq` VMID 108, and endpoint MAC
  `bc:24:11:23:dc:b7`.
- The rebuilt image's seed checksum was `bc520010af8ee7c81cfd4f5927b69199e4d3a376f13ff2b4326478141e5f42a6`,
  equal to the checkout; its nintent commit remained `84ac0b125c996bcc9c821252c34e84ca967c64f0`.
- Preview JobResult `7c726945-1733-4771-b0b8-77737b732436`: 2 creates, 1 endpoint update,
  21 unchanged, zero conflicts/errors.
- Approved apply JobResult `b2a31b5d-f35b-4d9d-bce9-d2a942b9a91a`: post-commit confirmation
  matched with no mismatch.
- Repeat apply JobResult `7cee3d33-78bf-48b1-a689-397bf2e3f15d`: 0 creates, 0 updates,
  0 conflicts; confirmation succeeded.

No Proxmox, Ansible, or realization-link write occurred.

