# Test Strategy Phase 4 — Step 3 Report: Command Matrix and Admission Rules

Parent: [plan.md](plan.md), Step 3.

Status: **`complete`**.

## Documentation outcome

Root [`README_DEV.md`](../../../../README_DEV.md) now owns the sole test command matrix, tier
definitions, admission checklist, environment classes, prerequisites, expected skips, evidence
locations, cleanup ownership, and explicit production/external approval boundary. It covers the
five ordinary component suites, both Nautobot runtime modes, OpenSSH, Ansible, the privileged
helper, and the measurement entry point.

`nctl`, `nintent`, `nauto`, `nodeutils`, and `ansible_agdev` now link to that root matrix instead
of maintaining conflicting command lists. `devtests/test_strategy/README.md` continues to own the
specific fixture behavior for its conformance gates.

The measurement command was implemented early with user approval because the Step 3 matrix is
required to contain and execute it, while its planned implementation step appears later. Its
measurement result and before/after interpretation remain Step 5 work after Steps 1–4 freeze the
test set.

## Matrix execution

Every currently runnable matrix command was executed from its documented directory:

```text
nctl ordinary                         967 passed
nintent Django-free fast              227 run, 14 expected skips
nauto ordinary                        110 passed
nodeutils ordinary                     54 passed
ansible helper ordinary                 4 passed
OpenSSH conformance                     2 passed
Ansible conformance                     1 passed
privileged-helper integration           1 passed
Nautobot runtime --keepdb             290 collected/passed
Nautobot runtime --clean              290 collected/passed; migration check clean
measurement --runtime                 passed; runtime stage cleaned
```

The production/external row intentionally has no ordinary command or run: it requires separate,
explicit user approval and remains out of scope. No matrix command uses a bare superproject
`pytest`; every pytest invocation names an owning project/path or working directory.

No public-network call, real inventory, external host, or production mutation occurred. The named
test database and fixture-owned paths were the only runtime mutation boundaries.
