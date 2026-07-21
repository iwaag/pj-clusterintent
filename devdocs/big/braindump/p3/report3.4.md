# Step 3.4 — Refresh evidence and conduct the unexplained-service conversation

Status: blocked pending a fix to the operation-scoped Ansible privilege configuration.

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

No second `reconcile --yes` was run after this correction. A new actual-state collection remains a
separate approved operation.

## Discrepancies

Step 3.4 cannot meet its fresh-observation or unexplained-service exit criteria until a post-fix
collection is explicitly approved, succeeds, and a new report is ingested.
