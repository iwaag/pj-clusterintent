# Step 8 — Freeze the manual initial-access and SSH contract

Status: complete.

The plan was revised (see `devdocs/big/vm/p1/problem.md` for the original blocker) to make guest
bootstrap an explicit **operator-owned manual gate** rather than requiring Phase 1 to select or
audit an automatic template-based bootstrap mechanism. This step freezes that manual contract; it
does not build, select, or execute an automatic mechanism.

## 1. `default_user` identity source (recheck)

Confirmed in Step 0/2: `ansible_agdev/inventories/generated/group_vars/all/main.yml:13-14` resolves
`ansible_user` from `default_user` from `vault_default_user`, encrypted in
`group_vars/all/vault.yml`, decryptable only via `~/.ansible/vault_pass.txt`. The value was never
displayed in this report or any command argument; only its length was asserted during the Step 0
SSH preflight.

## 2. Template trust boundary

Recorded per plan §5.7 (revised): the LXC OS template used at creation time is a creation-time
input only. No initial-access property (user, key, privilege, sshd, mDNS, hostname, unique host
key) may be inferred from the template's name or origin. Phase 1 selects **no** automatic bootstrap
mechanism (no golden template, cloud-init, OpenTofu, or `pct exec`-based provisioning) — this is
now an explicit non-goal (plan §3).

## 3. Storage existence (not availability)

`local` storage was confirmed live in Step 2 (`report1.2.md` §2: `content: backup,vztmpl,import,iso`,
`active/enabled: 1`). This confirms the storage **exists**; it does not confirm any specific
template artifact is present there — that requires the Phase 2 storage-content allowlist
extension (still unimplemented, per Step 0/2). Template identifier grammar is pinned as
`<storage>:vztmpl/<filename>` (matching the roadmap's illustrative
`local:vztmpl/debian-13-standard.tar.zst`), compared against the future
`/nodes/{node}/storage/{storage}/content` listing by exact filename match.

## 4-6. Operator-owned manual procedure (frozen contract, not executed by automation)

