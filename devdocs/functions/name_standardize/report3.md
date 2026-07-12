# Step 3 report: soft defaults in Quick Host Add

## Summary

Step 3 is complete.

Updated Quick Host Add creation logic:

- `nintent/nautobot_intent_catalog/operations/hosts.py`

Added focused tests:

- `nintent/nautobot_intent_catalog/tests/test_operations_hosts.py`

## Implemented behavior

`create_desired_node_with_primary_endpoint()` now fills blank endpoint names
only for the simple primary endpoint path:

- `endpoint_name=primary`
- `endpoint_type=primary`

For that primary endpoint case:

- blank `dns_name` becomes `<canonical-node-name>.home.arpa`
- blank `mdns_name` becomes `<canonical-node-name>.local`

The implementation uses the shared helpers from Step 1:

- `default_dns_name()`
- `default_mdns_name()`

Covered example:

- node name `PC1.local`
- blank `dns_name`
- blank `mdns_name`

Result:

- `dns_name=pc1.home.arpa`
- `mdns_name=pc1.local`

## Preserved behavior

Explicit values still win:

- `dns_name=custom.example.test` remains `custom.example.test`
- `mdns_name=custom.local` remains `custom.local`

Non-primary endpoints are not auto-filled:

- `endpoint_name=mgmt`
- `endpoint_type=management`

Result:

- `dns_name=None`
- `mdns_name=None`

## Verification

Executed from `nintent/`:

```text
python3 -m unittest nautobot_intent_catalog.tests.test_operations_hosts
```

Result:

```text
Ran 6 tests in 0.000s
OK
```

Executed the full local unit test suite from `nintent/`:

```text
python3 -m unittest discover nautobot_intent_catalog/tests
```

Result:

```text
Ran 56 tests in 0.005s
OK
```

## Notes for Step 4

YAML import should apply the same primary-endpoint-only defaulting policy at
the importer or operation boundary, where the referenced desired node has
already been resolved.
