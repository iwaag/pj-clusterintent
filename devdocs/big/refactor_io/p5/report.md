# Phase 5 Report — Cutover verification and simplification

## Result

Complete. The normal ownership boundary is now verified on the persistent local
scratch Nautobot environment:

```text
private local batch document -> batch REST (only desired-state writer)
                         -> Nautobot database (current desired state)
                         -> GraphQL (desired-state reader) -> nctl
Git -> framework, policy, synthetic fixtures, and Nautobot prerequisites
```

The root, nintent, nauto, nctl, and local-environment documents state this
model. Phase 5 also removed stale nctl prose that still described lifecycle
writes and the intent-catalog ViewSets as PATCH-based desired-state writers;
the implementation already used one-operation calls to the canonical batch
endpoint.

The Nautobot runtime-gate runner had a false concurrent-test detection: its
process scan matched the scan command itself. It now recognizes only the
actual `nautobot-server test` Python process, so it continues to protect the
shared `test_nautobot` database without refusing every invocation.

## Local acceptance

- A one-object `desired_node` batch dry run returned `create=1` and did not
  commit.
- A mixed committed batch returned exactly one create, one lifecycle update,
  and one delete. All three synthetic rows were then removed.
- An intentionally invalid mixed batch returned HTTP 409. Its preceding
  synthetic create was absent afterwards, proving atomic rollback.
- `nctl lifecycle` changed a synthetic node from `approved` to `active` and
  back to `planned`, confirming both writes through GraphQL. The lifecycle
  writer uses the canonical batch endpoint.
- A local synthetic `dcim.Device` was linked to a synthetic desired node by
  `nctl_core.reconcile.ledger.execute_link_actual_node`; its batch write was
  confirmed by GraphQL. Both fixture rows were deleted afterwards.
- A bounded `nctl reconcile p5-link --yes` was exercised. It stopped safely
  before action because the synthetic host had no enrolled SSH trust entry;
  no SSH/Ansible or external cluster mutation was attempted. Its durable
  operation ID was `01KYQHDRH1CTQEZKY1RJGC9304`.
- After cleanup, the private document dry run again reported all 27
  operations unchanged. GraphQL returned 6 nodes, 6 endpoints, 3 IP ranges,
  6 services, 1 placement, 1 compute platform, and 1 compute instance.
- The local Nautobot compose stack was restarted. `/opt/nautobot/intent_sources.yaml`
  remained absent, and the same 27-operation dry run and GraphQL read passed
  after the API became ready. No private seed file is needed for restart.

The cluster-wide `nctl drift --json` remains non-converged because of existing
compute/observation findings (including the missing compute primary endpoint
for `agdnsmasq`); Phase 5 did not change desired or actual cluster state to
hide those findings.

## Gates

| Gate | Result |
| --- | --- |
| nctl ordinary | 987 passed |
| nauto ordinary | 110 passed |
| nintent Django-free | 124 passed, 10 expected runtime skips |
| Nautobot runtime clean | passed; staged exact-local sources, `makemigrations --check` reported `No changes detected`, 173 runtime tests collected |

No supported code path or runtime image references `intent_sources.yaml`,
`/opt/nautobot/intent_sources.yaml`, or `intent_sources_file`. Historical
references under `devdocs/` are retained as records of the cutover.
