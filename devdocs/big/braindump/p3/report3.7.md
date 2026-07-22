# Step 3.7 — Run a separate scoped reconcile, observe again, and replace the review

Status: complete after the separately approved `fix_sshkey4` follow-up on 2026-07-22. The original
operation and its safe failure remain recorded below as historical evidence.

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

## 4. Review and next gate at the original safe stop

The LAN and onboarding-policy Alignment Reviews were replaced in place to record the fresh
observation, successful IPAM result, and failed apply. Their review UUIDs remain
`e28d37c8-4916-4b26-8a36-862f93131aab` and `f2b5e92f-edd2-48b5-9349-e8c10eefbd22`.

Correcting the production-inventory SSH host-key path requires a separately reviewed change and a
new explicit apply approval. Until then, the honest terminal state for this operation is
`non_converged`, even though fresh drift sees the dnsmasq service as converged.

## 5. Follow-up completion evidence

The SSH identity problem was corrected through the separately planned `fix_sshkey` through
`fix_sshkey4` work. Bootstrap and production inventories now use one stable
`nctl-node-<DesiredNode UUID>` `HostKeyAlias`, one private nctl-managed known_hosts store, and strict
host-key checking. Changing the route from `agdnsmasq.local` to `192.168.0.2` no longer creates a
second trust identity or requires a policy bypass.

After separate user approval, `fix_sshkey4/report_step7.md` ran a reversible live content change:

- plan `01KY4FJRGC806SBESZS1GG7EF2` named exactly one `dnsmasq_config` action for
  `host_slugs: ["agdnsmasq"]` plus the pre-existing IPAM action;
- apply `01KY4FKNFXQPAX53SRJDX3KZ25` recorded a ready same-generation production preflight for
  route `192.168.0.2`, port 22, the UUID-derived alias, and matching managed/offered fingerprints;
- both playbooks ran with `--limit agdnsmasq`, the managed records file was deployed, nodeutils
  re-observed the same metadata-owned path and matching SHA-256, and the next round planned no
  repeated `dnsmasq_config` action;
- the temporary endpoint was then deleted through the same REST owner; reverse plan
  `01KY4G17R75SBGBWEG5GAM3QW0` and apply `01KY4G1ECY07T2YK3XKQ4MPE67` restored the original content
  digest and again converged without a repeated configuration action; and
- the overall envelopes remained `non_converged` only because of the pre-existing repeated-IPAM /
  `missing_actual_ip_address` condition. The dnsmasq service target itself was `converged` with zero
  diffs after both directions.

A current production-inventory Ansible ping also succeeds with strict checking and `changed: false`.
The latest agdnsmasq actual evidence used by drift is `2026-07-22T08:46:17Z`; current drift reports
both the agdnsmasq node and dnsmasq service as `converged`.

On 2026-07-22 the LAN and onboarding-policy reviews were replaced in place with this successful
result. Their UUIDs remain `e28d37c8-4916-4b26-8a36-862f93131aab` and
`f2b5e92f-edd2-48b5-9349-e8c10eefbd22`; their Braindump bodies and authorship did not change.

## Discrepancies

None for the Step 3.7 SSH-backed configuration criterion. The unrelated IPAM warning remains
visible and is not reclassified as a Phase 3 or dnsmasq failure.
