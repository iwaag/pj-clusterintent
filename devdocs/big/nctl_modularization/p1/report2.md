# P1 Step 2 — Extend the owner

Status: complete.

## Owner changes

`nintent/nautobot_intent_catalog/compute_contract.py` is now the Django-free semantic owner for
the complete shared compute contract. It gained the lifecycle and realized-link vocabularies,
named lifecycle/kind/power/link validators, the pure pairing predicate, usable-IP and
compute-address predicates, and the duck-typed primary-endpoint selector with its existing
missing/ambiguous codes.

`validate_instance_config()` now calls the owner `validate_instance_kind()` while preserving the
existing `invalid_instance_kind` code, `instance_kind` path, and message. The model layer no
longer defines endpoint predicates or a primary-endpoint candidate filter: it consumes the owner
selector, retains the existing topology problem ordering, and retains its Django-specific field
messages when using the pairing predicate. Django field choices remain framework enforcement;
they and the owner validator derive from the same vocabulary rather than raising a contract error
through the ORM.

## Verification

The nintent Django-free gate passed: **233 tests run, 14 skipped**. The six-test increase from the
Step 0 baseline covers the newly owned lifecycle, kind, power, link-pairing, usable-address, and
primary-endpoint behavior. `owner-diff.txt` is retained in the private evidence directory.

No migration, nctl change, fixture, desired row, drift comparator, planner action, reconciler, or
actuator was added. Model write-path error fields and strings were preserved by the refactor.

## Gate verdict

Complete: owner symbols and their direct behavior tests exist, nintent's Django-free gate passes
with the expected 14 skips, and model-side duplicate implementations have been rewired without a
write-path contract change.
