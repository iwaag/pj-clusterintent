# Proxmox `pvesh` Privilege Fix Plan

Date: 2026-07-23

## Status

**Complete and deployed to `aghub`.** See `report0.md` through `report8.md` for the step-by-step
implementation record; `report8.md` cross-checks every Definition of Done item below.

This plan addresses only the confirmed Proxmox collection failure described in `problem.md`.
The agstudio stale-observation problem and the controller dump-scan issue are completed separately
in `report2.md`.

## Goal

Allow the supported nctl observation workflow to collect Proxmox inventory on `aghub` while
preserving these invariants:

- Git checkout, dependency synchronization, Python virtual environment, probe configuration, and
  report generation continue to run as `nodeutils_user`.
- Only the minimum read-only `pvesh get` operations run as root.
- The automation does not grant `nodeutils_user` general root access to `pvesh`, Python, `uv`, a
  shell, or a user-writable script.
- `/opt/nodeutils` and `/var/lib/nodeutils` do not acquire root-owned files.
- A failed privileged probe produces a truthful, actionable error before retrieval or ingest.
- A successful run is proven through collection, retrieval, Nautobot ingest, fresh drift, and a
  no-repeat reconciliation round.

## Confirmed Current Failure

The collection play currently runs:

```yaml
become: true
become_user: "{{ nodeutils_user }}"
```

That ownership choice is correct for the checkout, `.venv`, config, and report, but it also causes
`nodeutils collect` to invoke `pvesh` as the regular login user. On a Proxmox node, local `pvesh`
needs root access to `pmxcfs` IPC:

```text
regular user -> pvesh get /cluster/status -> RC=255
root         -> pvesh get /cluster/status -> RC=0
```

The current `run_pvesh()` calls the `pvesh` executable directly. Its generic command helper
collapses every non-zero result into `None`, so the caller reports only:

```text
failed to run pvesh get /cluster/status
```

No report is written, so nctl cannot retrieve, validate, cache, or ingest an aghub observation.

## Chosen Design

### Keep the collector non-root

Do not remove `become_user: "{{ nodeutils_user }}"` from the collection task. Clone/update,
`uv sync`, `uv run nodeutils collect`, config reads, serialization, and report writes remain under
one non-root owner.

### Add one root-owned, read-only `pvesh` helper

Install a small helper at this fixed path:

```text
/usr/local/libexec/nodeutils-pvesh-read
```

This path is a security-protocol constant shared by the Ansible installer and nodeutils caller,
not an inventory or host-configurable operational value. Tests on both sides must assert the exact
path so the grant and caller cannot drift apart.

The helper must:

- be owned by `root:root`;
- be non-writable by group and other users;
- use a fixed absolute, root-owned Python 3 interpreter in isolated mode;
- accept exactly one API path argument;
- reject empty input, extra arguments, control characters, query strings, `..`, shell
  metacharacters, and every path outside the explicit allowlist;
- hard-code the operation to `pvesh get`;
- hard-code `--output-format json`;
- execute a validated, absolute, root-owned `pvesh` binary;
- use an argv-based exec call, never a shell; and
- return the original command exit status and JSON stdout.

Implement the helper as a small standard-library-only Python program. Check the exact argument
count directly, validate the complete API path with full-match allowlist expressions, and then
replace the helper process with the fixed `pvesh` argv using `os.execv()`. Do not use a shell or
inherit Python path configuration from the invoking user. The Python interpreter path is a
security-protocol constant confirmed in Step 0; it is not inventory-configurable.

The initial allowlist is limited to endpoints already used by `nodeutils/proxmox_inventory.py`:

```text
/cluster/status
/cluster/resources
/nodes
/nodes/<node>/qemu
/nodes/<node>/lxc
/nodes/<node>/storage
/nodes/<node>/network
/nodes/<node>/qemu/<vmid>/config
/nodes/<node>/lxc/<vmid>/config
/nodes/<node>/qemu/<vmid>/agent/network-get-interfaces
```

`<node>` must match a bounded hostname-like segment, and `<vmid>` must be a bounded positive
decimal integer. Adding any future Proxmox endpoint requires an explicit helper and test change.

The helper source must come from the trusted Ansible controller checkout, not from the
remote `/opt/nodeutils` checkout owned by `nodeutils_user`. Copying a user-writable remote script
and then granting it passwordless root execution would create a privilege-escalation path.

### Grant sudo only for the helper

Install a dedicated sudoers fragment, for example:

```text
/etc/sudoers.d/nodeutils-pvesh
```

Its only grant is:

```text
<nodeutils_user> ALL=(root) NOPASSWD: /usr/local/libexec/nodeutils-pvesh-read *
```

