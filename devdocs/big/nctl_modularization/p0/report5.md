# P0 Step 5 — duplication inventory

Status: complete.

- Symbol-level AST comparison confirms the compute contract is duplicated: four `PROVENANCE_*` constants, `ComputeContractError`, config validation, bounded value validation, MAC normalization, lifecycle/effective-value rules, and actionable-lifecycle logic.
- The roadmap was corrected in this commit: `PROVENANCE_*` is duplicated, not nintent-only.
- nctl-only symbols divide into contract candidates (`validate_compute_lifecycle`, instance kind, power state), actuation-time selection (`select_compute_primary_endpoint` and endpoint usability), and source/transport helpers. The proposed owner/mechanism is recorded in `duplication-inventory.tsv`.
- Search of nintent loaders/importers/intent contract and nauto ingest policy found no second active duplicate beyond compute semantics; the one-sided write/read rules are retained as explicit non-duplication rows.
- Both test surfaces and write-time/actuation-time observations are recorded for every inventory row.
