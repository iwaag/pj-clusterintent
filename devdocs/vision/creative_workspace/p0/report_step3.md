# Step 3 — Local gates (before any rebuild)

Per the plan, ran the pure-domain (Django-free) test gate before touching the container, and
before this session's final commit:

```
$ cd nintent && python3 -m unittest discover -s nautobot_intent_catalog/tests
Ran 130 tests in 0.004s
OK (skipped=10)
```

10 skips are the expected Django-unavailable-locally skips (unchanged from the pre-Step-1
baseline of 129/10 — Steps 1-2 added exactly one Django-free test and several Django-gated ones
that only run under the Nautobot runtime gate).

Steps 1-2 were committed together in `nintent` (`5a550e9`, "Add DesiredWorkspace model,
migration, and batch writer wiring") and the superproject's `nintent` submodule pointer was bumped
in the same session (`9644afe`). Nothing has been pushed.

## Pause: ask the user to push nintent

Per the plan and `.local/localenv_memo.md`, the Dockerfile installs nintent from GitHub — local
commits are invisible to the Nautobot container until pushed. Stopping here to ask the user to
push the `nintent` submodule (`git -C nintent push`) before Step 4 (rebuild, migrate, runtime
gate) can proceed. This is also the boundary for the three steps requested this session
(Step 1, Step 2, Step 3); Steps 4-6 (rebuild/migrate/runtime-gate, live desired-state write,
GraphQL proof) remain and need the push first.
