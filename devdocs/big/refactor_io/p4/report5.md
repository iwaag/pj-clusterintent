# Phase 4 Step 5 Report — Live rebuild handoff

## Result

Complete. After the operator pushed the component commits, `NAUTO_COMMIT` was
set to `3bd1820fa19bc9603bdf20033a54468afc359c1a`. A no-cache rebuild resolved
and verified the pinned nintent revision, then created images whose
`build_info.json` records that pushed nauto SHA. `docker compose up -d` and
`nautobot-server post_upgrade` completed; no migrations were required.

`/opt/nautobot/intent_sources.yaml` is absent from the rebuilt container. The
database survived the rebuild: a batch dry run found all 27 private-document
operations unchanged (2 intent sources, 6 nodes, 6 endpoints, 3 ranges, 1
platform, 2 instances, 6 services, and 1 placement), and `nctl drift --json`
returned `ok: true`.

The desired-state GraphQL reader returned the same normalized current-set
counts: 6 nodes, 6 endpoints, 3 IP ranges, 1 service placement, 6 services,
1 compute platform, and 2 compute instances (with no operational overrides or
dependencies).

During the first `post_upgrade`, the pre-existing default Nautobot setting
sent installation metrics. No credential or desired-state payload was emitted.
Following the local-environment policy, the configuration now defaults that
telemetry to disabled and the recreated container confirmed the setting is
`False`; future runs require an explicit environment opt-in.

## Gates

| Gate | Result |
|---|---|
| nauto ordinary | 110 passed |
| nintent Django-free | 124 passed, 10 expected runtime skips |
| nctl ordinary | 987 passed |
| compute conformance | 1 passed |
| Ansible conformance | 2 passed |
| Nautobot runtime clean | passed; `makemigrations --check` reported `No changes detected` |

## Pushed component commits

- nauto: `3bd1820 Remove desired state seed from Git`
- nctl: `7c64438 Document private desired-state batch workflow` and
  `95afdd8 Sanitize desired-state test fixtures`
- nintent: `fdc76c9 Clarify desired state is not Git-held` and
  `d388049 Use synthetic compute conformance endpoint`
- superproject baseline before the live proof: `482241c Complete refactor IO
  phase 4 step 4`
