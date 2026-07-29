# LXC Initial Network Configuration — Implementation Plan

Date: 2026-07-29

## Goal

When creating a Proxmox LXC with a static endpoint, pass the IPv4 CIDR and gateway from desired
state to `pct create --net0`.

Make the network configuration applied manually to `agfixture` the standard creation result:

```text
ip=192.168.0.9/24
gw=192.168.0.1
```

This plan covers initial creation only. Changes to existing guests, IPv6, multiple NICs, DNS
configuration, DHCP, and guest user or SSH setup are out of scope.

## Current State

- `DesiredEndpoint` has `ip_policy`, `ip_address`, and MAC fields, but no gateway.
- `agfixture` is registered with `ip_policy: static` and `ip_address: 192.168.0.9`.
- The LXC creation playbook passes only the bridge and MAC to `net0`.
- Phase 3 deliberately left initial network configuration to the manual console bootstrap.
- VMID 109 now has `192.168.0.9/24` and `192.168.0.1`, configured manually.

## Target Contract

An endpoint used for initial static IPv4 configuration has the following structured values:

```yaml
desired_endpoints:
  - name: primary
    desired_node: agfixture
    ip_policy: static
    ip_address: 192.168.0.9/24
    gateway_address: 192.168.0.1
```

- Reuse the existing `ip_address` field and require IPv4 CIDR notation when it is used for
  creation.
- Add `gateway_address` as an optional `DesiredEndpoint` field.
- An endpoint with a gateway must use `ip_policy: static` and an IPv4 CIDR.
- The gateway must be a usable IPv4 address in the same subnet as the endpoint.
- A compute instance is creation-ready only when it has exactly one primary endpoint satisfying
  this contract.
- Include normalized `ipv4_cidr` and `gateway_ipv4` values in the creation plan parameters.
- Generate the following playbook `net0` value:

```text
name=eth0,bridge=<bridge>,hwaddr=<mac>,ip=<ipv4_cidr>,gw=<gateway_ipv4>
```

The Braindump is the semantic basis for these values, but it is not an execution input. Creation
uses only values written to confirmed desired state through the Import Job.

## Implementation

### 1. Extend DesiredEndpoint

Add nullable `gateway_address` to `nintent`, including its migration, model validation, GraphQL
read path, YAML loader/import path, and canonical seed path.

Keep existing uses of `ip_address` working. Existing endpoints without CIDR notation remain valid,
but they are not eligible for static LXC initialization. Creation preflight must explain the
missing information.

Update `agfixture` in `nauto/seed/intent_sources.yaml`:

```yaml
ip_address: 192.168.0.9/24
gateway_address: 192.168.0.1
```

### 2. Update nctl desired reads and creation preflight

Add `gateway_address` to the `DesiredEndpoint` typed model and GraphQL query.

During compute-creation derivation, validate and normalize the primary endpoint's IPv4 interface
and gateway. Put the resulting values in the creation parameters. If the endpoint is incomplete
or invalid, do not plan a creation action; report the reason through the existing compute
preflight-failure mechanism. Exact type names, function boundaries, and failure codes are left to
the implementer.

Reuse the existing IP and MAC collision checks. Do not reserve or manage the gateway itself as an
endpoint IP.

### 3. Apply the values in the LXC creation playbook

Add `ip` and `gw` to `--net0` in `create_lxc.yml`. The dry plan and execution must use the same
normalized values; Ansible must not independently infer network settings.

Keep the existing create, start, and result flow.

### 4. Apply the seed and update documentation

Deploy the nintent change to the scratch environment through the normal commit, user-push, and
Nautobot image rebuild workflow. Run the Import Job as preview, apply, and repeat no-op.

Update the LXC creation example in `nctl/README.md` to state that static IPv4 CIDR and gateway are
configured during creation, while guest SSH bootstrap remains a separate step.

## Verification

At minimum, verify the following:

1. The loader and model accept a valid IPv4 CIDR and gateway, and reject missing CIDR, another
   subnet, IPv6, and malformed values with understandable reasons.
2. The compute dry plan shows `ipv4_cidr` and `gateway_ipv4`; an incomplete endpoint produces no
   create action.
3. The Ansible conformance test's fake `pct` receives the complete expected `net0` argument.
4. The nctl ordinary, nintent Django-free, compute conformance, and Ansible conformance gates pass.
5. After applying the seed to scratch Nautobot, the `agfixture` desired endpoint reads as
   `192.168.0.9/24` with gateway `192.168.0.1`.

`agfixture` already exists, so acceptance does not require recreating it or running `pct set`.
When another disposable LXC is created, confirm its configuration through `pct config` and verify
the address and default route inside the guest.

## Minimal Constraints

- Do not turn Braindump prose directly into `pct` arguments.
- Do not add `pct set` or guest recreation for existing guests as part of this plan.
- Do not add unrelated stop, destroy, resize, or migrate operations.

Within these constraints and the target contract, file layout, type names, failure codes,
migration breakdown, test placement, and commit boundaries are left to the implementer.

## Completion Criteria

- A new static IPv4 LXC dry plan and `pct create` use the same CIDR and gateway.
- Incomplete or contradictory network intent stops before creation with an understandable reason.
- Existing LXC create/start, observation, ledger-link, and non-repetition behavior remains intact.
- The seed, current README, and final report describe the implemented contract.
