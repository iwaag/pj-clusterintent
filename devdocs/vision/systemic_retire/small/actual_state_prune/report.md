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

The first follow-up deployment exposed the collector API's second constraint:
each root must be a *homogeneous sequence*, not a bare model instance. The
dry plan again stopped before mutation with HTTP 500 (`Device object is not
subscriptable`). The final correction is committed as nintent
`02156ca18dbe7f6e8dbb43abe595ee645949aeb9` (`fix collector root sequence
shape`), which calls `collect([device])` and `collect([vm])` separately.
The same nintent ordinary suite passes. This commit must be pushed and deployed
before attempting the apply sequence.

After deploying that correction, the dry plan completed successfully (operation
`01KYRX06ABXRSHZKKF0XFHMRC9`) and identified the exact linked Device, VM, VM
interface, tags, and IP-link rows. Review found that Django's normal cascade
does not include the exclusively attached IPAddress itself, so apply was
deliberately withheld. nintent commit
`48f6552ab01e119d30e6efe3d50d3914024718b8` (`prune exclusively attached IP
addresses`) now adds an IP only when every Device/VM interface attachment is in
the selected collector set; shared IPs remain out of scope. The nintent
ordinary suite remains green. Push and deploy this commit before the final
dry-plan/apply/no-op acceptance.

## Final scratch acceptance

With nintent `48f6552ab01e119d30e6efe3d50d3914024718b8` deployed, dry plan
`01KYRX5980YVT86DR1WZAX47Y8` selected exactly seven Actual records: the
agfixture Device, VirtualMachine, VM interface, exclusively attached
IPAddress and its link, and two tags. It selected exactly three Desired rows:
the endpoint, compute instance, and node.

Apply `01KYRX5G5NB4MEGPF7EERHJ8TQ` completed all recorded stages:

1. deleted those seven Actual records, with no sibling guest or cluster in the
   collector result;
2. committed all three Desired deletes through the canonical batch API; and
3. removed the matching agfixture upserts from `.local/desired-state.yaml`.

The retained agfixture Braindump remains readable (`nctl braindump list`), and
the operation still exposes its event log plus Actual-plan/delete, Desired
batch, and operator-input evidence via `nctl ops show
01KYRX5G5NB4MEGPF7EERHJ8TQ`.

A repeat `nctl prune agfixture --yes --json` returned `state=noop` with
`result=already_pruned`; it performed no mutation. The full cluster drift runs
successfully and has no agfixture target. During this check, an unrelated
empty-Desired-platform assertion was discovered and corrected in nctl
(`compute_evaluation.py`); it now renders a platform summary instead of
crashing after a complete prune. `cd nctl && uv run pytest -q --durations=20`
passes with **1010 tests**.
