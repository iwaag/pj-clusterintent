# P0 Step 5 — duplication inventory

Status: complete.

- Symbol-level AST comparison confirms the compute contract is duplicated: four `PROVENANCE_*` constants, `ComputeContractError`, config validation, bounded value validation, MAC normalization, lifecycle/effective-value rules, and actionable-lifecycle logic.
- The roadmap was corrected in this commit: `PROVENANCE_*` is duplicated, not nintent-only.
- At Phase 1 frozen-tuple re-check, that last classification was corrected: nintent models also
  implement the primary-endpoint predicates, candidate filter, and outcome codes; the rule is
  duplicated rather than nctl-only. The realized-link/source pairing rule and its vocabulary are
  likewise duplicated at three call sites. The proposed owner/mechanism remains recorded in
  `duplication-inventory.tsv`.
- Search of nintent loaders/importers/intent contract and nauto ingest policy found no second active duplicate beyond compute semantics; the one-sided write/read rules are retained as explicit non-duplication rows.
- Both test surfaces and write-time/actuation-time observations are recorded for every inventory row.
