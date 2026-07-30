# Retire core Phase 1 — final report

Date: 2026-07-30

## Status: complete

Phase 1 persists explicit compute absence without changing compute drift semantics or actuation.

- `DesiredComputeInstance.desired_presence` is `present|absent`, defaults to `present`, and is
  migrated by `0021_desiredcomputeinstance_desired_presence`.
- The canonical batch writer atomically committed a disposable `retired + absent` declaration;
  nctl GraphQL typed-snapshot read it back. An absent-only declaration on a planned/present
  instance returned HTTP 409 and was confirmed rolled back.
- nintent `7c88023`, nctl `49f4355`, and the scratch image all agree through the generated compute
  conformance fixture. The deployed image was verified at nintent `7c88023`.
- The ordinary compute realization summary now shows desired presence and effective lifecycle.
  No new drift code, severity, classification, action, CLI option, VM presence field, Proxmox
  call, or actuation was added.

## Accepted limits and Phase 3 handoff

F4 remains intentional: batch preview is a value diff and does not run model `full_clean()`, so
an invalid absent-only document may preview as an update before apply atomically rejects it.

F5 remains intentional: changing a node lifecycle later does not re-run its instance validation.
Phase 3 must treat `desired_presence=absent` under a non-retired effective lifecycle as an
ordinary drift finding, never as a crash or deletion authorization. Phase 1 has one owner rule and
does not add a second node-write validator.

## Verification

All required gates passed: nintent Django-free 127 run / 10 expected skips, compute conformance 1,
nctl ordinary 989, and clean Nautobot runtime 181. See [report5.md](report5.md) for exact evidence;
[report0.md](report0.md) through [report4.md](report4.md) retain the step-by-step record.
