# Nautobot-backed and Live Verification

## 1. Deploy

- User pushed the nintent commits; `origin/main` confirmed at `ccddd8037698a92b8f92f03d63e5055e2f02dd2f`.
- `docker compose build --no-cache nautobot`: resolved commit
  `ccddd8037698a92b8f92f03d63e5055e2f02dd2f` in the pip-install log.
- **Gotcha hit and fixed**: the first rebuild only targeted the `nautobot`
  service. `nautobot-worker`/`nautobot-scheduler` have their own `build:`
  stanzas in `docker-compose.yml` (separate images), so they kept running the
  pre-change code (`filter(ip_policy="dhcp_reserved")`) until rebuilt
  separately. `docker compose build --no-cache nautobot-worker
  nautobot-scheduler` (same resolved commit) + `up -d --force-recreate` fixed
  it; confirmed by grepping the installed `jobs.py` inside
  `nautobot-nautobot-worker-1` for the new `.exclude(ip_address__isnull=True)`
  queryset before proceeding.
- `nautobot-server makemigrations nautobot_intent_catalog --check --dry-run`:
  `No changes detected in app 'nautobot_intent_catalog'`.
- Job discovery: `nautobot_intent_catalog.jobs.jobs` includes
  `ReconcileDesiredIPAMIntent`; `Meta.description` is the updated
  policy-aware text (no longer DHCP-only).
- Real `IPAddress.type` choices: `[('dhcp', 'DHCP'), ('host', 'Host'),
  ('slaac', 'SLAAC')]`. `_type_choice_for_policy` resolves `dhcp_reserved ->
  dhcp`, `static -> host`, `external -> host` against this live model.

## 2. Pre-deployment evidence (agdnsmasq)

- `nctl drift --host agdnsmasq --json`: `missing_actual_ip_address` present
  for endpoint `primary` (`0dea1561-bfb7-4058-8ba7-c71d18666cad`,
  `ip_policy=static`, desired `192.168.0.2`), with the new evidence payload
  (`observed_hosts: ["192.168.0.2"]`, basis
  `realized_device.primary_ip_address`, `last_seen`).
- Confirmed via `nautobot-server shell`: `IPAddress.objects.filter(host=
  "192.168.0.2").count() == 0`; endpoint's `realized_ip_address` was `None`;
  `desired_node.realized_device.custom_field_data["primary_ip_address"] ==
  "192.168.0.2"`.
- `nctl reconcile agdnsmasq` (dry run, before the worker fix): plan contained
  exactly one `reconcile_ipam:agdnsmasq` action pinning
  `eligible_endpoint_ids: ["0dea1561-bfb7-4058-8ba7-c71d18666cad"]`.

## 3. Scoped apply

Presented the dry plan to the user; approved explicitly before any live write.

- First attempt (worker still stale) correctly **failed closed**:
  `ipam_summary_coverage_mismatch: eligible endpoint id(s)
  ['0dea1561-...'] pinned at plan time are missing from the Job's plan rows` —
  Step 4's coverage check caught the stale-worker artifact (`endpoints: 0`)
  instead of reporting false success. `state: non_converged`, `ok: false`.
  This is exactly the scenario plan.md's completion criteria calls out
  ("never treat `endpoints: 0` ... as successful evidence") and it worked as
  designed on a real deployment defect, not just in unit tests.
- After rebuilding/restarting the worker+scheduler, `nctl reconcile
  agdnsmasq --yes` reached `state: converged`, `ok: true`, both actions
  `[ok]` (`reconcile_ipam:agdnsmasq`, `regenerate_production_inventory`).
- Positive evidence confirmed via `nautobot-server shell`:
  - `IPAddress` at host `192.168.0.2`, `type=host`, `status=Reserved`.
  - `DesiredEndpoint.realized_ip_address` points to that `IPAddress`;
    `realized_ip_address_source="derived"`.
- Fresh `nctl drift --host agdnsmasq --json`: no `missing_actual_ip_address`
  (only the informational `intent_effect_summary` diff remains).
- Immediate `nctl reconcile agdnsmasq` dry plan: `actions: []` — no repeated
  `reconcile_ipam`.
- Cluster-wide `nctl drift --json`: `agbach`/`aghub`/`agpc`/`agstudio`/
  `dnsmasq` all remain `converged` with unchanged diff sets — no other
  node's or service's desired/actual state was touched.

## 4. Negative boundaries

Not exercised against the live cluster (plan.md forbids falsifying desired
IPs/observations on real infrastructure); covered by the unit/component tests
added in Steps 1, 3, and 4:

- External/static endpoint whose observed IP does not match:
  `test_external_endpoint_with_mismatched_observation_is_manual_review_gap`
  (nctl), `test_mismatching_observation_is_conflict` (nintent).
- Missing observation: `test_static_endpoint_without_observation_is_manual_review_gap`,
  `test_static_endpoint_without_realized_device_is_observation_missing` (nctl),
  `test_static_endpoint_without_observation_is_manual_review_skip` (nintent).
- Conflicting Device/VM observations: `test_multiple_conflicting_observations_are_ambiguous`
  (nintent); the nctl-side ambiguous basis remains structurally unreachable
  today since `ActualVirtualMachine` carries no custom fields (documented in
  report4.md).
- Host/DHCP type conflict: `test_existing_dhcp_type_conflicts_with_static`,
  `test_existing_host_type_conflicts_with_dhcp_reserved` (nintent).
- Duplicate `IPAddress` candidates: `test_multiple_matching_ips_are_conflict`
  (pre-existing, unaffected).
- Job artifact with `endpoints: 0`: `test_reconcile_ipam_rejects_zero_endpoint_artifact_when_none_pinned`
  (nctl) — and, as it happens, reproduced for real above by the stale-worker
  incident.
- Observation changing after drift but before the Job: covered by nintent's
  Step 2 write-time recheck design (documented limitation in report4.md: not
  independently unit-tested at the nctl layer since nctl never observes the
  Job's intermediate state).

No real service was stopped, no policy was weakened, and no actual custom
field was manually rewritten to produce these cases.

## Completion Criteria

- [x] The eligibility truth table is implemented and tested in both nctl and the Job.
- [x] `static`/`external` never writes automatically without a matching self-observation.
- [x] A non-DHCP address is never created or linked as DHCP type (created as `host` on the live system).
- [x] An empty Job, skip, conflict, or coverage mismatch cannot become false success (proven live, not just in tests, by the stale-worker `ipam_summary_coverage_mismatch`).
- [x] A real planner/executor multi-round test proves action execution and non-repetition (`test_real_multi_round_ipam_convergence_for_non_dhcp_endpoint`, plus the live round-trip above).
- [x] The full nintent and nctl local suites pass (111/111, 984/984).
- [x] Nautobot migration check, Job discovery, and worker deployment are verified.
- [x] The scoped dry run selects exactly one `agdnsmasq` endpoint.
- [x] An approved scoped apply creates or links the `IPAddress`.
- [x] Fresh scoped drift and the next dry plan prove non-repeating convergence.
- [x] Operation evidence contains no secrets, raw inventory, or unnecessary personal information (checked plan/result/job artifacts above).
- [x] The root, nintent, and nctl worktrees contain no unintended changes (`git status --short` clean in all three after each step's commit).

## Status: complete

All applicable items in plan.md's Completion Criteria are satisfied, including
live deployment and a supervised scoped apply against the real `agdnsmasq`
node.
