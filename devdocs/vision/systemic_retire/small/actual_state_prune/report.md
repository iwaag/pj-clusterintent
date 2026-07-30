# Retired LXC state pruning — implementation report

Date: 2026-07-30

## Result

Implemented the bounded `nctl prune HOST [--yes]` workflow and its Nautobot
server-side Actual-deletion collector.

- The nctl planner reuses the existing typed snapshot and
  `compute_instance_removal_complete` drift result.  It accepts only one retired
  Desired node with one explicitly absent, linked Proxmox LXC whose cluster
  observation is complete.
- A dry run creates a durable `prune` operation, eligibility artifact, exact
  Desired delete list, and collector-backed Actual dependency plan.  It makes
  no infrastructure or database mutation.
- Apply re-fetches and compares the target before mutation, deletes only the
  reviewed Django collector set rooted in that node's linked Device and VM,
  then deletes the Desired endpoint/compute/node through the existing Desired
  batch API.  It records each completed step and preserves partial progress.
- A retry after Actual deletion but before Desired deletion performs only the
  remaining Desired cleanup.  A retry after all Desired rows are gone is an
  explicit `noop`.
- On completed Desired deletion, the command removes only this host's matching
  upsert rows from `.local/desired-state.yaml`, with before/after digests in
  the private operation artifacts.  It never deletes a Braindump or operation
  evidence, and never contacts Proxmox or Ansible.

## Scratch read-only acceptance

`nctl drift --host agfixture --json` confirmed the expected starting state:

- DesiredNode `198723ec-5ffe-4399-9e17-9ad92a958a12` is retired;
- DesiredComputeInstance `4bda2aa9-fe2d-4724-98ca-0286c6b5e2e2` is absent;
- linked VM `3a6aa5b1-f128-4d23-82f7-9c97acff3a68` is an absent LXC; and
- drift reports `compute_instance_removal_complete`.

The new `nctl prune agfixture --json` then correctly resolved the target and
prepared three Desired deletes (endpoint, compute instance, node), but stopped
before any mutation because the running local Nautobot container returned
`404` for the new `/api/plugins/intent-catalog/retirement-prune/actual/`
endpoint. Its durable evidence is in operation
`01KYRWCHGGZXH50D8KT6TN45NH` under the configured nctl event directory.

This is expected from the documented environment: nintent is installed in the
container from GitHub rather than the working tree. Deploying this endpoint
requires committing the nintent changes, user-authorized push, image rebuild,
and restart. Therefore no Actual or Desired record, and no operator-input row,
was changed in the scratch environment.

## Verification

- `cd nctl && uv run pytest -q --durations=20` — **1009 passed**.
- `cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests`
  — **127 passed, 10 expected skips**.
- `./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb` — **181
  passed** (the gate staged the working-tree nintent/nctl sources; no migration
  changes were detected).
- `git diff --check` passed for the changed submodule.

The destructive scratch apply remains pending the documented nintent deployment
step. Once deployed, run the dry plan again, review the collector records, then
use `nctl prune agfixture --yes` and repeat it to verify the no-op result.

## Follow-up deployment attempt

After the initial implementation was pushed, the local Nautobot image was
rebuilt at nintent `b2b2b46b1cc7e755b7db3377328211a6814ee622`.  The live dry
plan resolved the same eligible `agfixture` IDs but exposed a collector bug:
Django treats a list passed to `Collector.collect()` as a homogeneous model
set, so the mixed Device/VirtualMachine root list returned HTTP 500.  No
deletion was performed.

The correction is committed locally as nintent
`b1395903dcd0407484744c732aa1ee61f3fea74a` (`fix collector roots for
retirement prune`): collect the Device and VirtualMachine as separate roots.
The nintent ordinary suite still passes (127 tests, 10 expected skips).  Push
this follow-up commit, update the Dockerfile pin to its full SHA, and rebuild
before continuing with the destructive acceptance sequence.
