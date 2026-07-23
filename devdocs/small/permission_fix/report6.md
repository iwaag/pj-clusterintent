# Permission Fix Step 6 Report: Live Security-Boundary Verification

Date: 2026-07-23

## Status

**Complete. Live changes made to `aghub`; no code changes in this step.**

This is the first step in the plan that touches real infrastructure. The
`nodeutils_pvesh_helper` role was applied to `aghub` and its security boundary was verified with
both positive and negative live checks, then a real collection run was executed to confirm the
end-to-end fix.

## One bug found and fixed during this step

The role's `Reject a non-root-owned or group/world-writable executable or directory` assertion
used a bitwise-and Jinja expression:

```yaml
- (item.stat.mode | int(base=8)) & 0o022 == 0
```

This failed live with `Syntax error in expression: unexpected char '&' at 31` — Ansible's
condition-expression parser (as opposed to full Jinja2 template rendering) does not accept the
`&` operator. Since Ansible's `ansible.builtin.stat` result already exposes `wgrp`/`woth` booleans
directly, the fix replaces the arithmetic with:

```yaml
- not item.stat.wgrp
- not item.stat.woth
```

This was caught immediately (the whole play failed cleanly with `failed=1`, no partial state) and
fixed before any file was installed — `ansible-playbook --syntax-check` in Steps 1/3/5 could not
have caught this, since it only validates YAML/module syntax, not Jinja condition-expression
grammar. Re-ran `ansible-playbook --syntax-check` after the fix (still passes) before retrying
live.

## Live install result

Ran the role in isolation against `aghub` (via a throwaway wrapper playbook, not committed):

```text
ok=14  changed=2  unreachable=0  failed=0  skipped=0
```

The two `changed` tasks were installing the helper (`/usr/local/libexec/nodeutils-pvesh-read`) and
the sudoers fragment (`/etc/sudoers.d/nodeutils-pvesh`); everything else (directory creation,
stats, assertions, preflight) was already-satisfied or read-only.

## Positive checks

- `nodeutils_user` (`eiji`) can run the helper: `sudo -n /usr/local/libexec/nodeutils-pvesh-read
  /cluster/status` → valid JSON, `RC=0`.
- Helper file: `root:root 755` at the fixed path.
- Sudoers fragment: `root:root 440`, content exactly
  `eiji ALL=(root) NOPASSWD: /usr/local/libexec/nodeutils-pvesh-read *`.
- Full collection run (`ansible-playbook ... run_nodeutils_collect.yml -e target_hosts=aghub -e
  nodeutils_version=9351db9...`): `ok=33 changed=3 failed=0`, including both new post-collection
  ownership assertions from Step 3.
- Collection used the pinned SHA: `/opt/nodeutils` on `aghub` is checked out at exactly
  `9351db97c94666cbc40a3e821a93386a8a2fcf2a` (confirmed via `git rev-parse HEAD` on the host).
- Collection wrote schema v2 as `nodeutils_user`:
  `/var/lib/nodeutils/inventory.json` is `eiji:eiji 0600`, `schema_version: nodeutils.inventory.v2`,
  with real Proxmox data (`proxmox.enabled/detected: true`, `cluster.nodes: ["aghub"]`,
  3 QEMU VMs, 6 LXC containers).

## Negative checks

All performed as `eiji` (no `become`) over SSH, each with `</dev/null` to guarantee no interactive
prompt could ever block (see incident below):

| Check | Result |
|---|---|
| direct non-root `pvesh get /cluster/status` | `RC=255`, IPC failure (unchanged baseline) |
| `sudo -n pvesh get /cluster/status ...` | `sudo: a password is required`, `RC=1` |
| `sudo -n sh -c 'id'` | `sudo: a password is required`, `RC=1` |
| `sudo -n python3 -c 'print(1)'` | `sudo: a password is required`, `RC=1` |
| `sudo -n uv --version` | `sudo: a password is required`, `RC=1` |
| `sudo -n <helper> /access/users` (unlisted endpoint) | `nodeutils-pvesh-read: rejected API path`, `RC=1` |
| `sudo -n <helper> '/cluster/status/../../etc/passwd'` (traversal) | rejected, `RC=1` |
| `sudo -n <helper> '/cluster/status; id'` (shell metacharacter) | rejected, `RC=1` |
| `sudo -n <helper> /cluster/status /cluster/resources` (extra args) | `expected exactly one API path argument`, `RC=1` |
| `test -w <helper>` as `eiji` | not writable |
| `test -r`/`-w /etc/sudoers.d/nodeutils-pvesh` as `eiji` | neither readable nor writable |

Every negative case matches the plan's required list exactly: only the exact helper path for an
allowlisted `GET` succeeds; every other `pvesh`/shell/interpreter/`uv` sudo path, every out-of-
allowlist or malformed helper argument, and any attempt to read or modify the helper/sudoers
artifacts themselves is denied.

## Operational incident during verification (no live impact)

An earlier draft of the verification command used `sudo stat ...` (missing `-n`) to inspect the
sudoers fragment's ownership. Ansible's shell module has no TTY, so `sudo` without `-n` blocked
indefinitely waiting for a password that could never arrive, hanging the whole chained-command
invocation. It was killed via the background-task stop tool before any timeout damage; `pgrep -u
eiji -a sudo` on `aghub` afterward confirmed no stray process was left running. All subsequent
sudo invocations in this report use `-n` and `</dev/null`.

## Secrets review

```bash
grep -Eio '"[a-z_]*(token|secret|password|passwd|credential|apikey|api_key)[a-z_]*"\s*:\s*"[^"]*"' \
  /var/lib/nodeutils/inventory.json
# -> no matches
```

No raw credentials, SSH key material, or unredacted sensitive fields were found in the collected
report.

## Ownership hygiene after collection

```bash
find /opt/nodeutils -maxdepth 1 -not -user eiji -print
find /var/lib/nodeutils -maxdepth 1 -not -user eiji -print
# -> both empty
```

No root-owned descendant was left in either directory after the privileged helper install and a
full collection run.

## Not yet done (subsequent steps)

- The report above was written directly via `ansible-playbook`, not through the supported
  `nctl reconcile aghub --refresh-observation` path — Nautobot ingest, drift resolution, and the
  no-repeat round are Step 7's job.
- Repeatability (second `uv sync`/collection without ownership repair) is Step 8's job.
