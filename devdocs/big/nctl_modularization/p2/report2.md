# P2 Step 2 — Extract the compute contract into a pure package

Status: complete.

The fixture-bound compute values now live in `nctl_core.compute.model`, and contract vocabulary, validators, normalizers, effective-value rules, and endpoint predicates live in `nctl_core.compute.contract`. Collection and source-issue policy deliberately remain in `sources/desired.py` for Step 3.

The fixture consumer dispatches directly to `compute.contract`; fixture rule keys are unchanged, while the moved predicates are public as `endpoint_has_usable_ip`, `endpoint_satisfies_compute_address_contract`, and `validate_link_source`. Compute-value consumers import `compute.model` directly. The desired-source transport retains only its decode-time malformed-MAC tolerance wrapper.

Added `tests/test_module_boundaries.py`, which imports the pure modules in fresh subprocesses and proves `httpx`, `typer`, `nctl_core.nautobot`, and `nctl_core.cli` are absent. Step 3 extends this proof to `compute.collection`.

Gates passed: nctl ordinary `970 passed in 5.66s`; focused conformance, boundary, desired-source, inertness, and evaluation tests `26 passed`; superproject compute-conformance freshness gate `1 passed`; `git diff --check` clean. The compute fixture SHA-256 remains `ccff71d9f4c7715a46c026c1529373fc38806208df49f512bc85d6a3e31b81ce`.

No fixture, compute semantics, compute drift/planning/actuation behavior, or external state changed. Compute remains read-only and inert.
