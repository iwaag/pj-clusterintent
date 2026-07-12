# Step 2 report: canonical names in node evaluation

## Summary

Step 2 is complete.

Updated node evaluation to use the shared name helper from Step 1:

- `nintent/nautobot_intent_catalog/evaluations.py`

Added focused tests:

- `nintent/nautobot_intent_catalog/tests/test_evaluations.py`

## Implemented behavior

### Candidate scoring

`_node_candidate_score()` now uses `canonical_node_name()` for name-like node
identity fields:

- desired `name`
- desired `slug`
- desired `expected_spec.hostname` / `expected_spec.host_name`
- actual `name`
- actual `hostname`
- actual custom field `hostname`
- actual custom field `nodeutils_hostname`

Serial, UUID, and platform scoring are unchanged and still use the previous
plain normalized comparison.

Covered example:

- `DesiredNode.name=pc1` can match an actual `Device.name=pc1.local`

The match is still treated as an unlinked candidate, so the evaluation remains
`partial` and recommends explicit review/linking.

### Explicit link mismatch checks

`_node_mismatches()` now compares desired and actual hostnames with
`canonical_node_name()`.

Covered example:

- desired hostname `pc1`
- linked actual device name `pc1.local`

This no longer produces a `hostname_mismatch` conflict.

### Conservative FQDN handling

The evaluation path preserves the Step 1 conservative suffix policy.

Covered example:

- desired node `db01`
- actual device `db01.prod.example.com`

This does not match, because unknown FQDN suffixes are not collapsed.

## Verification

Executed from `nintent/`:

```text
python3 -m unittest nautobot_intent_catalog.tests.test_evaluations
```

Result:

```text
Ran 16 tests in 0.001s
OK
```

Executed the full local unit test suite from `nintent/`:

```text
python3 -m unittest discover nautobot_intent_catalog/tests
```

Result:

```text
Ran 53 tests in 0.005s
OK
```

## Notes for Step 3

The helper is now used by evaluation, so Quick Host Add can use the same
`default_dns_name()` and `default_mdns_name()` functions to generate soft
primary endpoint defaults without introducing another naming policy.
