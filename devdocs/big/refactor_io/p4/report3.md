# Phase 4 Step 3 Report — Sanitize committed desired data

## Result

Complete. The compute-contract semantic owner now uses the documentation MAC
`aa:bb:cc:dd:ee:01`, and the nctl consumer fixture was regenerated from that
owner. The nctl actual-snapshot fixture, the Ansible conformance fixture, and
their assertions now use `example-*` names, documentation addresses, and
`aa:bb:cc:*` MACs. The previously committed cluster desired-state identifiers,
addresses, and MAC are therefore absent from those fixtures.

## Decisions

- Kept `devenv/nautobot/docker-compose.yml`'s allowed local hostname and the
  historical OpenSSH narrative in `README_DEV.md`: both are local-environment
  facts, not desired-state rows.
- Kept the generic private-network webhook block in `nautobot_config.py`: it
  is a Nautobot security policy example, not cluster intent.
- Kept real observation-shaped inputs in the actual-state suites named in the
  plan: `nauto/tests/test_proxmox_*.py`,
  `test_ip_namespace_host_identity.py`, `test_nodeutils_ingest_batch.py`, and
  `nodeutils/tests/`. They reproduce observed Proxmox/nodeutils payloads, so
  are outside the desired-state-data removal boundary. The nctl fixture called
  out explicitly by the plan was converted because its data is a committed
  consumer fixture rather than an ingest payload.

## Verification

| Gate | Result |
|---|---|
| nintent Django-free | 124 passed, 10 expected runtime skips |
| nctl ordinary | 987 passed |
| compute conformance | 1 passed |
| Ansible conformance | 2 passed |

## Component commits

- nintent: `d388049 Use synthetic compute conformance endpoint`
- nctl: `95afdd8 Sanitize desired-state test fixtures`
