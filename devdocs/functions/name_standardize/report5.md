# Step 5 report: endpoint evaluation consumes node evaluation facts

## Summary

Step 5 is complete.

Updated endpoint evaluation and the Nautobot Job flow:

- `nintent/nautobot_intent_catalog/evaluations.py`
- `nintent/nautobot_intent_catalog/jobs.py`

Added focused tests:

- `nintent/nautobot_intent_catalog/tests/test_evaluations.py`

## Implemented behavior

### Endpoint evaluator accepts stored evaluation objects

`evaluate_endpoint_intent()` already accepted an `EvaluationPayload` or dict as
`node_evaluation`. It now also accepts a stored `IntentEvaluation`-like object
with attributes such as:

- `observed_facts`
- `actual_refs`
- `deterministic_summary`
- `gap_summary`

This matches the object shape returned by `_latest_evaluations()` in
`jobs.py`.

### Endpoint Job uses latest node evaluations

`EvaluateEndpointIntent` now loads latest persisted node evaluations once:

```text
node_evaluations = _latest_evaluations(NODE_TARGET_TYPE)
```

For each desired endpoint, it passes the matching stored node evaluation:

```text
node_evaluation=node_evaluations.get(str(desired_node.pk))
```

It no longer creates a fresh node evaluation with empty device and VM candidate
sets as the only source of node facts.

### MAC candidate discovery from node facts

Endpoint evaluation can now use interface facts from a node evaluation that
found a single actual node candidate by normalized name.

Covered example:

- desired node `pc1`
- actual device candidate `pc1.local`
- actual interface `eth0`
- actual MAC `aa-bb-cc-dd-ee-ff`

The node evaluation records `pc1.local` as the selected actual candidate. The
endpoint evaluation then reads that node evaluation's interface facts and
produces one DHCP MAC candidate:

```text
aa:bb:cc:dd:ee:ff
```

## Verification

Executed from `nintent/`:

```text
python3 -m unittest nautobot_intent_catalog.tests.test_evaluations
```

Result:

```text
Ran 18 tests in 0.001s
OK
```

Executed the full local unit test suite from `nintent/`:

```text
python3 -m unittest discover nautobot_intent_catalog/tests
```

Result:

```text
Ran 61 tests in 0.006s
OK
```

## Notes for Step 6

Documentation should explain that the intended workflow is:

1. run node evaluation first
2. run endpoint evaluation
3. export dnsmasq records

That order matters when an endpoint depends on node candidate facts rather than
an explicit realized node link.
