# Phase 3 — Step 3: follow-on cycle decision — skipped, with reasons

Date: 2026-08-04. Executes (by explicit skip) Step 3 of [`plan.md`](plan.md),
which is conditional: "If the diagnosis instead ends the matter (finding
recorded, no fix wanted), say so and skip to Step 4."

## Why no follow-on execution cycle runs in this phase

Step 1's diagnosis found all three drift findings to be **observation
defects** — nothing on the cluster is actually mis-deployed. The concrete
fixes it points at are therefore not cluster operations at all:

1. **Observer process-visibility gap** (swarmui/comfyui run as
   StabilityMatrix user processes the observer cannot see) — a `nodeutils`
   collector change.
2. **Substring false positive** (`prometheus-node-exporter.service`
   reported as service `prometheus`) — a `nodeutils` matching change.

Both are exactly the class the phase plan's time-separation split routes
through **episode → human selection → separate workflow-improvement
session**: they are improvements to cluster observation code prompted by a
run's pain, not fixes to the workflow-agent protocol itself. They are
recorded as `improvement_candidates` in episode
`2f2d3de6-039a-4a36-a6a6-152da8a92d51` (Step 2), which is `candidate` and
awaits human survey. Executing them now, in the same session that produced
the episode, would violate the convention this phase explicitly binds
itself to.

The one remaining possible *cluster* action — deciding what the
`prometheus` Service row with no active placement should become (delete it
as leftover, or keep it for a future deployment) — is a desired-state
choice only the user can make; nothing in the diagnosis shows it is wanted
now. No mutation is speculatively planned for it (planning-manual rule:
don't write a destructive step while the target's intent is unclear).

## Consequences accepted

- Marked-plan v2 handling (interactive y/N at the approval boundary)
  remains unbuilt — no real run needed a marked step. It stays a
  known-deferred item, per the phase plan's "only if a real run forces it".
- The swarmui/comfyui/prometheus drift entries remain visible in
  `nctl drift --json` until a workflow-improvement session lands the
  observer fixes (or the user decides otherwise). This is the recorded,
  explained state — not an unexplained finding anymore.

Proceeding to Step 4 (phase report + evaluation note).