The helper remains the security boundary because sudoers argument wildcards are not expressive
enough to validate the dynamic Proxmox API paths safely. The fragment must:

- be `root:root` mode `0440`;
- be installed atomically;
- be validated with `visudo -cf` before replacement;
- use a `nodeutils_user` value validated against a conservative local-account regex; and
- omit `SETENV`, shell commands, interpreters, `uv`, and direct `pvesh` grants.

### Use the helper from nodeutils

`run_pvesh()` should resolve execution as follows:

```text
effective UID is root
  -> execute the absolute pvesh binary directly

effective UID is non-root and the fixed helper exists
  -> sudo -n <fixed-helper> <api-path>

effective UID is non-root and the helper is missing/unusable
  -> fail with a specific privileged-helper error
```

Do not accept a helper command, sudo command, or executable path from the host-local probe YAML.
That YAML is writable by `nodeutils_user` and must not influence what root executes.

Use a dedicated subprocess path for privileged probes rather than the current lossy generic
`run_command()`. Preserve bounded return-code and stderr details sufficient to distinguish:

- helper missing;
- passwordless sudo not authorized;
- helper path rejected;
- `pvesh` IPC or API failure;
- timeout; and
- invalid JSON.

Do not include raw Proxmox JSON, credentials, or unbounded stderr in nctl operation evidence.

## Ownership Contract

| Path or process | Owner / execution user | Required mode or rule |
|---|---|---|
| `/opt/nodeutils` | `nodeutils_user` | existing directory contract; no root-owned descendants |
| `/opt/nodeutils/.venv` | `nodeutils_user` | created and updated only by non-root `uv sync` |
| `/var/lib/nodeutils` | `nodeutils_user` | `0700` |
| `/var/lib/nodeutils/inventory.json` | `nodeutils_user` | `0600` |
| `/var/lib/nodeutils/nctl-probe-config.yaml` | `nodeutils_user` | `0600` |
| privileged helper | `root:root` | `0755`, parent directories not user-writable |
| sudoers fragment | `root:root` | `0440`, `visudo` validated |
| nodeutils collector | `nodeutils_user` | remains non-root |
| allowlisted `pvesh get` child | root | stdout pipe only; no root-owned project/report files |

The helper returns JSON over stdout to the non-root collector. It does not create temporary files
or write into either nodeutils directory.

## Rejected Alternatives

### Run the whole collector as root

Rejected because `uv run` can mutate `.venv`, caches, bytecode, lock-related state, and the output
file. It also gives every generic host probe and host-local config hint root visibility, which is
broader than the actual need.

Adding a final `chown` is insufficient: failures before cleanup can strand root-owned files, and it
does not reduce the privilege of the probes themselves.

### Grant passwordless sudo to `pvesh`

Rejected because it gives the login user access to every present and future `pvesh` operation and
API path, including paths not needed for inventory. The fixed helper must hard-code GET semantics
and enforce the endpoint allowlist.

### Copy a helper from `/opt/nodeutils`

Rejected because that checkout is intentionally writable by `nodeutils_user`. A passwordless sudo
target must never be replaceable by the grantee.

### Root pre-collection into a temporary JSON file

Rejected for the first implementation because it introduces a second report-like artifact,
ownership transfer, cleanup, freshness, and partial-failure protocol. A stdout-only helper has a
smaller state surface.

### Proxmox HTTPS API token

Deferred. It could support remote collection and Proxmox-native ACLs, but it adds a credential
lifecycle and a second connectivity path. The current collector is intentionally host-local.

## Implementation Plan

### Step 0: Freeze the live baseline

Before changing code:

1. Record a fresh `nctl drift --host aghub --json`.
2. Record a dry reconcile and assert that `observe_node` is actually planned.
3. Inspect the two previously replayed aghub IPAM Job results and current IP ownership. Do not
   mutate or delete IPAM state merely to make the observation test pass.
4. On aghub, record:
   - absolute `pvesh`, `sudo`, Python, and `visudo` paths;
   - owner and mode of the `pvesh` binary and its parent directories;
   - `nodeutils_user` identity and sudo configuration;
   - owners/modes under `/opt/nodeutils` and `/var/lib/nodeutils`; and
   - the current remote report existence, schema, and timestamp.
5. Reconfirm the positive and negative baseline:
   - direct non-root `pvesh get /cluster/status` fails;
   - root execution succeeds.

Do not record raw SSH keys, tokens, private config, or full Proxmox responses in the report.

### Step 1: Implement and test the privileged helper

In `ansible_agdev`, add a dedicated role:

