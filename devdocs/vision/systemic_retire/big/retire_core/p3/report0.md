# Retire core Phase 3 — Step 0 baseline

Date: 2026-07-30

## Status: complete

Read-only baseline before Phase 3 implementation:

| Component | Revision |
|---|---|
| superproject | `d625830f3775ac165cca13089dbc34e403720916` |
| nctl | `13ae1cd64646cc94af76f54a200ca3d69b611318` |
| nintent | `7c880237eeb5f1f75b678b199ebd19340bc4a5c5` |
| nauto | `6462ebcbd9b8033853b60473dbe7f18d400cdd0b` |
| nodeutils | `775ed7fad5110a96186a737147b87d3bf450ced2` |
| ansible_agdev | `aa8f9f47ca746cea7facdf45f6929fd981efdf3a` |

`uv run --project nctl nctl drift --json` succeeded (`ok: true`). Its global
summary was `converged=9`, `drifting=2`, `unknown=4`; the unrelated existing
`compute_primary_endpoint_missing` finding for `agdnsmasq` was retained.

The disposable `agfixture` started as follows:

- `compute_instance` target `4bda2aa9-fe2d-4724-98ca-0286c6b5e2e2` was
  `converged`, with only `compute_realization_summary` (info). Desired was
  `approved` + `desired_presence=present`; the linked VM
  `3a6aa5b1-f128-4d23-82f7-9c97acff3a68` had `presence=present`.
- Its `node` target `198723ec-5ffe-4399-9e17-9ad92a958a12` was `converged`,
  with only `intent_effect_summary` (info). This is the F8 before-picture:
  no guest-OS node finding exists while the fixture remains approved/present.
- `uv run --project nctl nctl reconcile agfixture` was a plan-only operation
  (`01KYRME2E9V7D4R1GQCQSYNYKJ`) with `scope summary: converged=2`, no
  actions, manual review, or unsupported entries.

No Desired or Actual row, cluster guest, or external target was written.
