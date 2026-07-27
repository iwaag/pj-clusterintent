# P1 Step 8 — Manifest and documentation

Status: complete.

## Delivered documentation

`MANIFEST.md` now has the `compute-contract-single-owner` Tier A row. It names both the
superproject fixture-freshness test and nctl's fixture-replay test, their respective gates, and
the positive evidence that both owner-to-fixture and fixture-to-consumer boundaries held.

`nintent/README_DEV.md` now identifies `compute_contract.py` as the semantic owner and
`compute_conformance.py` as the Django-free publisher of the generated consumer fixture.
`nctl/README.md` explains that its retained read-time validation is fixture-bound and must not
become a runtime import from nintent.

## Verification

The manifest contains 27 behavior rows (the prior 26 plus the new contract-ownership row). Every
manifested test-file reference resolves to an existing file. The affected gates passed:

- nintent Django-free: **236 run, 14 skipped**;
- nctl ordinary: **968 passed**; and
- superproject compute-conformance freshness: **1 passed**.

No manifested test ID was renamed.

## Gate verdict

Complete: the manifest, owner documentation, and consumer documentation state the same ownership
boundary and both required conformance tests are present and passing.