```text
roles/nodeutils_pvesh_helper/
  defaults/main.yml
  files/nodeutils-pvesh-read
  tasks/main.yml
  templates/nodeutils-pvesh.sudoers.j2
```

The role should:

1. Detect Proxmox by the validated absolute `pvesh` path, not merely by an inventory label.
2. Validate `nodeutils_user`.
3. Stat the selected Python interpreter and `pvesh` binary, including their parent directories,
   and reject a non-root-owned or group/world-writable executable or directory.
4. Create the fixed libexec directory as `root:root` without recursive ownership changes.
5. Install the controller-owned helper as `root:root` mode `0755`.
6. Install and validate the sudoers fragment as `root:root` mode `0440`.
7. Run a non-mutating preflight as `nodeutils_user`:

   ```text
   sudo -n /usr/local/libexec/nodeutils-pvesh-read /cluster/status
   ```

8. Skip helper and sudoers installation on non-Proxmox hosts.

Add focused tests for the helper:

- every required endpoint is accepted;
- representative node names and VMIDs are accepted;
- unknown endpoints and verbs are rejected;
- extra arguments are rejected;
- `..`, newlines, whitespace injection, option-like values, query strings, and shell
  metacharacters are rejected;
- the executed argv is exactly `pvesh get <validated-path> --output-format json`; and
- no shell invocation is possible.

Add an Ansible syntax check and a sudoers fixture validated with `visudo -cf` where available.

### Step 2: Update nodeutils privileged-probe execution

In `nodeutils/proxmox_inventory.py`:

1. Define fixed absolute paths for the helper and production executables after confirming them on
   aghub.
2. Add a dedicated bounded subprocess result/error path for `pvesh`.
3. Use `sudo -n` plus the helper only for a non-root process.
4. Preserve direct root invocation for explicit administrative/manual collection.
5. Keep non-Proxmox `auto` behavior unchanged and ensure it never invokes sudo.
6. Emit actionable errors without embedding raw command output.

Add unit tests for:

- non-Proxmox auto mode does not invoke the helper;
- root mode invokes direct `pvesh` with the exact argv;
- non-root mode invokes only `sudo -n <fixed-helper> <path>`;
- missing helper, denied sudo, timeout, non-zero pvesh, and invalid JSON remain distinct;
- optional endpoints may degrade only where the existing collector contract already allows it;
- required `/cluster/status`, `/cluster/resources`, and `/nodes` failures stop collection; and
- suspicious Proxmox response keys remain redacted from the final bounded report.

Document the helper and sudoers prerequisite in `nodeutils/README.md`.

### Step 3: Integrate without changing collection ownership

Add the helper role to `run_nodeutils_collect.yml`, but retain:

```yaml
become_user: "{{ nodeutils_user }}"
```

for all of:

- Git clone/update;
- `uv sync --frozen`; and
- `uv run nodeutils collect`.

The helper preflight must occur before collection. A helper failure should stop that host before
nodeutils execution, report retrieval, or Nautobot ingest.

After collection, stat the report and the important project/state paths. For Proxmox hosts, fail
the play if the report is not owned by `nodeutils_user` with mode `0600`.

Do not use recursive `chown` as routine cleanup. A root-owned descendant is evidence that the
privilege boundary is wrong and should fail verification.

### Step 4: Coordinate submodule versions

The live observation clones nodeutils from GitHub at the exact gitlink recorded by the
superproject `HEAD`. Therefore the live test cannot use an uncommitted nodeutils working tree.

Required order:

1. Complete nodeutils changes and local tests.
2. Commit the nodeutils change.
3. Ask the user separately to push the nodeutils commit, and confirm that exact SHA is reachable
   from `nodeutils_repo`. This is the only remote push required before the local live replay,
   because aghub clones nodeutils from that remote.
4. Commit the Ansible role/playbook change in `ansible_agdev`.
5. Update and commit both submodule gitlinks in the superproject.
6. Confirm `resolve_nodeutils_version()` returns the new reachable nodeutils SHA.
7. Confirm all worktrees are clean before the live replay. The local controller uses the committed
   `ansible_agdev` checkout and the superproject's local `HEAD`, so their remote pushes are not
   prerequisites for this replay.
8. After the live result is accepted, ask the user separately to push the `ansible_agdev` commit
   and then the superproject commit. Confirm the Ansible commit is remotely reachable before
   publishing the superproject gitlink. Do not batch approval for multiple repository pushes.

Do not fall back to mutable `HEAD`, copy an uncommitted helper from the remote checkout, or use a
different collector SHA only for the acceptance run.

### Step 5: Automated verification

Run from each documented project directory:

```bash
cd nodeutils
uv run pytest
uv run ruff check .

cd ../nctl
uv run pytest

cd ../ansible_agdev
ansible-playbook --syntax-check playbooks/nautobot/run_nodeutils_collect.yml
```

