# Phase 3 Step 3.7 — Deploy once and perform the reviewed live transition

Parent: [plan.md](plan.md), Step 3.7.

This step paused twice for operator direction, as required: once before the deploy sequence itself
(push/rebuild/migrate/promote is hard to reverse and touches the live Nautobot and real PCs), and
once before running `nctl reconcile --yes` against real hosts. Both pauses and their answers are
recorded below.

## Backup and rollout boundary

- Rechecked the pre-migration live `desired_nodes` lifecycle count: **5, all `PLANNED**
  (`agbach`, `agdnsmasq`, `aghub`, `agpc`, `agstudio`), matching every earlier step's precondition.
- Created a custom-format backup of the Nautobot database at
  `.local/backups/nautobot-pre-p3-20260721.dump` (git-ignored, **1.4 MiB**). SHA-256:
  `d499621a3dfb6d9b626fa0a59b75d2cc50f832f562e6bd585888f03c1563971b`.
- Confirmed the nintent commit was pushed by the operator (`e018ffe`, "Demonstrate omitted
  lifecycle in YAML examples") before building; the build log resolved that exact commit through
  `pip install git+https://github.com/iwaag/nprojects.git`.
- Rebuilt the `nautobot`, `nautobot-worker`, and `nautobot-scheduler` images without cache and
  recreated all three containers; all reported healthy.

## Migration

Nautobot's entrypoint applied `0012_desired_node_lifecycle_default_active` automatically on
container start (no manual `migrate` was needed, though one was run explicitly afterward as a
no-op check). `showmigrations nautobot_intent_catalog` shows `0001`–`0012` all applied;
`makemigrations --check --dry-run` reports no changes; an explicit `migrate` after that is a no-op;
`nautobot-server check` reports no issues. Server-side model introspection
(`DesiredNode._meta.get_field("lifecycle").default`) confirms **`active`**, matching Step 3.3's
code change exactly. GraphQL/REST shape is otherwise unchanged (no field added/removed), consistent
with Decision 6's compatible-rollout premise.

## Existing-row verification

Requeried live `desired_nodes` lifecycle immediately after the rebuild, before any promotion:
still **5 nodes, all `planned`** — the migration changed only the Django-level default, not a
single existing row, exactly as Decision 4 specifies.

## Reviewed live transition

Presented each planned node's drift status, realized-object linkage, and the local-env
reachability notes (`agbach`/`agdnsmasq` known-unreachable-but-accepted, `agpc`/`agstudio`
confirmed-reachable) to the operator for review, per Decision 4 ("five personal-cluster rows are
small enough to make the one-time decision explicit").

**Operator decision**: promote `agpc` and `agstudio` only. `agbach`, `agdnsmasq` (has a recorded
`active` dnsmasq placement that stays honestly visible as `active_placement_not_applied`), and
`aghub` (no realized device/vm at all — looks unprovisioned) remain `planned` by explicit choice,
not by omission.

```
$ nctl lifecycle agpc active --json      # planned -> active, changed=true, confirmed
$ nctl lifecycle agstudio active --json  # planned -> active, changed=true, confirmed
```

Both PATCHes were confirmed via the GraphQL refetch the command itself performs (Decision 2, step
5) before reporting `changed=true`.

## Post-promotion drift/reconcile review

Host-scoped drift for both promoted nodes flipped from `converged` (invisible, because the node was
out of production scope) to `unknown` with a new `stale_actual_data` error — this is Phase 3
working as intended: recorded intent that is now live surfaces its real mechanism gap instead of
staying silently unevaluated. Dry `nctl reconcile <host>` plans for both were clean (no
`manual_review` items, no errors).

**Second operator checkpoint**: asked whether to run `nctl reconcile <host> --yes` for `agpc`/
`agstudio`, since that triggers real SSH/nodeutils-collection activity against the operator's
machines, a materially different risk class than the read-only/PATCH-and-refetch work up to that
point. Operator approved running it for both.

`nctl reconcile agpc --yes` and `nctl reconcile agstudio --yes` both ran one round, ended
`non_converged` with error `no_progress` (drift fingerprint unchanged), and each round's single
`observe_node` action failed with `"<host>: report is stale: collected_at=2026-06-26T15:28:41+00:00"`
— the same stale timestamp `nctl status` had already flagged for `agstudio.local` at the start of
this phase. This is a real infrastructure fact (stale/failed nodeutils collection against the live
hosts as of 2026-07-21), not a Phase 3 defect: `regenerate_production_inventory` still succeeded in
both runs, and per Decision 4/plan.md "known unreachable hosts may remain active with visible local
findings; do not claim them converged or demote them merely to make the dashboard green," neither
node was demoted or force-marked converged. Resolving the underlying collection staleness is
outside this phase's scope (a lifecycle-default/tooling phase, not an infrastructure-connectivity
fix) and is left for the operator.

## Final drift snapshot

```
node agdnsmasq  converged  active_placement_not_applied(warning), missing_actual_ip_address(warning)
node agbach     converged  (no local findings beyond provenance)
node aghub      unknown    missing_actual_node(error), no_realized_object(error), missing_interface_candidate(warning)
node agpc       unknown    stale_actual_data(error)
node agstudio   unknown    stale_actual_data(error)
service dnsmasq drifting   service_missing(error)
```

Every finding here is pre-existing/expected given the reviewed decisions above — nothing was hidden
and nothing was forced to a false "converged" state.

## Result

- Migration `0012` is applied, default-only, and left every pre-existing row untouched.
- `agpc`/`agstudio` are now `active` by explicit, confirmed operator decision; `agbach`/
  `agdnsmasq`/`aghub` remain `planned` by explicit choice.
- `nctl lifecycle` is proven end to end against the live server: PATCH, refetch-confirmation, and
  idempotence all behaved exactly per `nctl.lifecycle.v1`'s contract.
- No token, unrestricted live facts, dashboard/drift artifact, or generated production inventory
  entered Git. Final tested/deployed component commits: nintent `e018ffe`, nctl `e804620`, nauto
  `55eb63d`.
- The real-world staleness of `agpc`/`agstudio`'s nodeutils collection is recorded here as a known,
  visible, un-actuated finding — exactly the "derive aggressively, but legibly" outcome this
  roadmap's premises call for, and is a follow-up for the operator outside this phase's scope.
