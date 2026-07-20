# Phase 2 Step 2.8 — Coordinated deployment and live verification

Parent: [plan.md](plan.md), Step 2.8.

## Backup and rollout boundary

- Rechecked the pre-migration live `DesiredNodeOperationalConfig` row count through the old ORM:
  **0**.
- Created and archive-listed a custom-format backup of the Nautobot database at
  `.local/backups/nautobot-pre-p2-20260721.dump` (git-ignored, **1.4 MiB**). SHA-256:
  `2069c999476ad48219a6ec239c552d08295f563d768eddf01674e2abc1bac2c1`.
- Confirmed both GitHub URLs used by the local workflow resolved to the requested commits before
  each build. The final image resolved nintent commit `2ba5402`.
- Rebuilt all three Nautobot images without cache, recreated web/worker/scheduler, and confirmed
  all containers and Nautobot health backends healthy.

## Migration

`0010_operational_overrides_and_provenance` applied successfully. The first explicit migration
check then exposed pre-existing migration-state drift for inherited Nautobot `PrimaryModel`
fields, including the new override model. Work stopped for operator direction as required.

With approval, `0011_align_primary_model_inherited_fields` was added. Before deployment:

- `makemigrations --check --dry-run` reported no changes with `0011` present;
- `sqlmigrate` showed every operation as a database no-op, aligning Django state without changing
  existing tables; and
- the nintent suite remained **89 passed**.

After the second coordinated push/build, `0011` applied. Final `showmigrations` marks `0010` and
`0011` applied, `makemigrations --check --dry-run` reports no changes, and an explicit migrate is
no-op. The only system-check warning is the existing RawSQL placement-config constraint warning;
database, storage, migration, and Redis health checks all pass.

## GraphQL cutover

Read-only schema/data checks confirmed:

- `desired_node_operational_overrides` is present;
- `desired_node_operational_configs` is absent;
- node/endpoint source metadata fields are queryable;
- live counts are **5 nodes, 5 endpoints, 0 overrides**; and
- all **5 nodes remain planned**. Endpoint and node-link source inconsistency counts are both
  zero.

No old nctl revision was run against the new server.

## Read-only nctl verification

The exact no-output/no-apply commands from the plan were run with JSON streamed directly to a
bounded summary; no JSON or inventory artifact was saved.

### `nctl render production --json`

- Envelope: `nctl.render.production.v1`, **ok**.
- Report schema: **2.0**.
- Summary: eligible 0, included 0, skipped 0, placements 0, active placements 0, inactive
  placements 0.
- No errors. `active_placement_not_applied` remains visible in report drift as expected while
  nodes are planned.

### `nctl drift --json`

- Envelope: `nctl.drift.v1`, **ok**; 6 targets.
- Status summary: converged 4, unknown 1, drifting 1.
- Severity summary: error 3, warning 4, info 5.
- All five node targets contain `derived_value_provenance` INFO.
- No `missing_operational_config` or dead expected-OS mismatch code exists. Current live findings
  are the retained lifecycle, missing actual/link/IP/interface, and service-observation findings.

### `nctl reconcile --json`

- Envelope: `nctl.reconcile.v1`, **ok**, state `planned`, rounds 0.
- No unclassified-code failure and no unsupported finding.
- Manual findings are `active_placement_not_applied`, `missing_interface_candidate`, and
  `no_realized_object`; no mutation or Ansible action ran.

## Final repository check

The root and every submodule are clean before this report. No token, live UUID list, unrestricted
actual facts, dashboard output, drift JSON, or generated production inventory was added to Git.
The final tested component commits are nintent `2ba5402`, nctl `54f7fda`, and nauto `55eb63d`.