Also run:

```bash
git diff --check
python -m compileall <changed Python paths>
```

Add the highest-practical integration test for this boundary:

```text
non-root collector
  -> exact sudo helper argv
  -> allowlisted fake pvesh JSON
  -> schema-v2 report written by non-root
  -> report remains readable by the normal retrieval path
```

The test must assert positive helper execution; a skipped Proxmox path is not a pass.

### Step 6: Live security-boundary verification

On aghub, with the deployed role:

Positive checks:

- `nodeutils_user` can run the helper for `/cluster/status`;
- the helper returns valid JSON;
- collection uses the pinned nodeutils SHA; and
- collection writes schema v2 as `nodeutils_user`.

Negative checks:

- direct non-root `pvesh` still fails;
- `sudo -n pvesh ...` is denied;
- `sudo -n sh`, Python, `uv`, and the nodeutils command are denied;
- helper calls for an unlisted path are denied;
- helper calls with extra options, traversal, or shell metacharacters are denied; and
- the helper and sudoers fragment cannot be modified by `nodeutils_user`.

Inspect the generated report and operation artifacts for secrets. Public identifiers and bounded
diagnostics are allowed; raw credentials, SSH key material, and unredacted sensitive Proxmox
fields are not.

### Step 7: Live control-loop proof

First run a dry plan:

```bash
uv run --project nctl nctl reconcile aghub --refresh-observation
```

Require:

- scope exactly `aghub`;
- SSH preflight `ready=[aghub]`;
- one `observe_node` action;
- pinned nodeutils SHA in the planned/execution evidence; and
- no writes.

Then apply:

```bash
uv run --project nctl nctl reconcile aghub --refresh-observation --yes
```

Require positive evidence for:

1. helper preflight executed for aghub;
2. nodeutils collection executed as `nodeutils_user`;
3. at least one allowlisted `pvesh` call executed through the helper;
4. a fresh schema-v2 report was written;
5. nctl retrieved and validated the report;
6. the controller cache was atomically updated;
7. the Nautobot ingest Job reached `success`;
8. the observation action recorded `collected=true` and the pinned SHA;
9. production inventory regeneration used the resulting actual state;
10. fresh drift no longer reports the original missing-realization errors; and
11. the next normal reconcile does not repeat `observe_node` unless another real drift requires it.

If unrelated aghub or cluster drift remains, report the Proxmox observation transition separately
and do not claim whole-host convergence. If the intended observation action, helper, or ingest did
not execute, the acceptance run is unexercised.

### Step 8: Ownership and repeatability proof

Before and after the live apply, compare:

```text
/opt/nodeutils
/opt/nodeutils/.venv
/var/lib/nodeutils
/var/lib/nodeutils/inventory.json
```

Require:

- no new root-owned descendant in checkout, `.venv`, config, cache, or report paths;
- report owner remains `nodeutils_user`;
- a second `uv sync --frozen` succeeds as `nodeutils_user`;
- a second collection succeeds without ownership repair; and
- helper/sudoers ownership and modes remain unchanged.

## Failure and Rollback

The implementation must fail closed:

- invalid helper or sudoers installation stops before collection;
- failed helper preflight stops before ingest;
- a previous valid controller cache is not replaced by a missing or invalid report; and
- operation evidence retains the completed preflight/action history.

Operational rollback:

1. Disable/remove only the dedicated sudoers fragment.
2. Remove the dedicated helper after the sudoers grant is gone.
3. Revert the Ansible/nodeutils commits and superproject pins through normal Git history.
4. Preserve the last valid report and Nautobot observation unless a separate, explicit rollback
   requires changing them.

Do not weaken SSH verification, grant direct `pvesh` sudo, or run the entire collector as root as
an emergency workaround.

## Definition of Done

This fix is complete only when all of the following are true:

- the allowlisted helper and sudoers boundary are implemented and tested;
- generic non-Proxmox collection remains unchanged;
- nodeutils and Ansible tests pass from their documented working directories;
- the exact committed/pushed nodeutils SHA is deployed;
- live positive and negative privilege checks pass;
- aghub produces and ingests a fresh schema-v2 report;
- the original `no_realized_object`, `no_realized_device`, and `missing_actual_node` findings are
  resolved or explicitly replaced by a separately diagnosed non-permission issue;
- a fresh drift and no-repeat round prove the supported control loop;
- no root-owned nodeutils checkout, virtualenv, config, cache, or report artifact is created;
- operation artifacts contain no secrets; and
- the implementation report distinguishes Proxmox completion from unrelated cluster drift.