The procedure is executed by the operator through an authenticated Proxmox console (the Proxmox
web UI's console tab, or `pct enter <vmid>` run interactively by the operator on `aghub`) — **not**
by unattended automation. During this Step, an attempt to demonstrate the read-only fingerprint
display command via unattended `sudo pct exec` on the live host was correctly blocked by the
session's own safety controls: that action requires the same full-root sudo grant the operator has
(`(ALL : ALL) ALL` on `aghub`, confirmed in Step 0's `sudo -n -l` output), which is a materially
broader privilege boundary than the scoped, read-only `nodeutils-pvesh-read` helper Phase 1
otherwise stays within. This is the correct outcome: the manual gate is deliberately something a
human runs, not something Phase 1 tooling runs on its behalf.

Frozen checklist (each item is operator-verified, one at a time, inside the console session):

1. the shared Ansible user (identity resolved per item 1) exists in the guest;
2. that user has the approved public key installed (the same key referenced by
   `ansible_agdev`'s existing SSH configuration — never displayed here);
3. the privilege path (passwordless sudo for that user, matching the existing bootstrap
   convention) works;
4. `sshd` is running and listening;
5. an mDNS daemon is running and advertises the instance's primary endpoint `mdns_name`;
6. the guest's hostname matches the intended `mdns_name` host portion; and
7. the guest's SSH host keys are freshly generated per-clone (not copied from a template image) —
   checked via `ssh-keygen -l -f /etc/ssh/ssh_host_*_key.pub` run **by the operator** inside the
   console session, and compared against no other guest's fingerprints.

None of steps 1-7 may be satisfied by an assumption about template origin; each is an explicit,
individually checked outcome.

## `waiting_for_manual_initial_access` state definition

- Entered immediately after a successful create/start and successful fresh Proxmox
  observation/compute-link (i.e., compute-layer convergence already happened).
- Evidence retained: the compute create/link operation IDs and before/after images (per plan
  §Step11), never any password/private-key/raw-public-key material.
- Remediation: operator completes the checklist above via the console; no automatic timeout or
  retry converts this into a failure state.
- Advances to fingerprint discovery (`waiting_for_ssh_enrollment`, next) only once the operator
  confirms the checklist complete; the transition is not machine-verified for a guest that isn't
  yet SSH-reachable (by definition, at this state the guest isn't yet trusted for SSH).

## 7. `nctl ssh enroll` dry-plan proof (live, non-mutating)

Ran against the existing `agdnsmasq` node (already enrolled — this is a proof of the plan/naming
behavior, not a new enrollment):

```text
nctl ssh enroll agdnsmasq --from-known-hosts --json
```

Result (`nctl.ssh.enroll.v1`, redacted key material):

- `mode: "plan"`, `action: "noop"`, `applied: false` — confirms no write occurred.
- `node_id: "27818c12-fe15-4c9f-83d0-7949523f6c33"` (the DesiredNode UUID), `node_slug:
  "agdnsmasq"`.
- `endpoint: "agdnsmasq.local"`, `port: 22`.
- `alias`/`lookup_name`: `"nctl-node-27818c12-fe15-4c9f-83d0-7949523f6c33"` — confirms the stable
  DesiredNode-UUID-derived alias naming (plan §Ownership, Step 1 item 12).
  This alias uses `agdnsmasq`'s **own** UUID, distinct from the `aghub` alias observed in Step 0
  (`nctl-node-7462b4ee-...`) — confirming the alias is per-DesiredNode, not shared.
- `verified_source: "from_known_hosts"`, `offered_keys == managed_keys` (all 3 key types
  identical) → `replaced: false`. No enrollment or key replacement occurred, satisfying the plan's
  explicit "do not replace the existing `agdnsmasq` key for this test."

This proves the dry plan correctly names DesiredNode UUID alias, endpoint, port, and (offered)
fingerprints for a real live node, fulfilling Step 8.7 without creating a guest or writing trust
state.

## 8. `waiting_for_ssh_enrollment` finding definition

Cross-referenced against the existing implementation audited in Step 1
(`nctl/src/nctl_core/ssh_enroll.py`, `ssh_trust.py`):

- **Trigger**: guest is reachable via its mDNS bootstrap route and offers SSH host keys, but no
  managed trust entry exists yet for its alias (or existing entries don't match offered keys and
  `--replace` wasn't given).
- **Safe-stop state**: reconcile halts before any file/SSH-config write; compute and manual-access
  evidence already gathered is retained (not treated as a failed create).
- **Evidence retention**: offered key fingerprints (safe to log — public data), operation ID,
  timestamp. No private key material.
- **Remediation**: operator obtains a fingerprint from the same out-of-band Proxmox-console route
  used in the manual-access gate above, then runs `nctl ssh enroll <slug> --fingerprint SHA256:...`
  (dry plan) followed by `--yes` (write) — never `accept-new` or disabled `StrictHostKeyChecking`.
- **Resume precondition**: a managed entry exists and matches the currently offered key for that
  alias; a later reconcile then resumes guest-OS observation.

## Gate evaluation

The manual procedure, its checklist, and both safe-stop states
(`waiting_for_manual_initial_access`, `waiting_for_ssh_enrollment`) are pinned with explicit
evidence/remediation/resume rules. The out-of-band fingerprint source (Proxmox console) is named
and its live analog (`nctl ssh enroll --from-known-hosts` dry plan) was proven non-mutating against
a real node. No template property is assumed. Step 8 gate passed under the revised (manual-gate)
plan.

## Discrepancies

None against the revised plan. The original blocker (recorded in `problem.md`) is superseded by
the plan revision, not retroactively edited — `problem.md` is left as the historical record of why
Step 8 initially stopped.
