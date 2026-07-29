# Step 6 Report — Apply, idempotency, drift, and dry plan

Status: stopped; the Step 6 gates are not met, so `nctl reconcile agfixture --yes` was not run.

## Authorized import apply

After user approval of the Step 5 preview, the supported `Import Intent Sources` Job applied the
exact previewed canonical file at `/opt/nautobot/intent_sources.yaml`.

- JobResult `a65c597a-c160-4bc3-9ffd-037d6bee3f45`: `success`.
- Artifact: `.local/vm_converge_fix/step6-import-apply/apply.json`.
- `writes`: requested/attempted/committed all `true`; post-commit confirmation status `confirmed`
  with no mismatches.
- The committed changes were exactly:
  - `DesiredNode agfixture.accepted_actual_types`: `[virtual_machine]` -> `[device]`;
  - `DesiredEndpoint agfixture/primary.gateway_address`: `null` -> `192.168.0.1`.

## Idempotency gate failure

The required immediate repeat import was run as JobResult
`3a68d380-93d2-4f45-a4f6-c4e9ff43f77f` (`success`), with artifact
`.local/vm_converge_fix/step6-import-apply/repeat.json`.

It was **not** a no-op: totals were `create=0`, `update=1`, `unchanged=26`, `conflict=0`, and it
again planned/committed:

```text
DesiredEndpoint agfixture/primary.gateway_address: null -> 192.168.0.1
```

This contradicts the required repeat/no-op proof even though the Job's own confirmation reports
`confirmed`. No further import retry was attempted.

## Fresh drift and dry plan

The subsequent read-only commands completed:

```text
nctl drift --host agfixture --json
nctl reconcile agfixture --json
```

The fresh drift confirms the compute-instance target is converged and remains linked to
VirtualMachine `3a6aa5b1-f128-4d23-82f7-9c97acff3a68`; it does not propose any compute
create/start/relink action. The node remains `unknown` with `actual_node_not_linked`,
`no_realized_device`, `no_realized_object`, and `ipam_reconcile_observation_missing`.

The dry-plan operation is `01KYPWMHB49123AMJ7M7AKYAVJ`. It contains no automatic action and has
manual-review findings for `ipam_reconcile_observation_missing` and `no_realized_object`; it does
not identify the expected existing Device candidate for `link_actual_node`. It is therefore not an
approvable Step 6 apply plan.

No `--yes` reconcile, direct ledger write, guest create/start/relink, SSH/Ansible guest mutation,
or VM mutation was performed in this step.
