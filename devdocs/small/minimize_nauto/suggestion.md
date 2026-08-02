# nauto Custom Field Minimization — Proposed Policy

## Background

The ~35 Device custom fields in `nauto/seed/home_cluster.yaml` were
created before the project settled on its current policy: stuff rawdata
with everything collectible, and promote to a dedicated column only
what deterministic processing actually consumes. As a result they
diverge from that policy, with information split across many
individual columns.

Findings from fact-checking:
- Deterministic processing (nctl) reads only the 9 fields in
  `ACTUAL_FACT_FIELDS` (`nctl/src/nctl_core/sources/actual.py`).
- The remaining ~26 fields (os_name, cpu_model, memory_gb, gpu_*,
  docker_*, etc.) are not referenced by any deterministic processing.
- `inventory_raw_json` already stores the full raw payload (identity,
  facts.hardware/gpu/disk/network/software/services/workspaces).
- The Proxmox-side fields (`proxmox_*`) already follow a closed
  allowlist pattern consistent with the policy.
- Custom fields appear editable from the GUI, but every run of the
  `Ingest Nodeutils Inventory` Job overwrites them, so they are
  effectively write-only observation data in practice.

## Policy

1. **Retire the AI review feature**
   - Delete `nauto/jobs/ai_resource_review.py` (a Job Hook that
     generates an external-AI review on Device create/update and
     writes it back).
   - Delete the custom fields it writes: `ai_resource_review`,
     `ai_resource_review_updated_at`, `ai_resource_review_model`,
     `ai_resource_review_source_hash`.
   - No deterministic processing references these, so removal has no
     effect on real processing.
   - Also unregister the corresponding Job Hook in the Nautobot admin
     UI.

2. **Clean up unreferenced columns**
   - For individual columns not read by deterministic processing
     (nctl/nintent), drop the ones not used for list filtering/sorting
     from the DB schema, leaving that information only in
     `inventory_raw_json`.
   - Keep any column still used for filtering/sorting in list views.
   - Confirm necessity column by column before finalizing the removal
     list (no bulk deletion).

3. **Replace with GUI display**
   - For removed columns that are still useful as a human-readable
     Device summary (OS/HW/service overview, etc.), add a Nautobot
     `TemplateExtension` panel on the Device detail page that parses
     `inventory_raw_json` on render instead.
   - This panel is read-only, but since the existing custom fields
     were already effectively write-only, this is not a regression in
     practice.

## Open items

- Final column-by-column confirmation of which removal candidates are
  still needed for filtering/sorting.
- Concrete layout/field selection for the TemplateExtension panel.
