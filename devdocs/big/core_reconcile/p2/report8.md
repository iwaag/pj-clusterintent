# Phase 2 Report — Step 8 (documentation and phase closeout)

Date: 2026-07-15. Implements [p2/plan.md](plan.md) Step 8 and closes Phase 2.

## Documentation updates

### nctl

`nctl/README.md` now documents:

- `nctl drift`, `--host`, `--service`, success-vs-run-failure exit semantics, and the
  `nctl.drift.v1` payload (`summary`, `severity_summary`, `targets`, `sources`, `generated_at`);
- the three-source model: nintent desired state, Nautobot actual ledger state, and nodeutils
  observed dumps;
- `converged`, `drifting`, `converging`, and `unknown` target status rules and structured diff
  evidence fields;
- `nctl render production`, its `nctl.render.production.v1` data fields, direct
  `deployment_profiles.yml` read, staged `ansible-inventory` validation, immutable report, and
  atomic inventory replacement;
- comparator extension through `@register("node" | "service")`, the
  `SourceSnapshot`/`DriftContext` input boundary, deterministic sorting, and test expectations.

The parent `README.md` now exposes the four normal nctl entry points and states the final ownership
split: nctl compares/transforms, nintent stores desired state, Nautobot stores actual ledger state,
nodeutils supplies observations, and Ansible actuates.

### nintent

`README.md`, `README_QUICK.md`, and `README_DEV.md` were updated for nintent 0.6.0:

- removed operator/developer instructions for Quick Service Placement, profile projection/sync,
  Evaluate Jobs, and production export;
- documented the five retained Jobs and the surviving CRUD/YAML placement paths;
- documented fresh nctl comparator/MAC computation and `nctl drift --json` as the reconciliation
  surface;
- clarified that `Reconcile Desired IPAM Intent` remains a transactional write but no longer
  persists evaluation side effects;
- moved production/profile/evaluation test ownership to nctl and retained only ledger input
  reference validation in `intent_contract.py`.

The ansible_agdev README and production contract documentation were already updated in Step 7.
Historical plans, reports, migrations, and dev logs intentionally retain the old names as a record
of the migration; they are not current operator instructions.

## Phase 2 design outcomes

### Decision 1 — evaluations are computed, not persisted

`IntentEvaluation` and the Evaluate Node/Endpoint/Service Jobs are gone. nctl comparators compute
node, endpoint, range, service, platform-policy, and DHCP-MAC findings from one current
`SourceSnapshot`. `render dnsmasq` consumes that fresh computation, so no manual evaluation Job or
staleness window remains.

### Decision 2 — processing moved rather than sharing Django

nintent retains ORM storage, import/analyze operations, bootstrap export pending Phase 1.5, and the
transactional IPAM Job. Phase 2 production/evaluation/consumer processing lives in typed
`nctl_core` read models and pure functions behind pinned GraphQL queries. No Django-dependent shared
package was introduced.

### Production composition and the byte contract

`nctl render production` owns composition. It reads the Ansible-owned profile map directly. The
old production export Job, sync Job, projection model, canonical-JSON/digest transport, verify/sync
playbooks, and serialization task are deleted. The digest remains only as locally calculated schema
1.0 provenance.

## Query and parity record

The detailed pinned-query and parity procedures remain in the step reports:

- [report1.md](report1.md): desired/actual GraphQL query names/fields, nodeutils typing, and the
  REST fallbacks for DesiredServicePlacement and DesiredNodeOperationalConfig caused by Nautobot
  GraphQL resolver failures.
- [report2.md](report2.md): live production Job-vs-nctl parity, including normalized generation
  metadata and the exact inventory/report comparison.
- [report3.md](report3.md): comparator registry, status derivation, and deterministic ordering.
- [report4.md](report4.md): Evaluate Job parity and dnsmasq byte-parity before/after the fresh MAC
  source switch.
- [report5.md](report5.md): `nctl.drift.v1` CLI/envelope live behavior.
- [report6.md](report6.md): nintent deletion/migration boundary.
- [report7.md](report7.md): deployed nintent 0.6.0 gate and ansible_agdev cleanup.

No new REST fallback was added in Steps 5–8.

## Exit criteria

- [x] Live `nctl drift --json` returned all five cluster nodes in one run with structured diffs:
  three `converged`, two `unknown`, two error and nine warning diffs.
- [x] Comparators register per resource type and the core requires no comparator-specific branch.
- [x] Production output passed the live old-Job parity gate and the current nctl-owned
  `make production-inventory` path writes a validated production inventory/report.
- [x] The deployment-profile byte transport, sync/export playbooks/Jobs, and projection are gone.
- [x] Evaluate Jobs/model are gone; dnsmasq parity passed; nintent 0.6.0 is deployed; live
  `nctl status`, `drift`, `render dnsmasq`, and `render production` are green.
- [x] Phase 2 desired-state evaluation/composition logic exists only in nctl_core; nintent retains
  storage/import/transactional boundaries. The hosts-intent renderer remains explicitly assigned
  to the separate Phase 1.5 migration.
- [x] Final local suites pass: nctl **236 passed**, nintent **92 passed**.

All checkboxes in `p2/plan.md` were updated accordingly.

## Known follow-ups, not Phase 2 blockers

- `agdnsmasq.local` still does not resolve, so the Phase 1 real `nctl apply dnsmasq --yes` proof
  remains environment-gated. Rendering and post-deletion parity are proven.
- The current live dataset has no operational configs or placements, so the newly generated
  production inventory is valid but empty. The earlier live old-Job parity fixture covered populated
  composition cases before deletion.
- `makemigrations --check` in Nautobot 3.1 proposes inherited PrimaryModel tags/id/custom-field
  alignment for all surviving nintent models. Migration 0008 itself is applied and no deleted-model
  delta remains; the broad inherited-field migration is a separate maintenance decision.
- Service targets currently lack a wired observed-facts provider and therefore surface
  `service_observed_facts_unknown`; service observation integration can be added by a later
  comparator/source change.
- Phase 1.5 hosts-intent migration, the Phase 3 dashboard, and Phase 4 reconciliation orchestration
  remain future roadmap work.

## Commit boundary

Step 8 consists of documentation-only changes in the nctl and nintent submodules plus the parent
README, completed plan checklist, and this report. No commit was created. The submodule documentation
changes should be committed first, followed by the parent repository submodule-pointer/documentation
commit.
