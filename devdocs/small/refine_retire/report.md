# Retired LXC Workflow Refinement — Report

Date: 2026-07-30

## Result

Implemented the retirement-workflow refinement in `nctl`, `nintent`, and the
operator/brainforge documentation.

- `nctl reconcile GUEST --allow-destroy --json` plan mode now embeds the full
  `nctl.reconcile.plan.v1` object at `data.plan` in addition to `data.plan_path`.
  A reviewer can directly inspect the pinned `destroy_compute_instance` action,
  including its target slug, VMID, and control-node evidence.
- `compute_instance_removal_complete` remains visible as INFO drift/evidence,
  but is no longer a manual-review finding. A successful destroy followed by
  fresh absence observation now terminates `converged` with `ok: true`.
- The two-field retirement batch is documented as an update of an existing
  guest. Omitted fields are preserved; it is not a general VM lifecycle API.
- The retirement batch runtime test now verifies preview + atomic apply and
  preservation of existing compute fields.
- `actual_already_pruned` keeps the permissive retry behavior, but now reports
  `absent_actual_roots`, `remaining_actual_roots`, and
  `actual_deletion_requested: false`. It therefore never claims an Actual
  deletion that was not requested, including when no Device observation was
  ever recorded.
- `agentdocs/brainforge/README.md` now gives the executable batch-preview,
  JSON-plan-review, successful-removal, and separate-prune-preview guidance.

## Verification

| Check | Result |
|---|---|
| Focused nctl retirement/reconcile contracts | `89 passed` |
| Full nctl suite | `1019 passed` |
| nintent Django-free suite | `127 passed`, `10` expected Nautobot-dependent skips |
| Local Nautobot runtime gate (`--keepdb`) | `189 passed` |
| `git diff --check` | passed for root, `nctl`, and `nintent` changes |
| Scratch `nctl status --json` | Nautobot reachable/authenticated; Intent GraphQL available |
| Scratch `nctl drift --json` | `converged: 7`, `drifting: 2`, `unknown: 4` |

The runtime gate ran the updated nintent batch test against the existing local
scratch Nautobot/PostgreSQL environment.

## Disposable LXC replay

Not run. The plan requires a real Proxmox destructive replay, but it does not
identify the disposable guest's exact slug/VMID and control node. No existing
guest was inferred to be disposable and no Proxmox/Ansible destruction command
was issued. Consequently there are no live retirement/prune operation IDs to
record. Once an operator names that exact disposable target, replay:

```text
retire batch preview -> retire batch apply -> reconcile dry plan ->
reconcile --allow-destroy --yes -> fresh drift -> prune dry plan -> prune
```

and append the resulting operation IDs and final drift to this report.
