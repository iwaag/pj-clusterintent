# Step 2 — Change Job Selection and Write-time Observation Checks

## Changes

`nintent/nautobot_intent_catalog/jobs.py`, `ReconcileDesiredIPAMIntent`:

- Replaced `filter(ip_policy="dhcp_reserved")` with
  `.exclude(ip_address__isnull=True).exclude(ip_address="")` — the queryset now
  enumerates every nonblank explicit-`ip_address` endpoint in scope, regardless
  of `ip_policy`. It does not attempt to validate the address string itself;
  an invalid value (e.g. not parseable as an IP) still reaches
  `plan_endpoint_ipam_reconcile()`, which already returns a typed
  `missing_ip_address` skip for it (Step 1).
- Added `_observed_ip_candidates(desired_node)`: reads the `primary_ip_address`
  / `last_seen` custom fields directly off `desired_node.realized_device` and
  `desired_node.realized_vm` (the same `custom_field_data` boundary nauto's
  `Ingest Nodeutils Inventory` Job writes and nctl reads as
  `ActualFacts.local_ip`). It does not read the controller-local nodeutils
  cache. Since nauto ingestion currently only populates these fields on a
  Device, a linked VM without its own populated field naturally yields no
  candidate — the helper never invents a VM-side value.
- Each endpoint's plan call now passes `observed_ip_candidates=...`, so the
  eligibility recheck implemented in Step 1 happens immediately before commit,
  not just when nctl computed drift earlier. This is the Job's defense-in-depth
  check against state changing between the nctl decision and the Job write.
- Added an `eligible` count to the summary counters (incremented whenever
  `plan.eligibility_basis == "eligible"`), so an eligible-but-not-yet-applied
  gap is distinguishable from a manual-review skip in the artifact even before
  Step 4 tightens artifact verification on the nctl side.
- `Meta.description` no longer says "DHCP-reserved"; it now states the actual
  eligibility rule (dhcp_reserved always eligible; static/external require a
  matching observation), per the plan's Step 5 documentation note pulled
  forward since it's a one-line, same-file change.
- Removed the now-stale "matches the dhcp_reserved intent policy this Job
  already restricts itself to" wording from `_default_ip_address_status`'s
  docstring (status resolution logic itself is unchanged — Step 3's "Preserve
  the existing environment-compatible status resolver" applies as-is).

No model fields changed; this step does not touch `models.py`, so no migration
is expected (confirmed via `makemigrations --check --dry-run` deferred to the
Nautobot-backed verification phase, since this repo's local fast suite does
not load Django/Nautobot at all — see Verified Baseline in plan.md).

## Verification

`jobs.py` is excluded from Django-free unit test collection (it hard-imports
`nautobot.apps.jobs` etc., guarded by the existing `try/except ImportError`
block), so it is not exercised by the local suite. Confirmed only:

```
$ python3 -c "import ast; ast.parse(open('nautobot_intent_catalog/jobs.py').read())"
OK

$ python3 -m unittest discover -s nautobot_intent_catalog/tests
Ran 111 tests in 0.018s
OK
```

Real queryset behavior, per-endpoint observation extraction against actual
`custom_field_data`, and the Job's interaction with real `IPAddress` rows can
only be verified in the deployed Nautobot environment (per plan.md's Verified
Baseline and the "Nautobot-backed and Live Verification" phase later in this
plan).

## Status

Step 2 complete at the code level. Not yet deployed or Nautobot-verified.
