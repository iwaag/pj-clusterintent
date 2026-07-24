# Step 0 — Safety preflight and revision manifest

Status: complete.

## 1. Revision manifest

- Parent repository (pre-Step-0) HEAD: `bc123645954b9253de11fa07767543a8afc0402f` (`submodule`).
- Pre-existing root working-tree state: `README_DEV.md` modified, `devdocs/big/vm/` untracked
  (this plan). Both are pre-existing user changes, not touched by this step.
- Submodule HEADs, all clean (`git status --short` empty in each):
  - `ansible_agdev` `c6faafdaef4ed43fe3477ee0443437d4b9b58ea9`
  - `nauto` `489ff6fc869b4df7748b862dd0b8efc75aea764f`
  - `nctl` `576e13b856fc5a657cd0b6cce4382679ba60e6a6`
  - `nintent` `ad9d36397d23c269ad748e13acbccc532fa29f52`
  - `nodeutils` `36e1c5752ba895780eea21b8e994926b93cc1c53`
- Raw evidence root created: `.local/vm-p1/20260724T042313Z/` (mode `0700`, files mode `0600`);
  `.local/` is git-ignored (confirmed via `git check-ignore -v`).

## 2. Secret handling check

- `nctl.toml` sets both `token_env = "NAUTOBOT_TOKEN"` and
  `token_file = "/Users/eiji/projects/pj-clusterintent/.local/secrets"`. No inline token literal
  is present in the file. `.local/secrets` is mode `0600`, single-line, no line terminator. Value
  not displayed.

## 3. Generated-artifact baseline (present/absent + digest)

- `ansible_agdev/inventories/generated/hosts_intent.yml`: present,
  sha256 `3fe1572ac6b150102f19ccad3cb5e225b2d70bf57fc849e8e1c269e6a5cfc4d8`, mtime 2026-07-22.
- `ansible_agdev/inventories/generated/production.yml`: present,
  sha256 `2781a4950e8eb542612dd03dd5c9d278cd7c7ce6a5c088528e4f8f4d27fa59a7`, mtime 2026-07-24.
  (`.local/localenv_memo.md`'s note that this file is ungenerated is stale; Step 0 supersedes it
  per the plan's own instruction to recheck rather than trust the memo.)
- `ansible_agdev/inventories/generated/production.reports/`: 55 files present; latest
  `148b416b-ca4c-4d05-9be0-cdfa9611d238.json`,
  sha256 `77fb8ea1777dd64514857bee9bcc0adbfe82142164a96f533f0e7b2a434d1142`.

## 4. Nautobot health and fresh side-effect-free renders

- `nautobot-nautobot-1`, `-worker-1`, `-scheduler-1` containers: all `Up`/`healthy`.
- `http://localhost:8000/` responded `302` (expected redirect-to-login for anonymous GET).
- Fresh renders captured to the evidence directory, all schema `nctl.drift.v1` /
  `nctl.render.*` shape (`schema`, `generated_at`, `ok`, `data`, `errors`):
  - `nctl drift --json`: exit 0, `ok: true`, 6 targets, all `converged`, 0 errors — consistent
    with Braindump Phase 3 completion memory (cluster fully converged).
  - `nctl render hosts-intent --json`: exit 0; contains `aghub` (8 occurrences) and `agdnsmasq`
    (16 occurrences).
  - `nctl render production --json`: exit 0; contains `aghub` (4 occurrences).

## 5. Probe transport selection (Step 0.7–0.9)

- `ansible_agdev/inventories/generated/production.yml` contains `aghub` under both the `linux`
  host group and `ansible_ssh_common_args`, which pins:
  `-o HostKeyAlias=nctl-node-7462b4ee-fb3b-4fa0-a89e-d9e1ded61387`,
  `-o UserKnownHostsFile=.../nctl/ssh/known_hosts`, `-o StrictHostKeyChecking=yes`. This is a
  fresh production inventory containing `aghub` under the closed SSH trust contract, so it was
  used directly as probe transport (no mDNS/UUID-alias fallback needed).
- `~/.local/state/nctl/ssh/known_hosts` contains 3 pinned host-key entries (`ssh-rsa`,
  `ecdsa-sha2-nistp256`, `ssh-ed25519`) under alias `nctl-node-7462b4ee-fb3b-4fa0-a89e-d9e1ded61387`
  for `nctl:aghub`.
- Read-only SSH trust preflight: connected using the pinned `HostKeyAlias` /
  `UserKnownHostsFile` / `StrictHostKeyChecking=yes`, resolving the shared Ansible user only
  through `ansible-vault view` against the existing vault (never displayed or logged), and ran a
  single no-op remote command. Result: host-key trust accepted, publickey auth succeeded.
- No hand-written IP, alternate node, `agdnsmasq` route, or sorted fallback was used.

## 6. `/opt/nodeutils` pin and helper audit (Step 0.10)

- Remote `/opt/nodeutils` HEAD: `36e1c5752ba895780eea21b8e994926b93cc1c53` — **matches** the
  superproject submodule pin exactly. `git status --short` on the remote checkout: clean.
- `.venv` entry point present: `/opt/nodeutils/.venv/bin/nodeutils` (owner `eiji:eiji`, mode
  `rwxrwxr-x`).
- Root-owned helper found at `/usr/local/libexec/nodeutils-pvesh-read` (owner `root:root`, mode
  `rwxr-xr-x`), sha256 `b332447784b68e1e2beb55e83c81b5edecf062599b7aa55d9012be61786b9295` —
  **identical** to the tracked source at
  `ansible_agdev/roles/nodeutils_pvesh_helper/files/nodeutils-pvesh-read` (same digest, verified
  locally, no live drift).
- `sudo -n -l` for the collection user (`eiji`) confirms exactly one scoped NOPASSWD rule:
  `(root) NOPASSWD: /usr/local/libexec/nodeutils-pvesh-read *` — no broader root path exists.
- Local audit of the helper source confirms the allowlist regex set: `/cluster/status`,
  `/cluster/resources`, `/nodes`, `/nodes/{node}/qemu`, `/nodes/{node}/lxc`,
  `/nodes/{node}/storage`, `/nodes/{node}/network`, `/nodes/{node}/qemu/{vmid}/config`,
  `/nodes/{node}/lxc/{vmid}/config`, `/nodes/{node}/qemu/{vmid}/agent/network-get-interfaces`.
  It does **not** include `/nodes/{node}/storage/{storage}/content` — confirms plan §4.1's premise
  that the storage-content path is still outside the allowlist and Phase 2 must add it.
  The helper execs `pvesh get <path> --output-format json` only (no other pvesh subcommand is
  reachable).

## Gate evaluation

No pin mismatch, no broken helper, no failed trust preflight. Step 0 gate is **passed**: Phase 1
may proceed to Step 1.

## Discrepancies

None for Step 0. The single stale-documentation note (§3, `production.yml` presence) is recorded,
not a blocker.
