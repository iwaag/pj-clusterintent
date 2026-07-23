# Permission Fix Investigation Report 2

Date: 2026-07-23

## Status

**Complete for agstudio.**

- agstudio's stale schema-v1 observation was replaced through the supported nctl workflow.
- Verified SSH enrollment, pinned nodeutils deployment, collection, retrieval, Nautobot ingest,
  production inventory regeneration, and fresh drift all succeeded.
- `nctl drift --host agstudio` now reports `converged`.
- The schema-v1 `inventory.json` was not an unrelated file to delete: because the controller is
  agstudio, it is also that target's configured remote report path. Collection safely replaced it
  in place with schema v2.
- A newly exposed source-scan defect was fixed locally: nctl no longer tries to parse its own
  `nctl-probe-config.yaml` as a nodeutils inventory dump.
- The Proxmox/root-only `pvesh` problem on aghub is unchanged and remains open.
- The nctl code and this report are not committed or pushed.

## Initial state

Before repair, `nctl drift --host agstudio --json` reported:

```text
status: unknown
error: stale_actual_data
collected_at: 2026-06-26T15:28:41+00:00
```

The controller dump directory contained:

```text
/var/lib/nodeutils/agdnsmasq.json  nodeutils.inventory.v2
/var/lib/nodeutils/agpc.json       nodeutils.inventory.v2
/var/lib/nodeutils/inventory.json  nodeutils.inventory.v1, hostname=agstudio.local
```

The schema-v1 `inventory.json` was the remaining entry in `sources.observed_errors`.

An explicit refresh dry plan initially stopped at the strict SSH boundary:

```text
operation_id: 01KY70RE6PDGCFD642B4Q2N1BN
scope: agstudio
state: planned
ssh_preflight: unenrolled=[agstudio]
```

The plan correctly contained one forced `observe_node` action with
`evidence.forced_refresh=true`; no writes occurred.

## SSH enrollment

The ordinary OpenSSH known_hosts store contained currently offered agstudio keys, so the nctl
alias was enrolled from that already verified source:

```bash
uv run --project nctl nctl ssh enroll agstudio --from-known-hosts --yes
```

This created the nctl-managed alias entry without automatic or unverified trust. A subsequent
refresh dry plan succeeded:

```text
operation_id: 01KY70VY0HA044E7CF980ZWYDZ
scope: agstudio
state: planned
ssh_preflight: ready=[agstudio]
```

## Live refresh and convergence

The supported forced-observation workflow was applied:

```bash
uv run --project nctl nctl reconcile agstudio --refresh-observation --yes
```

Operation `01KY70W3Q2GCYJ81AJ384WV2WA` completed:

```text
state: converged
scope summary: converged=1
ssh_preflight: ready=[agstudio]
round 0:
  [ok] observe_node
  [ok] regenerate_production_inventory
```

Collection evidence recorded:

- nodeutils version:
  `e7b91860397abddee07801b438914e59e734ce57`;
- host: `agstudio`;
- `collected=true`;
- controller cache path: `/private/var/lib/nodeutils/agstudio.json`;
- `ingest_outcome=updated`; and
- no host or action error.

The Nautobot ingest Job moved from `pending` to `success` on its second poll. Its summary reported:

```text
total=1
updated=1
created=0
unchanged=0
skipped=0
```

The observation collected at `2026-07-23T08:18:41+00:00` identified Darwin/macOS and produced
schema v2 at both:

```text
/var/lib/nodeutils/inventory.json
/var/lib/nodeutils/agstudio.json
```

This duplication is expected in this local topology: agstudio is both the observed SSH target and
the controller. `inventory.json` is the remote collection output, while `agstudio.json` is nctl's
slug-keyed controller cache. The old generic-name file therefore did not need deletion or
quarantine; it was atomically refreshed in place.

The next reconciliation round planned zero actions and declared convergence.

## Source-scan defect exposed by the refresh

The collection playbook installs:

```text
/var/lib/nodeutils/nctl-probe-config.yaml
```

On a separate remote host that path is outside the controller's dump directory. On agstudio, the
controller and observed host are the same machine, so it appears inside the configured
`dumps_dir=/var/lib/nodeutils`.

`scan_dumps()` discovered every top-level `*.json`, `*.yaml`, and `*.yml` file. It consequently
tried to validate `nctl-probe-config.yaml` as a `NodeDump` and added a false
`sources.observed_errors` entry for missing `schema_version`, `identity`, and `collected_at`.

### Implemented fix

The nctl dump scanner now excludes the exact nctl-owned non-report filename
`nctl-probe-config.yaml` from dump discovery.

The exclusion is deliberately narrow:

- malformed or unsupported JSON/YAML report files are still reported;
- YAML nodeutils reports remain supported; and
- arbitrary invalid files are not silently ignored.

A regression test creates a valid inventory report beside `nctl-probe-config.yaml` and verifies
that the report is loaded with no source error.

## Verification

Focused tests:

```text
9 passed
```

Canonical nctl suite, run from the nctl project directory:

```text
964 passed, 1 warning
```

The warning is the existing Starlette/httpx deprecation warning in `test_serve_ws.py`.
`git diff --check` also passed.

An initial `uv run --project nctl pytest` invocation from the superproject root selected the
superproject as pytest's root and attempted to collect unrelated nintent and nodeutils tests. It
stopped on three missing-environment import errors (`django`, `nodeutils_collect`, and
`proxmox_inventory`). This was an incorrect test working directory, not an nctl test failure; the
canonical `cd nctl && uv run pytest` run above is the relevant result.

Final live verification:

```text
nctl drift --host agstudio
status: converged
severity: error=0, warning=0, info=1
observed_errors: []
```

The derived operational state now includes:

```text
host_os: macos
connection_path: local
connection_address: 192.168.0.100
production.state: included
```

## Remaining work

1. Commit and push the nctl source-scan fix and this report through the normal repository workflow.
2. Design the Proxmox privilege/ownership boundary before changing aghub collection to root.
3. Implement and verify the Proxmox fix with a real aghub observation, ingest, and fresh-drift
   convergence replay.
4. Review the two previously replayed aghub IPAM Job results noted in `report1.md`.
