# Permission Fix Step 3 Report: Integrate Without Changing Collection Ownership

Date: 2026-07-23

## Status

**Complete. Committed locally in the `ansible_agdev` submodule (`9bad3db`); not pushed.**

Only `playbooks/nautobot/run_nodeutils_collect.yml` changed. Nothing was run against a live host;
verification is a syntax check plus a re-run of the Step 1 helper unit tests.

## What changed

### Role wiring

```yaml
roles:
  - role: uv
  - role: nodeutils_pvesh_helper
```

`nodeutils_pvesh_helper` runs at the play's `roles:` stage — before any `tasks:` — so its
Proxmox-detection stat, ownership assertions, helper/sudoers install, and non-mutating preflight
all complete (or fail the host) before the checkout, `uv sync`, or collection tasks run. A helper
install or preflight failure on a Proxmox host therefore stops that host before nodeutils
execution, report retrieval, or Nautobot ingest — matching the plan's requirement.

### Collection ownership unchanged

`become_user: "{{ nodeutils_user }}"` is untouched on all three privileged tasks:

- `Clone or update nodeutils repository`
- `Sync nodeutils dependencies with uv`
- `Run nodeutils inventory collection`

The role's own privileged work (creating `/usr/local/libexec`, installing the helper, installing
the sudoers fragment, and the sudo preflight) runs under the play's `become: true` (root), which is
independent of and does not touch `become_user` on the collection tasks.

### Post-collection ownership verification

Added after the collection task:

1. `Stat the nodeutils checkout and state directories after collection` — stats
   `nodeutils_checkout_dir` (`/opt/nodeutils`) and `nodeutils_state_dir` (`/var/lib/nodeutils`).
2. `Fail if collection left a root-owned nodeutils directory` — asserts each exists and is owned
   by `nodeutils_user`. This is a non-recursive, top-level check only — per the plan's explicit
   rejection of routine recursive `chown`, a root-owned descendant should fail verification, not
   be silently repaired.
3. `Stat the collected nodeutils report` / `Fail if the report was not produced by the non-root
   collector` — asserts `nodeutils_output_path` exists and is owned by `nodeutils_user`, for every
   host (not just Proxmox).
4. `Fail if a Proxmox host produced a wrongly-moded report` — asserts mode `0600`, gated
   `when: nodeutils_pvesh_bin_stat.stat.exists` (the Proxmox-detection variable registered inside
   the role, still in scope after `roles:` completes). This matches the plan's narrower
   requirement that only Proxmox hosts must fail on report mode.

`nodeutils_collect.py:1290-1293` already opens the output file with `os.open(..., 0o600)` and
`os.chmod(..., 0o600)`, so this check requires no nodeutils-side change — it only verifies the
existing contract holds after introducing the privileged helper.

## Verification

```bash
ansible-playbook --syntax-check playbooks/nautobot/run_nodeutils_collect.yml
# -> playbook: playbooks/nautobot/run_nodeutils_collect.yml (no errors)

python3 roles/nodeutils_pvesh_helper/tests/test_nodeutils_pvesh_read.py
# -> Ran 8 tests in 0.000s, OK
```

No live host was reached in this step. `git diff --check` passed; only
`playbooks/nautobot/run_nodeutils_collect.yml` was modified.

## Not yet done (subsequent steps)

- The `nodeutils` and `ansible_agdev` submodule commits are still local-only; `aghub` cannot yet
  clone the pinned `nodeutils` SHA or run the updated playbook (Step 4).
- No live install of the helper/sudoers fragment on `aghub`, and no live collection run through
  this updated playbook, has happened yet.
