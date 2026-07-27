# P2 Step 1 — Audit and freeze dispositions

Status: complete.

Private evidence is under `.local/nctl-modularization/p2/20260728T120000Z/`:
`symbol-disposition-detailed.tsv`, `error-disposition.tsv`,
`policy-in-transport.tsv`, `duplication-findings.tsv`, `p0-corrections.md`,
`p1-corrections.md`, and `audit-searches-step1.txt`.

The seven planning findings were re-verified. `DesiredSourceIssue` is only
carried on `DesiredSnapshot`; it has no current envelope consumer. Its
preservation proof is therefore the Phase 1 snapshot-corpus capture and its
exclusion from typed compute collections. The Phase 0 `unreachable` labels
were corrected: the three Braindump write errors are factory-created, the two
Proxmox names are data records, `InventoryTrustError` is returned as a value,
and `Envelope` is a model. None authorizes deletion.

No caller distinguishes a Braindump, lifecycle, or session subclass by Python
type; their respective base error is the current code/detail boundary. The
taxonomy freezes 17 Braindump, 4 lifecycle, and 2 session subclasses for E2
folding in Step 6. `ConfigNotFoundError`/`ConfigInvalidError` remain E1
truthfulness distinctions; `NautobotAuthError` remains E1 because both
transport suites name it; `RepoVersionError` remains its module boundary; and
`ComputeContractError` remains fixture-bound. All Phase 3 error types are
untouched. Each of the 58 classes plus `Envelope` has an E1/E2/E3 disposition
record; E3 is recorded as a no-deletion correction, not an unreachable branch.

The roadmap overrides the Phase 0 production assignment: `production` route
composition and contract work remain Phase 4. `actual_type_problem` has one
source consumer (`production.derivation`); `missing_required_facts` and
`REQUIRED_FACT_BY_CONSUMER` currently have test-only consumers and will be
re-proven before their conditional Step 4 deletion. The independent lenient
`dnsmasq._normalize_mac` duplication is real but deferred to Phase 4 because
unification would alter deterministic bytes and the desired-MAC safe-stop.

The compute conformance test's private names and fixture-generated rule keys
were confirmed. Step 2 must move its nctl module reference/dispatch only;
the fixture remains byte-identical. No manifested test ID requires a rename.

Admission is recorded for the four new modules: `compute.model` owns compute
row/issue values, `compute.contract` owns fixture-bound rules,
`compute.collection` owns collection/source-issue policy, and the three
Braindump modules separately own REST status translation, command semantics,
and envelope/text presentation. Each has independent reasons to change and
current consumers. The rejected alternative is extracting all desired models:
their GraphQL query, decoder, and schema change together, and extraction would
create broad import churn without ownership gain.

No production or test code changed. The required scoped searches found no
compatibility shim, alias, or new framework; existing `legacy`, `fallback`,
and phase references are either current SSH/history semantics or documented
roadmap context and are not deletion permission.
