# Problem: `reconcile_ipam` job scope excludes statically-assigned endpoints

## Observed symptom

`nctl drift` reports a persistent `missing_actual_ip_address` warning for `agdnsmasq`
even after a full `nctl reconcile` run. nodeutils correctly observes the host's IP
(`192.168.0.2`, see `primary_ip_address` in the nodeutils cache), so the gap is not an
observation problem.

## Root cause

`missing_actual_ip_address` is about the Nautobot IPAM (`ipam.ipaddress`) object layer,
not the nodeutils-observed interface fact. The job meant to close this gap —
`Reconcile Desired IPAM Intent` (`nintent/nautobot_intent_catalog/jobs.py:344`) — only
considers `DesiredEndpoint` rows where:

```python
DesiredEndpoint.objects.filter(ip_policy="dhcp_reserved")
```

`agdnsmasq`'s primary endpoint has a manually/statically declared `ip_address`
(`192.168.0.2`) under a non-`dhcp_reserved` `ip_policy` (default is `external`), so it is
filtered out before the job ever evaluates it. Running the job scoped to `agdnsmasq`
confirms this: the job's summary artifact reports `"endpoints": 0`. The job cannot ever
close this gap for this endpoint by design, regardless of how many times reconcile runs.

## Design concern

The filter conflates two different things: "which IPs are DHCP-reserved" and "which IPs
are explicitly, deterministically declared in desired state." The system's stated
philosophy (see `README.md`, `agentdocs/brainforge/README.md`) is to actuate explicitly
declared desired state deterministically rather than guess. An endpoint with a concrete,
explicitly declared `ip_address` — regardless of `ip_policy` — is exactly the kind of
explicit intent this system is meant to reconcile automatically. Restricting the
automatic IPAM job to `ip_policy="dhcp_reserved"` leaves statically/externally assigned
endpoints permanently unreconcilable through the normal automated path, with no
automatic route to close the resulting drift.

## Recommendation

The job's scoping criterion should be based on whether the endpoint has an explicit,
concrete `ip_address` value (and, ideally, that it matches the host's own observed
address), not on the `ip_policy` value in isolation. `ip_policy=external` legitimately
covers endpoints whose IP is intentionally owned by another system, so scope should not
widen indiscriminately to all policies — but an endpoint with both an explicit desired
`ip_address` and a matching self-observation is a case the system already has enough
information to reconcile deterministically, and today it does not.
