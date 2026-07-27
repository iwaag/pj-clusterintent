# P1 Step 1 — Verify and freeze the disposition table

Status: complete.

Evidence root: `.local/nctl-modularization/p1/20260728T000000Z/`.

## Frozen disposition

`disposition.tsv` in the private evidence root classifies every discovered compute-contract
symbol as `shared`, `nintent_only`, or `nctl_only`, records its implementation sites, its
consumer behavior, and its Phase 1 action. Shared rules have nintent as their semantic owner;
nctl retains a fixture-bound read-time implementation where it must turn stale or compromised
rows into source issues. This means one independently maintained implementation, not a literal
deletion of every read-time predicate.

Every retained nctl-only check has a stated safety consequence: either it excludes an invalid
platform/instance from `compute_platforms`/`compute_instances` and emits its `DesiredSourceIssue`,
or it keeps a malformed endpoint readable while `_validate_endpoint_macs` emits the issue. The
effective-default assembler, canonical-MAC transport tolerance, collection/source-issue policy,
and snapshot-level duplicate-MAC check are nctl-only. The nintent topology orchestration and
storage/bridge completeness check are nintent-only write-boundary rules.

## Confirmed corrections

All four planning-time findings were confirmed against the Step 0 tuple.

1. The primary-endpoint contract is duplicated: `models.py` has the same usable-IP/address
   predicates, candidate filter, and missing/ambiguous outcome codes as nctl.
2. Realized-link/source pairing is implemented three times: once in nctl and inline in both
   compute model `clean()` methods. `derived`/`override` is shared vocabulary.
3. Desired-MAC uniqueness is intentional two-layer enforcement, not a deletion candidate:
   nintent's DB constraint protects writes and nctl's snapshot check protects current reads.
4. `MANIFEST.md` has 26 behavior rows. The prior 27 count included a non-behavior table line.

The roadmap and Phase 0 reports have been corrected in this commit. The Phase 0 private
duplication inventory has the same correction recorded locally. The required restricted search
was retained in `compute-search.txt`; each active match was classified in `search-classification.tsv`.
No match was treated as deletion permission.

## Gate verdict

Complete: no duplicated symbol is unclassified, the Phase 0 factual corrections are recorded,
and the required retained-check justifications are explicit. No product source, fixture, runtime
contract, or compute behavior changed in this step.
