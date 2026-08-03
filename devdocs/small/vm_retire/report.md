# VM Retire: Enabling QEMU VM Destruction via nctl

## Summary

`problem.md` documented that `nctl reconcile` intentionally refused to plan
`destroy_compute_instance` for QEMU virtual machines, forcing manual
`qm destroy <vmid>`. This was a single pure gate (`_destroy_parameters` in
`nctl_core/drift/compute_disposition.py`) plus one hardcoded LXC-only Ansible
playbook selection in the destroy action handler — nothing upstream
(planner, classifier, executor, `--allow-destroy` flag) was LXC-specific.

The gate and the actuation path have been generalized to cover both guest
kinds symmetrically. QEMU VMs with `desired_presence: absent` and
`lifecycle: retired` can now reach `destroy_required` and be destroyed by
`nctl reconcile --yes --allow-destroy`, exactly like LXC containers already
could.

## Changes

- **`nctl/src/nctl_core/drift/compute_disposition.py`**
  `_destroy_parameters` now maps `instance_kind` → expected `guest_type` via
  `_DESTROYABLE_GUEST_TYPES = {"container": "lxc", "virtual_machine": "qemu"}`
  instead of hardcoding `container`/`lxc`. Renamed gate-failure codes:
  `instance_kind_not_container` → `instance_kind_not_destroyable`,
  `guest_type_not_lxc` → `guest_type_disagrees_with_instance_kind`. The
  returned `parameters["guest_type"]` is now the observed value (`"lxc"` or
  `"qemu"`) instead of a hardcoded `"lxc"`.

- **`ansible_agdev/playbooks/proxmox/destroy_qemu.yml`** (new)
  Mirrors `destroy_lxc.yml` (probe → stop-if-running → destroy → confirm
  absent → write controller-owned result JSON) but uses `qm` instead of
  `pct`. Syntax-checked with `ansible-playbook --syntax-check`.

- **`nctl/src/nctl_core/reconcile/actions/compute_destroy.py`**
  Added `DESTROY_PLAYBOOKS = {"lxc": ..., "qemu": ...}` and selects the
  playbook from the pinned `action.parameters["guest_type"]` (which is
  re-validated against a freshly-derived disposition before any command
  runs, unchanged). Unknown guest types fail closed with an explicit error
  instead of falling through to the LXC playbook.

- **`nctl/src/nctl_core/retirement_prune.py`**
  The post-destroy ledger-cleanup eligibility check accepted only
  `guest_type == "lxc"` for a confirmed-absent linked VM; now accepts
  `("lxc", "qemu")` so `nctl prune` also completes the QEMU retirement
  lifecycle (Actual + Desired ledger row deletion), not just the destroy
  step.

- **`nctl/src/nctl_core/cli/main.py`**
  Updated `--allow-destroy` and `prune` help text from LXC-only wording to
  LXC/QEMU wording (no behavior change).

- **Tests** (`nctl/tests/test_compute_disposition.py`,
  `nctl/tests/test_compute_destroy.py`): updated the renamed gate-failure
  case, added `test_qemu_virtual_machine_can_be_destroy_required` (QEMU
  reaches `destroy_required`; a guest_type/instance_kind mismatch still
  gates as `retained`), and
  `test_destroy_handler_runs_qemu_playbook_for_virtual_machine_guest`
  (destroy handler picks `destroy_qemu.yml` for a `guest_type: qemu`
  pinned action).

## What did not need to change

- `reconcile/reconcilers.py`, `planner.py`, `classify.py`,
  `ssh_preflight.py`, `executor.py`'s `--allow-destroy` gate, and
  `actions/dispatch.py` were already guest-type agnostic — they consume
  `disposition.parameters`/`outcome` generically.
- `compute/contract.py` already accepted `instance_kind == "virtual_machine"`
  as a valid, fully-specified desired-compute-instance kind.

## Verification

- `uv run pytest` in `nctl/`: **1151 passed, 1 failed** (pre-existing,
  unrelated: `test_reconcile_profiles.py::test_real_repo_file_validates`
  fails identically on a clean stash of this change — `deployment_profiles.yml`
  references `comfyui`/`swarmui` profiles that aren't declared; not touched
  by this work).
- `ansible-playbook --syntax-check` on the new `destroy_qemu.yml` passes.
- No live Proxmox actuation was performed — this was implemented and
  test-verified only. Before running `nctl reconcile --yes --allow-destroy`
  against a real retired QEMU VM, do one supervised dry run first
  (`nctl reconcile` without `--yes` to confirm the plan lists exactly the
  intended `destroy_compute_instance` action with `guest_type: qemu`).

## State

Implemented in the `nctl` and `ansible_agdev` submodules; **not committed**.
`git status` in the superproject shows both submodules modified. Left
uncommitted pending your review, since this enables a new destructive
capability (physical VM deletion) and touches a submodule pointer bump in
the superproject.
