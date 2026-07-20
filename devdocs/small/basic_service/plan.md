# basic_service Implementation Plan: first-class dnsmasq service placement + bootstrap path

Goal: make the two scenarios in `.local/scenerio1.txt` / `.local/scenario2.txt` work end to end —
a freshly purchased PC is registered in nintent by its mDNS name, bootstrapped via the
hosts-intent inventory, and the cluster's most basic service (dnsmasq) is declared as a
`DesiredService` placement and actuated through the same generic placement machinery every other
service uses. `render production` keeps sourcing connection facts from the ledger/actual state
(scenario 2-3 is accepted as already correct — no change there).

## Current state (as of 2026-07-20)

Most of the machinery already exists; the gaps are small and specific.

Already in place:

- `DesiredService` + `DesiredServicePlacement` (`nintent/nautobot_intent_catalog/models.py`):
  placement binds a service instance to a `DesiredNode` via `instance_name`,
  `deployment_profile` (slug), `config_schema_version`, `desired_state`, `config`. This is the
  generic placement mechanism; **no nintent schema change is needed** (which also means no
  nintent push/rebuild cycle per `.local/localenv_memo.md`).
- `ansible_agdev/vars/deployment_profiles.yml` already declares profile `dnsmasq` → group
  `dnsmasq_server` with a full schema-1 variable map, and
  `deployment_profile_reconciliation.dnsmasq` → `action.kind: dnsmasq_config`.
- `nctl render production` (`production/composer.py`) already derives the `dnsmasq_server`
  group from active placements with `deployment_profile: dnsmasq`. Group membership from
  placements is the established pattern — this plan extends it, not replaces it.
- `roles/dnsmasq_server` + `playbooks/bootstrap/setup_dnsmasq.yml` (hosts: `dnsmasq_server`)
  install/configure the daemon; `playbooks/dnsmasq/deploy_dnsmasq_records.yml` pushes the
  rendered records conf.
- The reconcile executor (`reconcile/executor.py:447`) maps `dnsmasq_config` actions to
  `build_dnsmasq_apply`.
- `run_nodeutils_collect.yml` targets `ssh_hosts`, which `render hosts-intent` emits — the
  scenario-1 collect step is group-compatible today.

Gaps this plan closes:

1. **`ansible_host` is never set from `mdns_name`** — `hosts_intent.py::_host_vars` exports
   `mdns_hostname` but Ansible connects to `inventory_hostname` (the node slug). Scenario 1
   step 3 requires connecting to `<mdns_name>` (e.g. `agdnsmasq.local`).
2. **`hosts_intent.yml` contains only `ssh_hosts`** — no service groups, so bootstrap-time
   actuation (installing dnsmasq before any production inventory exists) has no
   `dnsmasq_server` group to target.
3. **The `dnsmasq_config` action only pushes records** — `setup_dnsmasq.yml` (daemon install)
   is not reachable from `nctl reconcile`/`apply`; on a fresh node the records deploy would
   restart a `dnsmasq.service` that was never installed.
4. **`apply dnsmasq` is hardwired to the configured production inventory**
   (`dnsmasq_apply.py`, `cfg.ansible.resolved_inventory`) — a chicken-and-egg on a fresh
   cluster, where only the bootstrap inventory exists.

## Design decisions

- **dnsmasq is data, not schema** (scenario 2-1): declare it as
  `DesiredService(name="dnsmasq", service_type="service")` plus one
  `DesiredServicePlacement(instance_name="dnsmasq", deployment_profile="dnsmasq",
  desired_state="active")` on the target `DesiredNode` (e.g. `agdnsmasq`). "Which node runs the
  dnsmasq daemon" (placement) stays orthogonal to "which endpoints get dnsmasq records"
  (`DesiredEndpoint.generate_dnsmasq` / `dnsmasq_record_type`) — the two concerns are not
  merged.
- **Service groups derive from placements, in both inventories** (scenario 2-2): the single
  source of a group name is `deployment_profiles.<profile>.group`; membership is active
  placements. `render production` already does this with full variables; `render hosts-intent`
  gains the same groups as bare membership (empty host objects, connection vars come from
  `ssh_hosts`), so bootstrap-time playbooks can target service groups over mDNS. No
  hand-maintained group ever exists.
- **Daemon install is part of the dnsmasq action**: `dnsmasq_config` becomes "ensure daemon,
  then push records" — the setup playbook is idempotent (a role), so running it before every
  records deploy is safe and removes the orphaned manual step. A separate action kind or a
  two-profile split (install vs records) would spread one service across two placements for no
  benefit.
- **Inventory override is explicit**: `nctl apply dnsmasq --inventory PATH` overrides the
  configured inventory for the bootstrap case. No silent fallback — an implicit switch from
  production to bootstrap inventory could actuate over stale mDNS names without the operator
  noticing. `reconcile` keeps using the production inventory it regenerates itself.

## Step 1 — hosts-intent: connect via mDNS

