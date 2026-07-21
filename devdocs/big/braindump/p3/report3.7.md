# Step 3.7 — Run a separate scoped reconcile, observe again, and replace the review

Status: partially complete; the deterministic operation made progress but its dnsmasq configuration
action did not complete.

## 1. Separate apply approval and operation

After the Step 3.6 lifecycle change and a separate dry-plan review, the user approved the exact
`agdnsmasq` scoped reconcile plan. Apply operation `01KY2NZR048X0GKWYBN4DVENW5` ran with scope
`host: agdnsmasq`.

## 2. Successful actions

- `observe_node` collected `agdnsmasq` and ingested the report into Nautobot successfully.
- The new actual/service-inventory timestamps are `2026-07-21T15:51:32Z`.
- Fresh observed services include `dnsmasq`.
- `reconcile_ipam:agdnsmasq` completed without conflicts or skipped items in both attempted rounds.
- Production inventory regeneration and dashboard derived-status refresh completed.
- The final drift summary moved to `converged: 4`, `unknown: 2`; the dnsmasq service target is
  `converged` with no remaining diff codes.

## 3. Failed configuration action

`dnsmasq_config:dnsmasq:dnsmasq` failed during its Ansible daemon-setup phase with exit code 4 and
one unreachable host. A read-only production-inventory ping identified the cause as SSH host key
verification failure.

The two established paths resolve the same node differently:

| Path | Effective connection target | Result |
|---|---|---|
| operation bootstrap inventory | `agdnsmasq.local` | nodeutils collection succeeded |
| production inventory | `192.168.0.2` | SSH host key verification failed |

This is a known-host identity/path consistency issue, not a desired-state, nodeutils, IPAM, or
dnsmasq-observation failure. No destructive retry or host-key override was performed.

## 4. Current review and next gate

The LAN and onboarding-policy Alignment Reviews were replaced in place to record the fresh
observation, successful IPAM result, and failed apply. Their review UUIDs remain
`e28d37c8-4916-4b26-8a36-862f93131aab` and `f2b5e92f-edd2-48b5-9349-e8c10eefbd22`.

Correcting the production-inventory SSH host-key path requires a separately reviewed change and a
new explicit apply approval. Until then, the honest terminal state for this operation is
`non_converged`, even though fresh drift sees the dnsmasq service as converged.

## Discrepancies

The Step 3.7 end-to-end apply criterion is not complete because the dnsmasq configuration action
failed. Its remaining blocker is the `192.168.0.2` SSH host-key verification path.
