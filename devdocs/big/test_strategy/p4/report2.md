# Test Strategy Phase 4 — Step 2 Report: Names, Skips, and Search Audit

Parent: [plan.md](plan.md), Step 2.

Status: **`complete`**.

## Historical name retirement

Renamed the active runtime module from `test_p3_node_link_http.py` to
`test_desired_node_link_http.py` in nintent commit `2a24bea`. All eleven collected method names
were preserved under the new module path, and its exact-local-source runtime gate passed. Historical
references in earlier phase reports remain historical evidence and were intentionally not rewritten.

The Django-free nintent command now reports **227 run, 14 skipped**. The previous recorded
226/13 count was stale; the new count is a measurement baseline to be recorded in the Step 3
matrix and Step 5 comparison, not a claim that a test was added by the rename.

## Skip/xfail audit

No xfail or `expectedFailure` decorator exists in the active suites. The 14 Django-free nintent
skips are explicit `Requires django/nautobot` guards (plus the one documented canonical-file
location guard); their owner is the optional exact-local-source Nautobot tier, where the required
runtime cases do not skip. This preserves fast Django-free discovery without allowing a required
Tier A proof to pass silently.

## Required search classification

The roadmap's removed-surface, compatibility, historical-name, skip/xfail, fixture, mock,
external-tool, transaction, network, and secret searches were run across active code, tests,
fixtures, configuration, current documentation, and this roadmap. Matches were classified in the
private evidence:

- Removed-surface and compatibility matches are migration/history, deliberate negative absence
  contracts, or current durable-reader contracts.
- Fixture and helper matches retain a current consumer; no unexplained orphan was found.
- Ordinary tests use `respx`, mocked URLs, or fixture-owned loopback HTTP. No ordinary test
  initiates a public-network call.
- Token/password-like strings are test fixtures or redaction assertions, not credentials. Existing
  host-like labels in nctl fixtures are deterministic test data, cause no connection without their
  explicit mocked/loopback boundary, and are not secret values or live inventory paths.

No bounded behavior change was required. No production/external target or credential was used.
