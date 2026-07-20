# Phase 0 — Step 0.6 report: Classify production failures for Phase 1

Parent: [plan.md](plan.md) Step 0.6.

## What was done

Exhaustively grepped every `raise ContractError(...)` site across `production/composer.py` and
`production/contract.py` (57 total: 1 + 56) and extracted every literal code string, including the
ones hidden inside multi-line raise statements that a simple line-range citation would have missed.
Grouped them into three scopes per `composer.py`'s own documented split (shared profile-schema
validation, final closed-output-contract validation, per-node/per-placement composition), added the
new "recorded but not applied" finding the roadmap requires, and cross-referenced the existing
correctly-local `_host_actual_skip_reasons` codes for contrast.

## The central finding

**Every one of the 15 per-node/per-placement `ContractError` codes in Group C is invisible to
`reconcile/classify.py`'s `CODE_CLASSIFICATION` table today** — not because they're
misclassified, but because they never reach `classify()` in the first place. Every `ContractError`,
regardless of where it's raised, is caught only at the outermost boundary
(`production_render.py:73-82`, `drift/comparators.py:185-201`) and converted into one
`Target(kind="global")` diff, which `classify()` routes straight to `_GLOBAL_CLASSIFICATION`
without ever consulting the per-code table. The moment Phase 1 changes any of these 15 codes to a
node- (or placement-) scoped target, `classify()` will look each one up for the first time — and
since none are registered, every one would raise `UnclassifiedDiffCodeError` unless Phase 1 adds
all 15, not just the one (`missing_operational_config`) the roadmap names by example. This is the
concrete mechanism behind the roadmap's own warning about that failure mode, now traced to its
exact cause and its exact scope (15 codes, not 1).

## Other findings

- **`invalid_connection_address` is raised from two different call sites** — once inside per-node
  connection resolution (local) and once during document-level IP normalization in the final report
  validation (global). Phase 1 must distinguish *which* call site fired it rather than
  blanket-classifying by code name; recorded explicitly in the table so this isn't rediscovered
  later as a bug.
- **`unknown_profile`, `unsupported_config_schema`, `invalid_placement_config`,
  `unknown_config_key`, `missing_required_config`, and `invalid_profile_value_type` are all raised
  from `map_placement_config`, which is placement-scoped, not node-scoped** — Phase 1's
  implementation plan must decide whether `Target.kind` for these is `"node"` (attributing the
  failure to the host it would have landed on) or a new `"placement"` kind, rather than Phase 0
  presuming one. Flagged as an explicit open decision for Phase 1, not resolved here since it's an
  implementation-shape choice, not a tier/schema question this phase owns.
- Proposed the new finding code `placement_config_not_applied` (name subject to Phase 1's own
  naming pass) for discussion.md's Example 1 scenario, with severity `WARNING` and classification
  `MANUAL_REVIEW` (the only real fix is a human decision — promote the node, or accept the
  placement is intentionally inert).
- Every proposed classification is `MANUAL_REVIEW` — none of Group C's failures are automatically
  fixable by an existing `AUTOMATIC`/`OBSERVATION` reconciler, which keeps Phase 1's actual code
  change simple (a table addition) even though the underlying finding-count is larger than the
  roadmap's single named example.

No blocking surprises requiring human judgment.

## Next step

Step 0.7 — assign every contradiction and transition item identified across §2–§6 to exactly one
owning phase, and perform the roadmap's required consistency review (Phase 3 hard-blocked on
Phase 1+2, no Derived field required as human input, every Override optional/validated/visible,
etc.).