- `nctl/src/nctl_core/hosts_intent.py::_host_vars`: emit `ansible_host: <endpoint.mdns_name>`
  alongside the existing `mdns_hostname` var (keep `mdns_hostname` — production's
  `resolve_connection_variables` and humans read it).
- Tests: extend the hosts-intent renderer tests to assert `ansible_host` presence and value;
  a node whose selected endpoint has no `mdns_name` is already skipped, so no new skip reason.

## Step 2 — hosts-intent: service groups from placements

- Extend the hosts-intent GraphQL query to fetch active `DesiredServicePlacement` rows
  (service name, node id, `deployment_profile`, `desired_state`).
- Load `deployment_profiles.yml` (reuse `production/profiles.py` loading/validation) to map
  `deployment_profile` → group name. Placements with an unknown profile are reported in the
  export's skip/warning list, not silently dropped.
- Emit each group with member hostnames only (empty host objects, mirroring the production
  contract's rule that service-group members carry no vars — `production/contract.py`
  `_require_slug`/empty-object checks). Members must already be in `ssh_hosts`; a placement on
  a node that was skipped (no mDNS endpoint) is reported and omitted.
- Schema: bump the `nctl.render.hosts_intent.v1` envelope if the JSON payload shape changes
  (groups list); breaking-change phase, no compatibility shim.
- Tests: fixture with one dnsmasq placement → `dnsmasq_server: {hosts: {agdnsmasq: {}}}` in
  the emitted YAML; unknown-profile and skipped-node cases covered.

## Step 3 — declare dnsmasq in the ledger (data entry, documented)

- Create via nintent UI/REST on the live instance: `DesiredService` "dnsmasq" and an active
  placement on the dnsmasq host with `deployment_profile: dnsmasq`, `config` holding the
  operational knobs (`interfaces`, `enable_dhcp`, `local_domain`, …) that
  `map_placement_config` already maps to `dnsmasq_*` Ansible variables.
- Document the exact fields in `nctl/docs/` (or the README's workflow section) as the
  reference "add a basic service" recipe — this is the template scenario 2 generalizes from.
- No code in this step; it is listed because the scenarios are only "achievable" once the
  recipe is written down and exercised once.

## Step 4 — dnsmasq action installs the daemon

- `nctl/src/nctl_core/dnsmasq_apply.py`: before invoking `deploy_dnsmasq_records.yml`, run
  `playbooks/bootstrap/setup_dnsmasq.yml` against the same inventory/group, same
  check/diff-vs-apply mode, its own `ansible/dnsmasq-setup` artifact stem and events. A setup
  failure aborts before the records deploy.
- The reconcile executor path (`dnsmasq_config` → `build_dnsmasq_apply`) inherits this with no
  planner changes; the plan's action description should mention both phases.
- Tests: runner-level test asserting the two playbook invocations in order and abort-on-setup-
  failure; envelope gains a `setup` result field next to the existing `ansible` one (schema
  bump of `nctl.apply.dnsmasq.v1`).

## Step 5 — `apply dnsmasq --inventory PATH`

- CLI option on `nctl apply dnsmasq`; plumb into `build_dnsmasq_apply` as an optional override
  of `cfg.ansible.resolved_inventory`. The envelope's `inventory_path` already reports which
  inventory was used.
- Validation is unchanged: the chosen inventory must resolve ≥1 host in `dnsmasq_server`
  (which the bootstrap inventory now provides after Steps 2–3).
- Document the bootstrap sequence this enables (see verification below).

## End-to-end verification (the scenarios, replayed)

Scenario 1:
1. Register the new PC in nintent: `DesiredNode` + `DesiredEndpoint` with `mdns_name`
   (`<host>.local`) and `description`.
2. `uv run nctl render hosts-intent --out ansible_agdev/inventories/generated` — inventory
   connects via mDNS (`ansible_host` set), groups include any service placements.
3. `ansible-playbook -i inventories/generated/hosts_intent.yml
   playbooks/nautobot/run_nodeutils_collect.yml` succeeds against the new host.

Scenario 2:
1. Declare the dnsmasq service + placement (Step 3 recipe).
2. `uv run nctl apply dnsmasq --inventory ansible_agdev/inventories/generated/hosts_intent.yml`
   (dry-run first, then `--yes`) — installs the daemon and pushes DNS names / DHCP
   reservations rendered from `DesiredEndpoint`/`DesiredIPRange` desired state.
3. After nodeutils collection + ingest (`nctl reconcile`), `uv run nctl render production`
   emits `production.yml` with the `dnsmasq_server` group and connection facts resolved from
   the ledger — unchanged behavior, confirmed as the intended source (scenario 2-3).

## Exit criteria

- Both scenario transcripts above run without manual inventory editing or manual playbook
  wiring; every group in every generated inventory is derived from placements + profiles.
- `nctl reconcile` on a fresh dnsmasq node converges: daemon installed, records deployed,
  drift `converged`.
- No nintent schema change was needed; the "add a basic service" recipe is documented.
