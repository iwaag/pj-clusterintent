# Permission Fix Step 1 Report: Implement and Test the Privileged Helper

Date: 2026-07-23

## Status

**Complete. Committed locally in the `ansible_agdev` submodule; not pushed.**

Nothing was deployed to `aghub` in this step. All work is local implementation and unit
verification only.

## What was added

New role `ansible_agdev/roles/nodeutils_pvesh_helper/`:

```text
defaults/main.yml
files/nodeutils-pvesh-read
tasks/main.yml
templates/nodeutils-pvesh.sudoers.j2
tests/test_nodeutils_pvesh_read.py
```

Committed in `ansible_agdev` as `f304407` (local; per Step 4 of the plan, the submodule gitlink in
the superproject is updated later, after the nodeutils change also lands).

### Helper (`files/nodeutils-pvesh-read`)

Standard-library-only Python program (`sys`, `os`, `re`), shebang
`#!/usr/bin/python3.13 -I` (the exact interpreter confirmed root-owned on `aghub` in Step 0, used
in isolated mode). It:

- requires exactly one argument (`sys.argv` length 2), else exits non-zero without executing
  anything;
- validates that argument with `\A...\Z`-anchored regexes (not `$`, so an embedded newline cannot
  smuggle a second command past the anchor) against the 10 allowlisted endpoint patterns from the
  plan, with bounded `NODE` (`[A-Za-z0-9][A-Za-z0-9-]{0,62}`) and `VMID` (`[1-9][0-9]{0,8}`, no
  leading zero, no negative/zero values) segments;
- on success, calls `os.execve("/usr/bin/pvesh", ["/usr/bin/pvesh", "get", path,
  "--output-format", "json"], {"PATH": "/usr/bin:/bin", "HOME": "/root"})` — an argv-based exec
  with a minimal explicit environment, never inheriting the caller's environment and never
  invoking a shell.

### Sudoers template (`templates/nodeutils-pvesh.sudoers.j2`)

```text
{{ nodeutils_user }} ALL=(root) NOPASSWD: {{ nodeutils_pvesh_helper_path }} *
```

No `SETENV`, no shell, no interpreter, no direct `pvesh` grant — matches the plan's requirement
that the sudoers wildcard stays permissive (it cannot itself validate Proxmox API paths) while the
helper is the actual security boundary.

### Role tasks (`tasks/main.yml`)

1. Stats `nodeutils_pvesh_bin` (`/usr/bin/pvesh`) to detect Proxmox — this is the play's Proxmox
   detection, independent of any inventory label.
2. Everything else runs inside a `block: ... when: nodeutils_pvesh_bin_stat.stat.exists`, so
   non-Proxmox hosts skip helper/sudoers installation entirely but continue the rest of the
   collection play (an earlier draft used `meta: end_host`, which would have wrongly skipped
   nodeutils collection too on non-Proxmox hosts — caught and fixed before committing).
3. Validates `nodeutils_user` against `^[a-z_][a-z0-9_-]{0,31}$`.
4. Stats the `pvesh` binary, the Python interpreter, and `/usr/bin`, `/usr`, `/`, then asserts each
   is root-owned and not group/other-writable (`mode & 0o022 == 0`).
5. Creates `/usr/local/libexec` as `root:root 0755` (no `recurse`, so no ownership change is
   forced on existing unrelated content).
6. Installs the controller's `files/nodeutils-pvesh-read` as `root:root 0755` — sourced from the
   `ansible_agdev` checkout, never copied from the remote `/opt/nodeutils` checkout that
   `nodeutils_user` can write to.
7. Renders the sudoers fragment to an `ansible.builtin.tempfile`, validates it with
   `visudo -cf`, then copies it (`remote_src: true`) to `/etc/sudoers.d/nodeutils-pvesh` as
   `root:root 0440`, and removes the temp file. The candidate is never installed before validation
   passes.
8. Runs `sudo -n <helper> /cluster/status` as `nodeutils_user` (non-mutating preflight) and asserts
   the stdout parses as JSON.

## Tests

### Helper unit tests (`tests/test_nodeutils_pvesh_read.py`, stdlib `unittest`, no dependencies)

Loads the helper file directly via `importlib.machinery.SourceFileLoader` (it has no `.py`
extension) and exercises `validate_path()` and `main()` without touching the filesystem or any
real `pvesh`/`sudo`:

- every one of the 10 required endpoints is accepted, including representative node names
  (`aghub`, `pve-node-1`) and VMIDs (`100`, `9999`, `1`);
- 20 rejected cases cover: empty/root path, unknown endpoints (`/access/users`), a wrong HTTP-verb-
  shaped path, trailing slash, `..` traversal (both raw and inside a segment), embedded newline,
  `;`, backtick and `$()` shell metacharacters, a query string, an extra option-looking suffix,
  vmid `0`, negative vmid, leading-zero vmid, a space inside a node name, and option-like arguments
  (`-e`, `--help`);
- extra arguments (`["prog", "/cluster/status", "/cluster/resources"]`) and missing arguments are
  rejected;
- `main()` is monkeypatched at the `os.execve` boundary to assert the exact executed argv
  (`["/usr/bin/pvesh", "get", "/cluster/status", "--output-format", "json"]`) for an accepted path,
  and to assert `os.execve` is never called for a rejected path;
- a source-text assertion confirms the file contains no `subprocess`, `os.system`, `os.popen`, or
  `shell=True` — no code path can reach a shell.

Result:

```text
Ran 8 tests in 0.004s
OK
```

### Ansible syntax check

```bash
ansible-playbook --syntax-check <wrapper playbook including role: nodeutils_pvesh_helper>
```

Passed (no target hosts required for a syntax check).

### Sudoers fixture

Rendered the template with `nodeutils_user=eiji`,
`nodeutils_pvesh_helper_path=/usr/local/libexec/nodeutils-pvesh-read`, and validated with
`visudo -cf`:

```text
eiji ALL=(root) NOPASSWD: /usr/local/libexec/nodeutils-pvesh-read *

<tmpfile>: parsed OK
```

## Deviations from a literal reading of the plan

- The plan's ownership contract table lists the helper as mode `0755`; `tasks/main.yml` installs
  it at `0755` (root-owned, executable by all, writable by none but root) — matches.
- `execv()` vs `execve()`: the plan text says `os.execv()`; the implementation uses `os.execve()`
  with an explicit minimal environment instead of inheriting the caller's environment, which is a
  stricter reading of "do not inherit Python path configuration from the invoking user" applied to
  the exec'd `pvesh` process too. This is a refinement, not a contradiction, and is covered by the
  argv-assertion test.

## Not yet done (subsequent steps)

- The role is not yet wired into `run_nodeutils_collect.yml` (Step 3).
- `nodeutils/proxmox_inventory.py` does not yet call the helper (Step 2).
- Nothing has been installed on `aghub`; the live preflight task has only been syntax-checked, not
  executed against a real host.
