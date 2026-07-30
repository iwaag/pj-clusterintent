# Retire core Phase 1 — Step 4 scratch deployment and canonical-writer proof

Date: 2026-07-30

## Deployment

After the operator pushed nintent, the scratch Dockerfile pin was advanced to nintent
`7c880237eeb5f1f75b678b199ebd19340bc4a5c5`. A no-cache build resolved that exact GitHub
commit, and the image's `build_info.json` and installed package `direct_url.json` both reported
the same SHA. The web, worker, and scheduler services were recreated. `nautobot-server migrate`
shows `0021_desiredcomputeinstance_desired_presence` applied.

## Canonical-writer proof

All writes used `nctl desired apply` against disposable scratch rows; `agfixture` was untouched.

1. A dry run of the disposable node/platform/instance creation reported four creates; `--yes`
   committed it.
2. The atomic `node.lifecycle=retired` plus `instance.desired_presence=absent` document previewed
   two updates and committed both in one transaction.
3. A nctl GraphQL typed-snapshot re-read reported the target as `retired/absent`.
4. A separate planned/present disposable instance received the invalid absent-only document. Its
   preview reported one update; apply returned HTTP 409. A nctl GraphQL re-read confirmed it
   remained `planned/present`, proving rollback rather than partial write.

The first attempted invalid replay changed only the already-absent instance's node lifecycle;
that correctly exercised accepted limit F5 because no instance write occurred. It was immediately
restored to `retired`, then the distinct present instance above was used for the required rollback
proof. This confirms F5 is a Phase 3 handoff, not a reason to add a second validator in Phase 1.

All six test-owned Desired rows were deleted after the proof. A fresh whole-cluster drift returned
the Step 0 summary unchanged: `drifting=2`, `converged=9`, `unknown=4`; severity
`error=6`, `warning=5`, `info=17`.

## Status

**complete** — the field is deployed, migrated, atomically writable, and readable through the
canonical nctl path without unrelated drift movement.
