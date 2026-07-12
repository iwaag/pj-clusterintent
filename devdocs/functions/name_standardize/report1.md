# Step 1 report: shared name helper

## Summary

Step 1 is complete.

Added a shared helper module for conservative node-name normalization and
default endpoint-name generation:

- `nintent/nautobot_intent_catalog/names.py`

Added focused unit tests:

- `nintent/nautobot_intent_catalog/tests/test_names.py`

## Implemented behavior

### `canonical_node_name(value)`

The helper now:

- trims whitespace
- lowercases the value
- removes a trailing DNS root dot
- strips only the built-in local identity suffixes:
  - `.local`
  - `.home.arpa`
- preserves unrelated FQDNs

Covered examples:

- `pc1` -> `pc1`
- `PC1.local` -> `pc1`
- `pc1.home.arpa` -> `pc1`
- `db01.prod.example.com` -> `db01.prod.example.com`

Boundary cases are also covered so strings like `pc1local` and
`pc1home.arpa` are not accidentally stripped.

### `default_dns_name(node_name, suffix="home.arpa")`

The helper generates DNS names from the canonical node label:

- `PC1.local` -> `pc1.home.arpa`
- `pc1.home.arpa` with `suffix="lab.example"` -> `pc1.lab.example`

Blank node names return a blank string.

### `default_mdns_name(node_name)`

The helper generates mDNS names from the canonical node label:

- `pc1.home.arpa` -> `pc1.local`

Blank node names return a blank string.

## Verification

Executed from `nintent/`:

```text
python3 -m unittest nautobot_intent_catalog.tests.test_names
```

Result:

```text
Ran 10 tests in 0.000s
OK
```

Executed the full local unit test suite from `nintent/`:

```text
python3 -m unittest discover nautobot_intent_catalog/tests
```

Result:

```text
Ran 50 tests in 0.004s
OK
```

## Notes for Step 2

`names.py` is intentionally model-free and has no Nautobot/Django dependency, so
it can be imported by evaluation, importer, loader, and operation code without
creating model side effects.

The next step should use `canonical_node_name()` in node candidate scoring and
explicit realized-link hostname mismatch checks.
