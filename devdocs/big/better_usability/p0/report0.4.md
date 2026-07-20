# Phase 0 — Step 0.4 report: Specify derivation, override, and provenance contracts

Parent: [plan.md](plan.md) Step 0.4.

## What was done

Added `field-classification.md` §4: the common provenance contract (effective value / source kind
/ source reference / override-won flag / finding), the full derivation/override rulebook table for
every Derived and Override row identified in §2–§3, the roadmap-required minimum scenario matrix
(9 rows), and the Phase 2 persistence-shape decision.

## Key design outcome: `actual_state_policy` doesn't need to be its own stored field

The most consequential finding in this step: `DesiredNodeOperationalConfig.actual_state_policy`
(today required, no default — the field whose absence triggers the global `ContractError` at
`composer.py:185`) reduces entirely to *whether a declared-platform override
(`declared_host_os`) is present for the node*. There is no independent fact `actual_state_policy`
carries beyond that. Recommending it be **computed, not stored**, removes an entire required field
rather than merely defaulting it — a stronger simplification than the roadmap's own framing implied
going in.

## Connection-path derivation, spelled out precisely

`connection_path` + `local_endpoint` + `tailscale_endpoint` derive from `DesiredEndpoint` topology:
exactly one usable-local endpoint (today's case for all 5 live nodes) picks itself; multiple
endpoints with exactly one designated `primary` pick the primary; multiple with no designated
primary is an explicit ambiguity finding, never an arbitrary/lexical winner; Tailscale is never
auto-selected — it is always an explicit override. Zero usable-local endpoints leaves the node
bootstrap/mDNS-exportable but production-connection-undecidable, surfaced as a local finding, not a
crash or a silent skip.

## Phase 2 shape decision: dissolve, confirmed by evidence

The roadmap favored dissolution provisionally; this audit confirms it concretely: zero live
`DesiredNodeOperationalConfig` rows, one programmatic creation path (the import Job), and every
ordinary-case value computable from data the system already owns. What survives is a named,
fully-optional override record carrying exactly the fields already agreed to be "the model done
right" (`declared_host_os`, `tailscale_endpoint`, `ansible_port`, `power_control`, `is_laptop`, plus
a forced non-default `local_endpoint`/`connection_path`) — the required-ness is what's removed, not
the concept. `nintent_operational_config_id` in the production contract needs to be replaced or
removed per roadmap instruction; `nintent_desired_node_id` already covers the same provenance need.

One minor finding carried forward: `DesiredServicePlacement.assignment_source` has two reserved
choice values (`"generated"`, `"policy"`) accepted by the loader's validation set but written by no
code anywhere today — consistent with a future auto-placement/policy-engine feature, not a defect,
noted for whoever eventually builds that.

No blocking surprises requiring human judgment.

## Next step

Step 0.5 — build the consumer and transition impact map: trace every classified field into its
runtime readers (§5b) and record the required Django migration, existing-row policy, output-schema
bump, coordinated nintent/nctl rollout order, and rollback point for each target schema change.
