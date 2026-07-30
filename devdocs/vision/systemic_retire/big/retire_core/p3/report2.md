# Retire core Phase 3 — Step 2 evaluator

Date: 2026-07-30

## Status: complete

nctl commit `8880be0299fe531a60d3dda368fb3bc2f43e885f` makes compute drift
consume the shared disposition before reading retained guest fields.

- Retired/present produces only the realization summary (identity conflicts
  remain visible); it cannot emit stale link, power, or resource findings.
- Retired/absent/observed-present emits warning
  `compute_instance_destroy_required`; retired/absent/observed-absent emits
  info `compute_instance_removal_complete`. Both retain the structured
  summary, including actual presence and disposition.
- Non-retired `desired_presence=absent` emits warning
  `compute_presence_lifecycle_conflict` and continues ordinary comparison; it
  authorizes no deletion.
- Ordinary present-path comparison and unrelated-guest handling are unchanged.

The third code is the planned Phase 3 vocabulary extension: it makes an
invalid lifetime/presence combination visible and reviewable instead of
silently treating it as permission to remove a guest.

Verification: `cd nctl && uv run pytest -q --durations=20` — **994 passed**.
No planner, handler, CLI option, playbook, Actual write, or Proxmox call was
added in this step.
