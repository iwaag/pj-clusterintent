# P2 Step 4 — Confirm the actual transport boundary

Status: complete.

The required consumer audit found `actual_type_problem` had one production
consumer, `production.derivation.resolve_operational_values`; it now lives
there with its ownership test. `missing_required_facts` and
`REQUIRED_FACT_BY_CONSUMER` had zero `src/` consumers (only their own source
test and a stale explanatory comment). They were deleted with that test.

The retained independent producers of the equivalent skip-code family remain
unchanged: `production/derivation.py` produces `missing_observed_system` and
`missing_mac_address`; `production/composer.py` and `dnsmasq.py` retain their
own observed-network-interface checks; `reconcile/classify.py` retains their
classification. A future per-consumer fact requirement must be defined beside
the consumer that needs it.

The rest of `sources/actual.py` remains transport-shaped: it decodes the
allowlisted actual facts, GraphQL rows, and Proxmox records only. Its and
`production/composer.py`'s stale ownership docstrings were corrected.

Gates passed: focused actual/production tests `88 passed`; nctl ordinary
`970 passed in 5.94s`; `git diff --check` clean. The ordinary-suite count is
one below Step 3 solely because the proven-orphan helper test was deleted.
No protocol, composition result, skip code, or external state changed.
