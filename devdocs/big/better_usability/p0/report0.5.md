# Phase 0 — Step 0.5 report: Build the consumer and transition impact map

Parent: [plan.md](plan.md) Step 0.5.

## What was done

Added `field-classification.md` §5b (runtime consumer boundaries: `sources/desired.py`,
`production/adapter.py`, `production/composer.py`, `drift/comparators.py` +`evaluation.py`
+`evaluation_snapshot.py` +`service_placement.py`, `reconcile/executor.py`'s OS-playbook selection,
`production/contract.py`'s schema/host-variables, nintent's own display-only readers) and the
transition impact map (required migration / existing-row policy / output-schema bump / coordinated
deploy order and rollback point / deletion list for each identified schema change).

To close the plan's explicit requirement ("confirming whether each exported variable is consumed or
only metadata"), traced every `_BASE_HOST_VARIABLES` name against `ansible_agdev`'s actual
playbooks/roles/templates (excluding the generated inventory output).

## Findings surfaced in this step

- **`reconcile/executor.py` reads only `expected_host_os`/`declared_host_os`** from the operational-
  config cluster (for OS-specific playbook selection); `connection_path`, `local_endpoint`,
  `tailscale_endpoint`, `ansible_port`, `power_control`, and `is_laptop` are consumed **only** inside
  `production/composer.py` at render time, never at reconcile time. This narrows exactly what Phase
  2's derivation must keep stable for `reconcile/` versus what only needs to stay stable for
  `production/`.
- **`DesiredNode.lifecycle` is not read anywhere in `drift/evaluation.py`'s node/endpoint/service
  checks** — only `production_policy` (via re-running the composer) is lifecycle-sensitive. Phase
  3's default change therefore has no drift-engine-side migration concern, only the
  production-composer path already covered by Phase 1/2.
- **Ansible consumption of exported host variables is uneven**, confirmed by grep against real
  playbook/role/template source (not the generated inventory): `host_os`, `power_control`, and
  `is_laptop` are genuinely branched on (`playbooks/power/*_home_assistant_power_switches.yml`,
  `playbooks/bootstrap/linux_initial_setup.yml`). `connection_path` and `tailscale_ip` are exported
  but **not read by any playbook task** — `connection_path` appears only as a hardcoded literal
  string in one template, never as a read of the actual inventory value. The four `nintent_*`/
  `nautobot_device_id` provenance variables have zero references anywhere in `ansible_agdev` source,
  confirming `contract.py`'s own docstring claim that they're for humans/nctl, not Ansible.
  `ansible_port` is consumed by the Ansible engine itself as a reserved connection variable, not by
  playbook logic — its absence from grep hits is expected, not a gap.
- This directly informs the Phase 2 deletion list: **removing/renaming `nintent_operational_config_id`
  from the production contract is safe** — no playbook reads it — and gives Phase 2 a validated
  reason `connection_path`'s current export may be safe to keep as pure provenance even if its
  underlying field is dissolved into a computed value.
- Built the transition impact map covering all 6 identified changes (`DesiredNode.lifecycle`
  default, `DesiredNodeOperationalConfig` dissolution, cross-path default reconciliation,
  `missing_operational_config` local-fail, placement-config unapplied-intent finding,
  `IntentSourceForm` cache-field removal), each with migration/rollback specifics per roadmap's
  coordinated-breaking-rollout rule.

No blocking surprises requiring human judgment.

## Next step

Step 0.6 — classify every production `ContractError`/skip-reason code into the failure-scope
matrix required by Phase 1, using the `composer.py`/`contract.py` call-site inventory already
gathered.
