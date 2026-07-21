# Step 3.6 — Propose and write one confirmed structured desired-state change

Status: complete.

## 1. Approved proposal

The user explicitly approved the narrow structured desired-state change proposed from the LAN/DNS
Braindump:

```text
DesiredNode agdnsmasq
lifecycle: planned -> active
```

This was selected because the desired `dnsmasq` service and its active placement already existed on
`agdnsmasq`; its `planned` lifecycle alone excluded that placement from production application.

## 2. Canonical write and confirmation

The established `nctl lifecycle` writer performed the exact REST PATCH and fresh GraphQL
confirmation.

- Node ID: `27818c12-fe15-4c9f-83d0-7949523f6c33`
- Node slug: `agdnsmasq`
- Previous lifecycle: `planned`
- Requested/current lifecycle: `active`
- Result: `changed: true`, schema `nctl.lifecycle.v1`

No node endpoint, IP range, DesiredService, DesiredServicePlacement, deployment profile, or
unmanaged workload was created, removed, or modified.

## 3. Post-write state

A scoped `nctl drift --host agdnsmasq --json` returned the node target as `converged`, with only
`intent_effect_summary` and `missing_actual_ip_address` records. The desired dnsmasq placement is
now eligible for production application; this does not itself prove that dnsmasq is installed,
running, or freshly observed.

The LAN-policy review and onboarding-policy review were replaced in place to explain the confirmed
desired commitment and the remaining apply gate. Their review UUIDs remained
`e28d37c8-4916-4b26-8a36-862f93131aab` and `f2b5e92f-edd2-48b5-9349-e8c10eefbd22`.

## 4. Reconcile boundary

No `nctl reconcile --yes`, Ansible service action, nodeutils collection, DNS/DHCP application, or
manual host operation occurred in this step. Step 3.7 must first obtain a scoped plan and then a
separate apply confirmation.

## Discrepancies

None for Step 3.6.
