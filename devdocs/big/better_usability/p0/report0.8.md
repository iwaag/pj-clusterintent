# Phase 0 — final report: assembly, verification, and roadmap reconciliation

Parent: [plan.md](plan.md) — Verification section and exit criteria.

## What was done

- **Closed one rulebook gap** found during a final internal-consistency pass: `DesiredEndpoint.
  vpn_dns_name`/`protocol`/`port` and `DesiredIPRange.generate_dnsmasq` were classified Override in
  §2 but had no §4 rulebook row. Added one consolidated row for these trivially-optional fields
  (no derivation algorithm exists to specify beyond "use as given, absence is not an error").
- **Ran the plan's full documentation/static-check verification list**:
  1. Programmatically cross-checked the §2 field inventory against `models.py` by extracting every
     `= models.` field declaration per class and comparing to every `` `field` `` cell in the
     table — **exact match, 100/100 fields, same order, zero omissions or extras**, for all 8
     models.
  2. Did a final targeted sweep for the three models least covered by the original per-file agent
     research (`IntentSource`, `DesiredDependency`, `DesiredIPRange`) across all of `nctl/src` —
     confirmed `IntentSource` has **zero** references anywhere in `nctl` (correct: it's purely an
     nintent-side import-tracking construct, absent from `sources/desired.py`'s GraphQL query by
     design) and that `DesiredDependency`/`DesiredIPRange`'s remaining hits (`evaluation.py`,
     `dnsmasq_query.py`) were already accounted for in §2/§4/§6.
  3. Lifecycle-default search: already exhaustive in §7 (4 independent `DesiredNode.lifecycle`
     sources, all agreeing; 4 independent `DesiredService.lifecycle` sources, no contradiction).
  4. `raise ContractError` search: already exhaustive in §6 (57 sites, all 57 classified into
     Group A/B/C).
  5. Programmatically verified every table row whose Contradiction cell says "Yes" (or similar) has
     a non-empty Owning phase cell — **zero rows failed this check**.
  6. Compared `roadmap.md` against the completed audit and updated it in this same change (below).
- **Ran the plan's read-only environment checks**, final pass:
  - `uv run --project nctl pytest -q nctl/tests` → **518 passed** (unchanged from Step 0.1's
    baseline and from plan.md's recorded baseline).
  - nintent local unit suite (`uv run python -m unittest discover -s nautobot_intent_catalog/tests
    -p "test_*.py"`, run from `nintent/`) → **88 passed** (unchanged).
  - `git status --short` in the repo root **and every submodule** (`nctl`, `nintent`, `nauto`,
    `ansible_agdev`, `nodeutils`) — confirms the entire Phase 0 effort touched only
    `devdocs/big/better_usability/p0/*` and one paragraph of `roadmap.md` in the root repo; **no
    submodule has any uncommitted or out-of-scope change**, satisfying the plan's "Out of scope"
    list (no runtime/model/migration/API/CLI/composer/drift/reconcile/Ansible/live-ledger changes).
  - Live GraphQL/`nctl drift --json` checks against the dev Nautobot (done in Step 0.1, re-verified
    unchanged by inspection — no write operations were performed at any point in this phase).

## Roadmap reconciliation

Updated `roadmap.md`'s Phase 2 section (the only place it stated a provisional, hedged choice this
audit was positioned to resolve): added a paragraph confirming the "(b) dissolve" persistence shape
with the concrete evidence from `field-classification.md` §4 (zero live rows, one creation path,
every ordinary case derivable), and surfacing the audit's one finding that goes beyond the roadmap's
original framing — `actual_state_policy` collapsing into a computed fact about `declared_host_os`'s
presence rather than needing its own derivation logic at all. No other part of `roadmap.md` required
correction: Phase 3's "reconsider `DesiredService.lifecycle`" instruction is satisfied by the
decision recorded in `field-classification.md` itself (no roadmap text asserted a specific outcome to
correct), and Phase 1's `ContractError`/`missing_operational_config` framing already matches §6's
findings without contradiction.

## Exit criteria (plan.md) — final check

- [x] `p0/field-classification.md` contains every required section (1–9, plus an added §10
  consistency review) and every app-declared writable field exactly once.
- [x] Every Derived value has deterministic inputs, precedence, no/stale/ambiguous behavior, and
  output provenance (§4).
- [x] Every Override has a safe default/not-set behavior and a named target persistence location
  (§4, including the gap closed in this final pass).
- [x] The Phase 2 operational-config shape is selected (dissolve), with deletion/move/retention
  decisions for every current field and consumer (§4, §5 transition impact map).
- [x] Every production composition error has an agreed global or target-local scope (§6, all 57
  sites).
- [x] Every lifecycle creation ingress and the existing-row transition are assigned to Phase 3 (§7,
  §8).
- [x] Every contradiction and breaking transition is assigned to exactly one later phase (§8).
- [x] No schema-shaping or behavior-shaping open issue remains (§9).
- [x] Roadmap, discussion, classification artifact, and plan agree on Phase 1 → Phase 2 → Phase 3
  as the hard dependency chain (§10; roadmap.md updated this change where it had a provisional gap).
- [x] Read-only live checks and both scoped test suites pass; no runtime or live data was changed.

Phase 0 is complete. Nothing encountered during this work required stopping to ask the user for a
judgment call — every ambiguity surfaced during construction was either traced to a definite answer
within this phase or explicitly and narrowly deferred to the later phase whose own implementation
plan the roadmap already reserves it for.
