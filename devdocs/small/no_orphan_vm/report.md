# No-Orphan VM Prune — Report

Date: 2026-07-31

## Result

`nctl prune` now treats the linked Actual VirtualMachine and Device as
independent roots. The VirtualMachine is planned whenever it remains; a Device
is included only when it exists. Desired tombstones are deleted only after the
collector has deleted every surviving root in that reviewed plan.

This fixes the guest-without-initial-observation case:

```text
retired DesiredNode + absent DesiredComputeInstance
  + retained Actual VirtualMachine
  + no Actual Device
=> prune plans/deletes the VirtualMachine, then deletes Desired records
```

The reverse partial state is handled the same way. If no Actual root remains,
prune performs only the final Desired cleanup. This is a retry state, not a
claim that a remaining root was deleted.

## Implementation

- `nctl_core.retirement_prune._resolve()` builds a payload from surviving
  linked roots instead of skipping all Actual cleanup when either root is
  absent.
- The nintent retirement-prune endpoint accepts nullable root IDs, re-resolves
  each supplied root through the Desired links, rejects an existing linked root
  that was omitted from the plan, and collects whichever roots survive.
- The collector accepts VM-only, Device-only, or two-root cleanup while keeping
  its reviewed-record-set check before deletion.
- `nctl/README.md` now documents independent roots and the no-orphan contract.

No Proxmox command or live prune was run during this source change.

## Verification

- `uv run pytest -q tests/test_retirement_prune.py tests/test_reconcile_executor.py`
  in `nctl/`: **52 passed**.
- `python -m compileall` passed for the changed nintent retirement-prune module.
- `git diff --check` passed in `nctl/`.

The local nintent `uv` environment does not provide `pytest`, so its Django
test suite was not run here. Run the normal Nautobot runtime test gate after
deploying the nintent commit, including a VM-only retirement-prune fixture.
