# P4 Step 6 — Canonical serialization versus validation schema

Status: complete.

`nctl_core.canonical` now owns canonical JSON bytes and SHA-256 digest generation. The production schema keeps `ContractError` and validation, while profile loading and reconcile fingerprinting import the generic utility directly. The `deterministic-rendering` manifest note now names its new owner.

`test_production_contract.py` and `test_production_profiles.py` passed (**13 passed**), preserving the exact canonical byte and digest assertion.
