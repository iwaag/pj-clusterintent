# Step 5 Report: Make Actual Facts Exportable Without Inference

## Summary

Completed Step 5. The two allowlisted observed facts that were not yet persisted through dedicated
fields (`facts.system` and the primary interface name) are now written as first-class Device custom
fields by the nauto nodeutils ingest job, and a new pure, tested extraction layer in nintent reads
**only** the documented allowlist from a realized Device. The exporter (Step 6) can now obtain every
allowlisted fact through stable, documented fields without parsing the unrestricted
`inventory_raw_json` blob, and no derived operational value (package manager, power policy, service
placement) can travel through the actual-fact path.

Step 1 had already landed the contract-level pieces this step depends on in
`production_inventory_contract.py`: host_os normalization (`_OBSERVED_SYSTEM_MAP`,
`evaluate_platform_policy`) and freshness validation (`actual_state_problem`). Step 5 supplies the
missing persistence and the realized-Device extraction boundary that feeds those functions.

## Status of plan items

| # | Item | Outcome |
|---|------|---------|
| 1 | Persist each allowlisted fact with collection timestamp + provenance | `last_seen`/`inventory_source` already persisted; added `host_system`; provenance complete |
| 2 | Persist primary interface name explicitly (not via raw JSON) | Added `network_interface` custom field from `facts.network.primary_interface.name` |
| 3 | Keep source values intact; normalize host_os in one tested exporter function | `host_system` stores raw `Linux`/`Darwin`; reader does not normalize; normalization stays in `evaluate_platform_policy` |
| 4 | Freshness validation for `required`, bypass only for declared | `actual_state_problem` (Step 1) consumes the reader's `collected_at`; covered by an integration test |
| 5 | Required actual fields per consumer; not every field on every host | `REQUIRED_FACT_BY_CONSUMER` + `missing_required_facts(facts, consumers)` |
| 6 | Tests proving no derived operational value is emitted from actual data | `test_actual_facts.py` asserts the closed allowlist and rejects derived noise |
| 7 | Limit actual-backed composition to realized Devices; `unsupported_actual_type` for VMs | `actual_type_problem(realized_type)` |

## Changes

### nauto/jobs/ingest_nodeutils_inventory.py

- `build_custom_fields` now reads `network.primary_interface` and persists two new dedicated custom
  fields:
  - `host_system` ← `facts.system` (raw `platform.system()` value, the documented source the
    exporter normalizes to `host_os`). Stored as a source value, not a desired value.
  - `network_interface` ← `facts.network.primary_interface.name`, so the exporter never has to
    inspect `inventory_raw_json` for the interface name.
- `inventory_raw_json` is unchanged and retained for other consumers (AI review); the point is that
  the actual-fact exporter no longer needs to read it.

### nauto/seed/home_cluster.yaml

- Added text custom-field definitions for `network_interface` (weight 232) and `host_system`
  (weight 234), both on `dcim.device`, each with a description documenting the exact nodeutils source
  path. Verified all custom-field keys remain unique.

### nintent/nautobot_intent_catalog/actual_facts.py (new)

- Pure module (no Django/Nautobot import) defining the actual-state extraction boundary:
  - `ACTUAL_FACT_FIELDS`: closed allowlist mapping each exportable fact to its nauto custom-field key.
  - `ActualFacts`: a frozen dataclass with one field per allowlisted fact and nothing else, so no
    derived operational value can structurally pass through.
  - `read_actual_facts(custom_fields)`: reads only the allowlisted keys (ignores everything else),
    trimming blanks to `None`. Does **not** normalize host_os — it returns the raw `observed_system`.
  - `actual_type_problem(realized_type)`: `None` for `device`, `unsupported_actual_type` for VMs/other
    realized types, `no_realized_device` when absent (Step 5 item 7 / Step 6 skip taxonomy).
  - `REQUIRED_FACT_BY_CONSUMER` + `missing_required_facts(facts, consumers)`: consumer-scoped required
    facts (`host_os`→observed_system, `wol`→mac_address, `network_interface`→network_interface);
    returns sorted, deterministic `missing_<field>` reason codes and rejects unknown consumers.

### nintent/nautobot_intent_catalog/tests/test_actual_facts.py (new)

- 14 tests: allowlist-only reading; structural proof that `ActualFacts` exposes no
  `package_manager`/`service_roles`/`observed_services`/`power_control`; interface name comes from the
  dedicated field and not the raw blob; blank/missing/None handling; Device/VM/unknown/absent type
  gating; per-consumer required-fact logic; unknown-consumer rejection; and integration with the
  contract proving the reader does not normalize host_os and that `actual_state_problem` consumes the
  reader's `collected_at`.

### nauto/README.md

- Added `network_interface` and `host_system` to the Device custom-field list.
- Removed the stale `service_roles` and `preferred_services` list entries, the obsolete
  `preferred_services` JSON example block, and rewrote the host-local-facts paragraph to describe
  `observed_services` correctly and point desired placement at nintent `DesiredServicePlacement`.
  (These were Step 3 removals that the doc had missed; corrected here since the same field list was
  being edited.)

## Verification

- `python3 -m unittest discover nintent/.../tests` — 150 tests pass (includes 14 new `test_actual_facts`,
  12 `test_ansible_inventory`, 9 `test_production_inventory_contract`).
- `python3 -m py_compile nauto/jobs/ingest_nodeutils_inventory.py` — OK.
- Seed YAML parses and all custom-field keys are unique; both new keys present.
- `nauto/tests/test_nodeutils_ingest_batch` (9) and `nodeutils/tests/test_inventory_report` (3) pass.
- Residual scan: the only remaining `service_roles`/`preferred_services` matches are intentional
  negative assertions (`assertNotIn`) in `nodeutils/tests/test_inventory_report.py` and the noise blob
  in `test_actual_facts.py`. No execution environment is available, so no live Nautobot ingest run.

## Exit Criterion Status

Met. The exporter can obtain every allowlisted fact — `host_os` source, `local_ip`, `mac_address`,
`network_interface`, and collection provenance — through stable, documented Device custom fields via
`read_actual_facts`, with no parsing of arbitrary raw inventory blobs and no inferred operational
values.

## Notes

- nodeutils already emits `facts.system` and `facts.network.primary_interface.name`, so no nodeutils
  change was needed; the gap was purely in nauto persistence and the nintent extraction boundary.
- The actual-fact reader is intentionally pure and accepts a plain custom-field mapping plus a
  realized-type string, mirroring the bootstrap exporter's object-shaped test style. Step 6's composer
  will fetch the realized Device, pass its custom fields and type here, and feed `observed_system`,
  `collected_at`, and the realized type into the existing contract functions.
- Existing Devices need the two new custom fields created (re-run the home_cluster seed) and a fresh
  ingest to populate `host_system`/`network_interface`; there is no runtime fallback that derives them.
