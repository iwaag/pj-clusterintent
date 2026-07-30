# Phase 4 Step 3 — destroy handler

Status: complete.

Added the registered `compute_destroy` bootstrap handler. Before it constructs an Ansible command, it re-derives the round-snapshot disposition and requires `destroy_required` plus exact equality with the pinned parameters. It then invokes only `destroy_lxc.yml`, limited to the pinned control-node slug, and requires controller-owned JSON confirmation of absence.

- A successful actual destruction is `mutated=true`; an already-absent guest is truthful success with `mutated=false`.
- Non-zero playbook exit, missing result, invalid JSON, and unconfirmed absence are failed results with `mutated=true`, preserving the existing executor failure-path final-drift refresh behavior.
- The handler never writes Actual state and retains ordinary `requires_observation=true` behavior, so the control node—not the destroyed guest—is observed afterwards.

Validation includes happy path, parameter drift refusal before runner start, result failure forms, and already-absent truthfulness. The complete nctl suite later passed 1005 tests.
