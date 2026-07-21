# Phase 0 Step 0.5 — Define failure and input behavior

Parent: [plan.md](plan.md), Step 0.5.

## Check performed

Confirmed the plan's Step 0.5 failure/input table is implementable with nctl's existing error and
envelope conventions, rather than requiring a new error-handling mechanism.

- `nctl_core/nautobot.py` already defines a small exception hierarchy — `NautobotError` (base),
  `NautobotConnectionError`, `NautobotAuthError`, `NautobotGraphQLError` — which distinguishes
  connection, auth, and GraphQL failure today. This is the natural place to add a Braindump-facing
  error (e.g. an "unknown ID" / "duplicate review" case) rather than inventing a parallel hierarchy.
- `cli/main.py` uniformly ends each command with
  `raise typer.Exit(EXIT_OK if envelope.ok else EXIT_FAILURE)`, and validation/config failures use a
  distinct `EXIT_USAGE` exit path (`except (ConfigError, ValidationError) as exc: ... raise
  typer.Exit(EXIT_USAGE)`). This confirms the plan's row "API/auth failure -> no local fallback
  store and no partial success claim" and "Unknown Braindump ID -> structured target-local command
  error" both map onto exit codes/envelope shapes that already exist, rather than requiring new CLI
  plumbing.
- No code currently touches Braindumps (the feature doesn't exist yet), so there is nothing to
  verify live for whitespace validation, Unicode round-trips, or the create-or-replace review
  semantics; those remain Phase 1/2 test obligations exactly as Step 0.7 already lists them.

## Result

The plan's Step 0.5 table (arbitrary Unicode preservation, empty/whitespace rejection, contradictory
prose stored unchanged, review replacement semantics, missing review as normal state, unknown-ID
error, explicit deletion confirmation, no local fallback on API/auth failure, stored-not-executed
text) requires no new nctl error-handling concept — it fits the existing `NautobotError` hierarchy
and `envelope.ok`/`EXIT_USAGE`/`EXIT_FAILURE` exit-code pattern. No edit to `plan.md` was required.
