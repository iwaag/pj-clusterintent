# Phase 3 Step 3.2 — nctl lifecycle operation and CLI command

Parent: [plan.md](plan.md), Step 3.2.

## Implementation

Added `nctl_core/lifecycle.py` (Decision 2's focused core module):

- `LIFECYCLE_STATES` is the closed five-value vocabulary.
- `set_node_lifecycle(client, node_slug, requested_state)` is the pure operation: resolves the
  node from `fetch_desired_snapshot()` by exact slug match only (no fuzzy/ID matching), returns
  `changed=False` with no PATCH when current state already matches, otherwise PATCHes exactly
  `{"lifecycle": STATE}` to `/api/plugins/intent-catalog/nodes/{id}/` through
  `NautobotClient.rest_patch()`, then refetches through GraphQL and raises
  `LifecycleConfirmationMismatchError` (fail closed) unless ID/slug/state all confirm.
- `LifecycleError` subclasses map 1:1 to the plan's Decision 3 table: `invalid_lifecycle`,
  `unknown_node`, `lifecycle_update_rejected`, `lifecycle_confirmation_mismatch`. None of these
  join `drift.registry` or `reconcile.classify.CODE_CLASSIFICATION` — they are raised/caught only
  inside this module and the CLI command.
- `build_lifecycle(cfg, node_slug, requested_state)` is the CLI-facing entry point (resolves the
  token, runs the operation, always returns an `Envelope[LifecycleData]`, never raises), matching
  the `build_status`/`build_drift` convention.
- `render_lifecycle_text` renders `NODE: before -> after` or `NODE: already STATE (no change)`,
  and error text only, per the plan's explicit-idempotence requirement. No token, response body, or
  unrelated node field is ever printed.

Added the thin `nctl lifecycle NODE STATE [--json] [--config PATH]` Typer command in
`cli/main.py`: parses arguments, calls `build_lifecycle`, renders, and maps `invalid_lifecycle`/
`unknown_node` to usage exit (2) and any other failure to failure exit (1), leaving success at 0 —
no business logic in the command function itself.

Documented the command in `nctl/README.md` (new `### lifecycle` section, explicit "not an approval
engine, not part of `reconcile --yes`" statement) and `nctl/docs/output-format.md` (new
`## nctl.lifecycle.v1` section with example payload and field semantics).

## Tests

- `tests/test_lifecycle_contract.py` (frozen in Step 3.1): all **7 pass** against the new module —
  vocabulary, invalid-state short-circuit before any fetch, unknown-node rejection with no PATCH,
  idempotent no-write, single-field PATCH at the exact path, rejected-PATCH error, and
  confirmation-mismatch fail-closed.
- `tests/test_cli_lifecycle.py` (new, **7 pass**): text/JSON rendering, argument pass-through,
  idempotent-text wording, and exit-code mapping (`invalid_lifecycle`/`unknown_node` → 2,
  `lifecycle_update_rejected` → 1, success → 0).
- Full nctl suite: `uv run --project nctl pytest -q nctl/tests` — **600 passed** (587 baseline +
  13 new), no regressions, same pre-existing `StarletteDeprecationWarning`.

## Live-safe verification

Ran the deployed command against the live development Nautobot (read/idempotent paths only, no
node mutated):

- `nctl lifecycle agpc planned --json` on the currently `planned` node `agpc`: resolved the real
  node ID, returned `changed: false`, `previous_state == current_state == "planned"` — confirms the
  idempotent no-write path end to end against real GraphQL/REST, with no PATCH issued.
- `nctl lifecycle no-such-node active`: `error: no desired node with slug 'no-such-node'`, exit
  code **2**.
- `nctl lifecycle agpc bogus`: `error: invalid lifecycle 'bogus'; must be one of planned, approved,
  active, deprecated, retired`, exit code **2**.

No live node's lifecycle was changed in this step; the actual `active` promotions are reserved for
the reviewed Step 3.7 live transition after the nintent default batch lands.

## Result

The lifecycle command is complete, tested, documented, and verified against the live server on its
read/idempotent/error paths. It compiles cleanly against the current Phase 2 nintent REST/GraphQL
shape with no schema change on either side, matching Decision 6's compatible-rollout premise. Step
3.3 can now land the nintent default-site batch independently.
