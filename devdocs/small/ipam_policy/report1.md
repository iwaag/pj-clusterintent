# Step 1 — Extract Pure Normalization and Eligibility Planning in nintent

## Changes

`nintent/nautobot_intent_catalog/operations/ipam.py`:

- Added `NON_DHCP_POLICIES`, `KNOWN_IP_POLICIES`, `HOST_TYPE_VALUES` and the
  `_ELIGIBLE`/`_OBSERVATION_MISSING`/`_OBSERVATION_MISMATCH`/`_OBSERVATION_AMBIGUOUS`/
  `_UNKNOWN_POLICY` eligibility-basis constants.
- `IPAMReconcilePlan` gained `ip_policy`, `observed_ip_candidates`, and
  `eligibility_basis` fields, all serialized by `as_dict()`.
- `plan_endpoint_ipam_reconcile()` now takes `observed_ip_candidates` and
  implements the plan's eligibility truth table at the top of the function via
  new `_resolve_eligibility()` / `_normalized_observed_hosts()` helpers:
  - Empty/invalid desired IP -> `missing_ip_address` skip, regardless of policy
    (checked first, before policy is even looked at).
  - Unknown `ip_policy` -> `unknown_ip_policy` skip (fail closed).
  - `dhcp_reserved` -> always eligible, observation not required (unchanged
    behavior).
  - `static`/`external` -> eligible only if exactly one distinct normalized
    observed host matches the normalized desired host; otherwise
    `observation_missing` / `observation_mismatch` / `observation_ambiguous`.
  - `ip_policy_not_dhcp_reserved` as a skip reason no longer exists — a
    non-DHCP endpoint with a satisfied observation condition now proceeds into
    the same create/link/conflict logic DHCP endpoints already used.
- `ip_address_create_fields()` and a new `_type_choice_for_policy()` /
  `_resolve_type_choice()` pair make `IPAddress.type` selection policy-aware:
  `dhcp_reserved` resolves the DHCP-equivalent choice (was `_dhcp_type_choice`,
  renamed/generalized), `static`/`external` resolve the Host-equivalent choice
  via `HOST_TYPE_VALUES = {"host"}`. If the model exposes a `type` field but no
  compatible choice can be resolved, the plan returns `conflict` /
  `ip_address_type_unresolvable` instead of creating.
- `_existing_ip_conflicts()` is now policy-aware: an existing candidate's type
  must be in the policy-compatible set (DHCP-equivalent for `dhcp_reserved`,
  Host-equivalent otherwise). An empty/unknown existing type is now also a
  `ip_address_type_conflict` (previously only a non-empty incompatible type
  conflicted) — this matches the plan's explicit instruction to treat empty,
  unknown, and incompatible types alike, and does not overwrite the existing
  row.
- Existing fail-closed behavior for DNS conflicts, duplicate candidates, and
  realized-link mismatch is unchanged; it now happens after the eligibility
  gate rather than after a hardcoded `dhcp_reserved` gate.

Every branch above is exercised by Django-free unit tests (no Nautobot/Django
import in this module or its test file).

## Test changes

`nintent/nautobot_intent_catalog/tests/test_operations_ipam.py`:

- Replaced `test_non_dhcp_reserved_endpoint_is_skipped` (asserted the old
  `ip_policy_not_dhcp_reserved` skip) with
  `test_static_endpoint_without_observation_is_manual_review_skip`.
- Added: static/external create-eligible-with-matching-observation (Host
  type), prefix-notation host-portion matching, mismatching observation is a
  conflict-class skip, multiple conflicting observations are ambiguous,
  `dhcp_reserved` still needs no observation, unknown policy fails closed,
  existing Host type compatible with static, existing DHCP type conflicts with
  static, existing Host type conflicts with `dhcp_reserved`, create refuses to
  proceed when the model lacks the required type choice, invalid desired IP is
  out-of-scope regardless of policy, and the plan's `as_dict()` carries policy/
  observation/eligibility evidence.

## Verification

```
$ python3 -m unittest discover -s nautobot_intent_catalog/tests -p 'test_operations_ipam.py'
Ran 31 tests in 0.001s
OK

$ python3 -m unittest discover -s nautobot_intent_catalog/tests
Ran 111 tests in 0.016s
OK
```

No Django/Nautobot import was added to this module; the full local nintent
suite (Django-free) passes. `jobs.py` still calls
`plan_endpoint_ipam_reconcile()`/`ip_address_create_fields()` with their old
argument names only (no `observed_ip_candidates` or `ip_policy` passed yet),
so Step 1 is backward-compatible at the call site — Step 2 wires the Job's
queryset, per-endpoint observation extraction, and write-time recheck through
these new parameters.

## Status

Step 1 complete. Not yet deployed (no Nautobot-backed or live verification
performed in this step; that follows the plan's later phases).
