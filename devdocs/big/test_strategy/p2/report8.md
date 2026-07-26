# Test Strategy Phase 2 — Completion Addendum: Remaining Queue Dispositions

Parent: [plan.md](plan.md), Steps 1–7 and exit criteria.

Status: **`complete`**.

## Decision

The final audit reviewed all 81 queue groups that remained after the helper allowlist table in
[report1.md](report1.md). They are now explicitly disposed; no group is left merely because it is
old, long, or similar-looking. The audit did not make a deletion quota. A proposed merge was only
permitted where it would retain the same primary contract, diagnostic, authority source, and
layer. None of these groups met that condition without weakening the proof or creating a generic
fixture/table that restated the implementation.

The private `remaining-dispositions.tsv` records the review counts, disposition classes, reasons,
and relevant focused/component results. The exact file-level scope of each class is enumerated in
the matrix below. It is stored with the other restricted Phase 2 evidence in
`.local/test-strategy/p2/20260726T144434Z/`.

## Disposition matrix

| Queue groups | Disposition | Reason |
|---|---|---|
| `nauto/tests/test_ingest_nodeutils_inventory_job.py`, `test_ip_namespace_host_identity.py`, `test_nodeutils_ingest_batch.py`, `test_nodeutils_ingest_summary.py`, `test_proxmox_cluster_vm_upsert.py`, `test_proxmox_ingest.py`, `test_proxmox_interface_ip_upsert.py`, `test_seed_home_cluster_ownership.py` | Retain standalone | Each fixture owns a different ingest/identity/upsert/no-op or native-ownership decision. Combining their fake-ORM shapes would hide transaction, partial-evidence, or write-selection diagnostics. |
| nctl CLI files (`test_cli_actual.py`, `test_cli_apply_dnsmasq.py`, `test_cli_braindump.py`, `test_cli_drift.py`, `test_cli_lifecycle.py`, `test_cli_ops.py`, `test_cli_render_dnsmasq.py`, `test_cli_render_hosts_intent.py`, `test_cli_render_production.py`, `test_cli_session.py`, `test_cli_status.py`, `test_cli_surface.py`) and `test_output.py` | Retain adapter smoke | Already disposed in [report3.md](report3.md): each owns consumer-visible text/JSON, usage, exit, forwarding, redaction, or discoverability behavior rather than replaying a core success matrix. |
| `nctl/tests/test_nautobot.py` | Retain contract-local transport fixtures | Already disposed in [report2.md](report2.md): status, GraphQL, and each REST verb have distinct malformed/auth/connection translations. A common response builder would be a second schema. |
| `nctl/tests/test_dnsmasq.py`, `test_dnsmasq_render.py`, `test_dnsmasq_query.py`, `test_hosts_intent.py`, `test_hosts_intent_render.py`, `test_actual_render.py`, `test_drift_comparators.py`, `test_drift_render.py`, `test_production_composer.py`, `test_production_contract.py`, `test_production_derivation.py`, `test_production_render.py`, `test_production_adapter.py`, `test_production_profiles.py`, `test_service_placement.py` | Retain domain-owned cases | The alternatives vary canonical bytes, closed-schema diagnostics, competing candidate authority, or renderer/consumer contracts. Existing parameterized cases remain tables where one rule is varied; the remaining standalone cases each name a different result or diagnostic. |
| `nctl/tests/test_ansible.py`, `test_config.py`, `test_dumps.py`, `test_events.py`, `test_artifacts.py`, `test_jobs.py`, `test_observation.py`, `test_operations_index.py`, `test_repo_versions.py`, `test_session.py`, `test_sources_actual.py`, `test_sources_braindump.py`, `test_sources_desired.py`, `test_sources_observed.py`, `test_sources_snapshot.py`, `test_status.py` | Retain standalone | These prove separate configuration, parsing, filesystem privacy, durable-evidence, repository, source, Ansible invocation, or status contracts. Their failure messages and consumers differ; a cross-module table would have no single authoritative function. |
| `nctl/tests/test_braindump.py`, `test_compatibility_snapshots.py`, `test_drift_engine.py`, `test_drift_evaluation.py`, `test_drift_evaluation_snapshot.py`, `test_drift_operations.py`, `test_drift_registry.py`, `test_drift_status.py`, `test_inventory_trust.py`, `test_lifecycle_contract.py`, `test_p4_deployment_profiles_unavailable_contract.py`, `test_p4_intent_effect_summary_contract.py`, `test_p4_mixed_node_orchestration.py`, `test_phase3_lifecycle_transition.py` | Retain standalone | These are distinct classification, compatibility-reader, trust, lifecycle, or historical regression contracts. In particular, they must not be folded into a presentation or broad success table. |
| `nintent/.../test_analysis.py`, `test_api_contract.py`, `test_braindump.py`, `test_compute_contract.py`, `test_importers.py`, `test_jobs_import.py`, `test_loaders.py`, `test_names.py` | Retain standalone or existing subtest table | The framework/model input, permission, importer preview/apply, closed-schema, and name-normalization boundaries differ. `test_loaders.py` and runtime manifests already use subtests for same-rule axes; forcing the remaining semantic cases into one table would mix authority sources. |
| `nintent/.../test_remove_unused_surfaces.py`, `test_templates.py`, `test_ui_contract.py` | Retain Phase 1/UI proof | Removed-surface absence was completed in Phase 1. The remaining UI/template proof is explicitly retained in [report4.md](report4.md) for route, permission, no-POST, escaping, and unique-template semantics. |
| `nodeutils/tests/test_inventory_report.py`, `test_proxmox_inventory.py`, `test_pvesh_helper_integration.py` | Retain standalone | The first contains the named cross-repository digest consumer, the second separates normalization/error diagnostics from collection, and the third is the required real privileged-helper boundary. [report5.md](report5.md) records the golden ownership. |

## Final verification

On 2026-07-27, with no production-code or test behavior edits after the prior component gates:

- nctl: **966 passed** in 5.99 s;
- nintent: **227 run, 14 skipped**;
- nauto: **110 passed**;
- nodeutils: **54 passed** in 2.28 s; and
- ansible helper: **4 passed** (the stable-ID subtest table remains intact).

No nintent or nauto framework-owned code changed, so a local-source Nautobot runtime gate was not
triggered by this completion audit. The phase performed no external write, SSH, Ansible run,
observation, ingest, deployment, or secret read.

## Exit-criteria reconciliation

The sole selected same-layer repeated rule has a stable-ID table; every other Tier B group now has
an explicit standalone reason. Transport, CLI, UI, and golden dispositions remain recorded in
reports 2–5. There were no new merge/deletion actions, all prior merge records remain in the
ledger, and the final ordinary component gates pass. Measurements, skips, runtime signals, fixture
concentration, and deviations remain recorded in the restricted evidence directory; the audit
introduced no arbitrary reduction target.
