# Step 3.4 — Refresh evidence and conduct the unexplained-service conversation

Status: complete.

## 1. Plan-only operation

`nctl reconcile agpc --json` produced plan operation `01KY2MJDC188VJ4RPH1KHQSDX5`.

- Scope: `agpc` only.
- Planned reconciler action: `observe_node`.
- Intended effect: fresh nodeutils collection followed by Nautobot ingest to resolve or refine stale
  actual evidence.
- The plan contained no desired-service or DNS/DHCP intent change.

## 2. Approved apply operation

After explicit approval, `nctl reconcile agpc --yes --json` ran operation
`01KY2MNBRNPPPC1173FH1KPC16`.

- Terminal state: `non_converged` (`no_progress`).
- The `observe_node` action started but failed before a fresh report was produced.
- The prior report retrieved from `agpc` was still dated 2026-06-26 and was rejected as stale.
- The operation artifact `ansible/collect.stdout` identifies the immediate collection failure:
  Ansible fact gathering stopped with `Missing sudo password`.
- Reconcile's normal post-action path regenerated the production inventory and refreshed the
  dashboard's derived reconciliation-status cache. It did not change desired services, placements,
  node lifecycle, DNS/DHCP intent, or the actual observation.

## 3. Unexplained-service case result

No fresh observed-service inventory exists after this operation. Therefore the stale `prometheus`
candidate on `agpc` was not used to start the unexplained-service conversation, and no service was
classified as unwanted, managed, or removable.

The affected machine-placement and onboarding-policy reviews were replaced in place to explain the
failed refresh. Their review UUIDs remained `bbd8f745-53f6-416b-a4a6-1b9d4cbe1a16` and
`f2b5e92f-edd2-48b5-9349-e8c10eefbd22`, respectively.

## 4. Root-cause diagnosis

This is not an `agpc` sudo-authority omission:

- The Ansible connection user is `eiji`.
- `sudo -n -l` on `agpc` reports `(ALL : ALL) ALL`, so the user has full sudo authority but must
  authenticate with a password except for two suspend commands.
- With the normal generated inventory, `ansible_become_password` is non-empty from the local vault.
- With nctl's operation-scoped bootstrap inventory, the same variable is empty. That generated
  inventory lives under the operation artifact directory and has no adjacent
  `group_vars/all/vault.yml`, so the normal inventory's group variables are not discovered.

The direct corrective target is the nctl/Ansible inventory-variable handoff, not a broad change to
`agpc` sudoers. No correction was applied in this step.

## 5. Follow-up correction

The handoff was corrected after the failed operation in nctl commit `3f65248`
(`Preserve shared inventory vars during observations`). Both the nodeutils collection and report
slurp commands now pass the operation-scoped bootstrap inventory first and the configured normal
inventory second. This preserves the fresh operation host selection while allowing Ansible to load
the normal inventory's adjacent `group_vars`, including the vaulted become credentials.

The exact two-inventory command shape was checked against the live local inventories: the generated
operation inventory alone leaves `ansible_become_password` empty, while adding the configured
production inventory makes it non-empty. Focused observation tests (6) and the full nctl suite
(733 passed, one existing warning) pass at the correction commit.

## 6. Post-fix collection and unexplained-service result

After explicit approval, the corrected nctl ran `nctl reconcile agpc --yes --json` as operation
`01KY2ND30BVR6912R2NN222B9K`.

- Terminal state: `converged`.
- `observe_node` successfully collected `agpc` and the Nautobot ingest outcome was `updated`.
- `agpc` actual and service-inventory timestamps are now `2026-07-21T15:41:20Z`.
- A scoped post-operation drift has one `agpc` target, `converged`, with only
  `intent_effect_summary`; the full cluster summary moved from `converged: 2, unknown: 4` to
  `converged: 3, unknown: 3`.
- Fresh observed services on `agpc` include `prometheus`.

All three current Braindump bodies were checked through nctl and do not mention `prometheus`.
The desired catalog still contains only `dnsmasq`, with no `prometheus` DesiredService or placement.
The updated machine-placement review therefore asks the user whether the fresh `prometheus`
observation is an intentional unmanaged workload, an experimental project, a service to bring under
management, or a candidate for separately confirmed removal. It does not classify it as unwanted
and makes no desired-state or service-execution change.

## 7. User disposition

The user explicitly set the current policy that all unmanaged services are intentional unmanaged
workloads for now. This was stored as a new `user_direct` Braindump
`c1e2eb7c-0efc-4968-965c-2a40695d8049` with one current review
`04b3c325-2f5c-4700-a3f9-61e8afc2c5ec`.

Accordingly, the fresh `prometheus` observation on `agpc` is recorded as intentional unmanaged
state. It remains absent from desired state, is not included in reconcile planning, and was neither
stopped nor removed. The same policy applies to future fresh observations of unmanaged services;
the older `agstudio` service inventory is not asserted to be current merely because this policy
exists.

## Discrepancies

None for Step 3.4. Moving a named unmanaged service into desired state, stopping it, or removing it
remains a separate user-confirmed action.
