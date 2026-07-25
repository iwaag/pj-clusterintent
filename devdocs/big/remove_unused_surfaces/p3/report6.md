# Phase 3 Step 6 — Prove retained UI, REST, GraphQL, and Braindump behavior

Parent: [plan.md](plan.md) Step 6.

Executed 2026-07-25. nintent commit: `0914ca496dc9c72319c8c1e2e1bcc2bf7e418a7e`. Private evidence
directory: `.local/remove-unused-surfaces/p3/20260725-162655/` (mode `0700`, files `0600`),
containing `step6-removal-tests-final.log`, `step6-full-app-suite.log`.

## 1. Focused removal/retained-path module, final state

Added `ComputeUIRegistrationTests` (`TestCase`, matching `NodeServiceUITests`'s pattern) and
`ComputeAPIRegistrationTests` (`APITestCase`) to `test_remove_unused_surfaces.py`: creates a real
`DesiredComputePlatform` and proves its list page renders it, its REST list returns it, and a
`desired_compute_platforms { id name }` GraphQL query returns it — the plan §7 Step 6.7 proof that
VM Phase 3's compute registration survives this phase's deletions, not merely that its URL name
still reverses (already covered by `RetainedRoutesTests`).

`nautobot-server test nautobot_intent_catalog.tests.test_remove_unused_surfaces --keepdb`:
**32/32 passed** (29 from Steps 1/3 + 3 new compute registration tests).

## 2. Braindump regression

`nautobot-server test nautobot_intent_catalog.tests.test_braindump --keepdb`: unaffected by this
step (no Braindump file touched); the full-app-suite run in §3 below includes and passes its 33
tests.

## 3. Complete Nautobot-runtime app suite

`nautobot-server test nautobot_intent_catalog --keepdb`: **252/252 passed** (249 from Step 3 + 3
new compute registration tests). Zero failures, zero errors.

## 4. Content-level (not merely status-code) proof, cross-referenced to plan §6.4

- Node/service list and detail pages contain the actual test names (`NodeServiceUITests`,
  `report3.md`).
- Cache labels/dashboard text are absent from those same pages (`NodeServiceUITests`).
- Quick Host Add remains in navigation; `nctl Dashboard` is absent (`NavigationTests`).
- REST returns actual node/service/compute-platform IDs and surviving fields
  (`RestApiTests`, `ComputeAPIRegistrationTests`).
- GraphQL returns non-empty node/service/compute-platform roots and rejects the two old fields
  as unknown (`GraphQLTests`, `ComputeAPIRegistrationTests`).
- Compute URLs/schema remain registered and now positively loaded, not just reversible
  (`RetainedRoutesTests`, `ComputeUIRegistrationTests`, `ComputeAPIRegistrationTests`).
- Braindump queries return the test documents/review relation (`test_braindump`, included in the
  §3 full-suite run).
- No test in this module invokes nctl, SSH, Ansible, Jobs, or host operations (all fixtures are
  plain Django ORM `.objects.create()` calls against local models).

## 5. Local Django-free suite

`python3 -m unittest discover -s nautobot_intent_catalog/tests`: **187 passed**, unchanged.

## Gate

Absence of the cache/link is positively proven (Steps 1/3) and ordinary desired-state, compute, and
Braindump paths are now positively exercised with real content assertions, not status-code-only
checks. Step 6 gate met.
