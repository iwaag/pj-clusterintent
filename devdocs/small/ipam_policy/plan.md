# IPAM Policy Reconciliation Plan

Date: 2026-07-23

## Goal

Allow a non-`dhcp_reserved` endpoint with an explicit `DesiredEndpoint.ip_address`
and a matching self-observed host address to be created or linked safely and
deterministically in Nautobot IPAM through the normal `nctl reconcile` path.

When complete, the current `agdnsmasq` state must pass through this closed loop:

```text
explicit desired IP + matching self-observation + missing IPAddress
  -> missing_actual_ip_address
  -> reconcile_ipam action is planned for agdnsmasq
  -> Reconcile Desired IPAM Intent processes the primary endpoint
  -> IPAddress is created or linked with policy-appropriate type
  -> DesiredEndpoint.realized_ip_address is linked
  -> fresh drift no longer reports missing_actual_ip_address
  -> the next dry plan does not repeat reconcile_ipam
```

Removing `ip_policy="dhcp_reserved"` from the Job queryset alone is not
sufficient. The Job eligibility rule, `IPAddress` type, nctl automation
classification, Job artifact verification, and multi-round convergence proof
must be corrected as one contract.

## Verified Baseline

The following implementation and local-environment behavior has been confirmed:

- `ReconcileDesiredIPAMIntent` in
  `nintent/nautobot_intent_catalog/jobs.py` restricts its endpoint queryset to
  `ip_policy="dhcp_reserved"`.
- `nintent/nautobot_intent_catalog/operations/ipam.py` also skips every
  non-`dhcp_reserved` endpoint with `ip_policy_not_dhcp_reserved`, and treats
  both new `IPAddress.type` selection and existing-type compatibility as
  DHCP-only.
- The nctl endpoint evaluator emits `missing_actual_ip_address` whenever no
  `IPAddress` corresponds to an explicit endpoint IP, regardless of policy.
- nctl always classifies that code as `AUTOMATIC/reconcile_ipam`, but does not
  treat a Job artifact with `endpoints: 0` as a coverage failure. This allows a
  successful but empty Job to repeat indefinitely.
- The `primary_ip_address` custom field on
  `DesiredNode.realized_device` is the existing actual-state boundary written
  by nauto from nodeutils `facts.network.primary_ip_address`. nctl already reads
  it as `ActualFacts.local_ip`.
- A read-only
  `uv run --project nctl nctl drift --host agdnsmasq --json` run on 2026-07-23
  reported the node target as `converged` while retaining one
  `missing_actual_ip_address` warning. The same output resolved the connection
  address to the nodeutils-observed `192.168.0.2`.
- The nintent local fast suite does not load Django or Nautobot. Queryset
  behavior, Job discovery, real `IPAddress` choices, and Celery-worker
  execution must also be verified in the deployed Nautobot environment.
- The Nautobot containers install nintent from a GitHub commit rather than a
  local source mount. Applying the change requires a commit, a user-performed
  push, and rebuild/restart of all three web, worker, and scheduler services.

## Scope and Non-goals

### In Scope

- IPAM reconciliation eligibility based on explicit IP intent
- A matching self-observation safety condition for non-DHCP endpoints
- Policy-appropriate `IPAddress.type` creation and existing-candidate checks
- Alignment between nctl drift/classification/planning and the nintent Job's
  defense-in-depth validation
- Host-scoped Job artifact coverage and truthful result reporting
- Unit, component, multi-round, Nautobot-backed, and scoped live verification
- Updates to current operator and developer documentation

### Out of Scope

- Changing `ip_policy` values or the model default
- Adding an Ansible actuator that configures the desired IP on the host OS
- Adding a general importer that projects nodeutils observations directly into
  IPAM objects
- Assigning an `IPAddress` to an `Interface`
- Deleting or releasing an `IPAddress`, or automatically overwriting existing
  attributes
- Changing the DNS or dnsmasq deployment contract
- Adding an endpoint or `IPAddress` model migration

`external` continues to mean that another system owns address configuration.
This change only creates or links the Nautobot ledger object when an explicit
desired IP and a matching self-observation already exist. It does not transfer
ownership of external configuration to nctl.

## Corrected Contracts

### 1. Eligibility Is Not Equivalent to `ip_policy`

Desired and observed primary IPs are normalized to their host portions before
comparison. For example, `192.168.0.2` and `192.168.0.2/24` represent the same
host address. An invalid string never counts as a match.

| DesiredEndpoint state | Self-observation | Automatic IPAM action |
|---|---|---|
| Valid explicit IP, `dhcp_reserved` | Not required | Eligible; preserve the existing reservation-intent behavior |
| Valid explicit IP, `static` | Matches the desired IP | Eligible |
| Valid explicit IP, `external` | Matches the desired IP | Eligible |
| Valid explicit IP, `static`/`external` | Missing | No automatic write; manual review |
| Valid explicit IP, `static`/`external` | Mismatch | Conflict; no automatic write |
| Valid explicit IP, `static`/`external` | Multiple distinct values | Ambiguous conflict; no automatic write |
| Empty or invalid desired IP | Any | Out of scope; no automatic write |
| Unknown policy | Any | Fail closed |

Here, self-observation means the `primary_ip_address` custom field available on
a linked realized object in Nautobot when the Job runs. The nintent Job must
not read the controller-local nodeutils cache directly. Normal nodeutils
collection followed by nauto ingest remains the sole write path for actual
observation. The plan evidence records this value and `last_seen`.

If both a linked Device and VM provide values, discard empty values and
normalize the remaining values to their host portions. One unique value is
usable; multiple distinct values are ambiguous and stop automation. If the
current nauto ingestion supports only Devices, the resolver must not guess a VM
value.

### 2. nctl and the Job Apply the Same Decision at Different Safety Boundaries

nctl drift determines eligibility from its fixed `SourceSnapshot` and explains
why a case is or is not automatable. The nintent Job re-evaluates the same
condition against current Nautobot state immediately before writing. The Job
check is defense in depth against state changing after drift was fetched; it
must not trust the earlier nctl decision unconditionally.

Only an eligible create or link gap emits the existing automatic codes:

- `missing_actual_ip_address`
- `actual_ip_address_not_linked`

When a non-DHCP endpoint does not satisfy the observation condition, emit one
of these node-targeted manual-review codes instead:

- `ipam_reconcile_observation_missing`
- `ipam_reconcile_observation_mismatch`
- `ipam_reconcile_observation_ambiguous`

Each diff must carry at least the endpoint id and name, `ip_policy`, normalized
desired IP, normalized observed IP candidates, current IPAM state (`missing` or
`unlinked`), realized-object reference, and observation timestamp. Do not retain
warnings with empty `desired={}` and `actual={}` evidence.

Register the three new codes as `MANUAL_REVIEW` so they do not repeatedly
trigger the Job. Do not add a matching-observation requirement to
`dhcp_reserved`: a DHCP reservation must remain capable of reserving ledger
state before the host is observed.

### 3. `IPAddress` Type Is Policy-aware

The current planner assumes that every selected endpoint is DHCP. Expanding
scope therefore requires a policy-specific type contract.

| Endpoint policy | New IPAddress type | Compatible existing type |
|---|---|---|
| `dhcp_reserved` | The Nautobot DHCP-equivalent choice | DHCP equivalent only |
| `static` | The Nautobot Host-equivalent choice | Host equivalent only |
| `external` | The Nautobot Host-equivalent choice | Host equivalent only |

Resolve actual Nautobot choice values and labels through model metadata; never
invent a choice string that the model does not expose. If the required type
choice cannot be resolved, stop the create as a conflict. If an existing
candidate has an empty, unknown, or policy-incompatible type, do not overwrite
it; report `ip_address_type_conflict`.

Preserve the existing safety boundaries:

- Multiple candidates for the same host address are a conflict.
- A linked `realized_ip_address` that differs from the desired IP is a conflict.
- An existing DNS name that differs from the desired DNS name is a conflict.
- Existing `IPAddress` attributes are not overwritten.
- A successful create or link saves
  `realized_ip_address_source="derived"`.

Redesigning status lifecycle is out of scope. Preserve the current
environment-compatible status resolver and generalize its DHCP-specific
documentation. If environment-backed verification reveals that status policy
must change, record it as a separate decision instead of silently folding it
into this fix.

### 4. A Successful Empty Job Is Not Successful Reconciliation

The nctl planner re-evaluates each automatic gap and pins at least the following
onto the action:

```text
desired_node_slug
eligible_endpoint_ids
eligibility evidence (policy, desired IP, observed IP/basis)
```

Add the following evidence to every Job summary plan row:

```text
desired_endpoint.id/name/node slug
ip_policy
normalized desired IP
normalized observed primary IP candidates
eligibility basis
action and reasons
```

Preserve the existing `nctl.ipam.reconcile.summary.v1` top-level shape
(`schema_version`, `scope`, `summary`, and `plans`) and add fields and counts in
a backward-compatible manner. If implementation requires changing the meaning
or type of an existing field, bump the schema to v2 and update nintent and nctl
within the same commit boundary.

The nctl executor verifies all of the following:

- The requested node and selected node match.
- Every eligible endpoint id pinned by the planner appears in the plan rows.
- `summary.endpoints` agrees with the plan-row count.
- Each expected endpoint reaches `create/link applied` or
  `noop/already linked`.
- A skip or conflict for an expected endpoint is not hidden by Job process
  success.

Zero coverage, a missing expected id, or an eligibility change between planning
and Job execution stops with structured `ipam_summary_coverage_mismatch` or the
specific plan conflict/skip reason. A successful JobResult alone must not make
the ActionResult successful.

If one endpoint on a node is applied and another conflicts, preserve both the
applied-row and conflict-row evidence. Compute `progress_made` from the applied
mutation count rather than Job process success, while the remaining conflict
terminates as `manual_intervention_required`.

## Implementation Steps

### Step 1 — Extract Pure Normalization and Eligibility Planning in nintent

Change `nintent/nautobot_intent_catalog/operations/ipam.py`:

- Centralize host normalization for desired and observed IPs.
- Add a pure eligibility input/result that can receive observations from a
  linked realized object.
- Implement the truth table above at the start of
  `plan_endpoint_ipam_reconcile()`.
- Add `ip_policy`, observation evidence, and eligibility basis to the plan.
- Make create fields and existing-type conflict checks policy-aware.
- Isolate DHCP/Host choice resolution into small functions testable against
  model metadata.
- Preserve existing fail-closed behavior for DNS conflicts, duplicate
  candidates, and realized-link mismatch.

Keep every branch in this step executable by Django-free unit tests.

### Step 2 — Change Job Selection and Write-time Observation Checks

Change `nintent/nautobot_intent_catalog/jobs.py`:

- Replace `filter(ip_policy="dhcp_reserved")` with a queryset that enumerates
  nonblank explicit-`ip_address` endpoints in the active scope.
- Do not guess validity in the queryset; let the pure planner produce a typed
  skip for an invalid address.
- Add a helper that safely extracts observed primary-IP candidates and
  `last_seen` from linked Device/VM custom fields.
- Pass observations into each endpoint plan and recheck eligibility immediately
  before writing.
- Preserve existing host scope, inactive exclusion, dry-run behavior, per-row
  atomic create/link, and summary-scope contracts.
- Distinguish eligible, applied, noop, skip, and conflict counts in the summary.
- Preserve the Job name and remove DHCP-only wording from its description.

No model fields change, so do not create a migration. Confirm that
`makemigrations --check --dry-run` reports no changes in the Nautobot
environment.

### Step 3 — Make nctl Eligibility and Drift Evidence Explicit

The primary files are:

- `nctl/src/nctl_core/drift/evaluation.py`
- `nctl/src/nctl_core/drift/evaluation_snapshot.py`
- `nctl/src/nctl_core/drift/comparators.py`
- `nctl/src/nctl_core/reconcile/classify.py`

Changes:

- Pass `ActualDevice.actual_facts().local_ip` as the endpoint IPAM eligibility
  self-observation. Do not read unrestricted raw inventory JSON.
- Emit the existing automatic code only for an eligible gap.
- Emit new evidence-bearing manual codes for a missing, mismatched, or ambiguous
  observation.
- Preserve endpoint identity and decision evidence when converting an endpoint
  gap into a node target.
- Keep IPAM ledger eligibility independent from DHCP readiness, MAC selection,
  and range evaluation. Do not make `static` or `external` endpoints dnsmasq
  DHCP-reservation targets.

### Step 4 — Pin Endpoint Coverage Through Planning and Execution

The primary files are:

- `nctl/src/nctl_core/reconcile/reconcilers.py`
- `nctl/src/nctl_core/reconcile/planner.py`
- `nctl/src/nctl_core/reconcile/ledger.py`
- `nctl/src/nctl_core/reconcile/executor.py`

Changes:

- Resolve eligible drifting endpoint ids for the target node from the fixed
  snapshot and pin them in action evidence and parameters.
- Extend Job artifact verification from node scope to endpoint coverage and
  count consistency.
- Do not treat an expected endpoint skip/conflict, empty plan, or missing row as
  success.
- If a partial failure contains an applied row, preserve mutation evidence and
  progress while terminating for manual intervention.
- Require fresh drift in the next round to prove that the action is not
  regenerated.

### Step 5 — Update Current Documentation

Update at least:

- `nintent/README.md`
- `nintent/README_QUICK.md`
- `nintent/README_DEV.md` with Nautobot-backed Job verification
- `nctl/README.md` reconcile/IPAM documentation if required

Document that:

- The Job handles explicit IP intent rather than DHCP-only intent.
- `dhcp_reserved` and `static`/`external` have different eligibility rules.
- Non-DHCP intent requires a matching ingested self-observation.
- IPAM ledger reconciliation is not a host IP-configuration actuator.
- A conflict, skip, or empty coverage result is not convergence.

Do not rewrite historical plans or reports.

## Automated Verification

### nintent Pure Unit Tests

Add or update at least the following cases in
`nintent/nautobot_intent_catalog/tests/test_operations_ipam.py`:

- A DHCP endpoint is create/link eligible without an observation.
- A `static` endpoint with a matching observed IP is create eligible with Host
  type.
- An `external` endpoint with a matching observed IP is create eligible with
  Host type.
- Prefix-notation differences still match by host portion.
- A missing observation produces a typed skip/manual reason.
- A mismatching observation is a conflict.
- Multiple conflicting observations are an ambiguous conflict.
- An invalid or blank desired IP is not writable.
- An existing Host type is compatible with `static`/`external`.
- An existing DHCP type conflicts with `static`/`external`.
- An existing Host type conflicts with DHCP.
- A create does not proceed if the model lacks the required Host or DHCP choice.
- Existing realized-IP mismatch, duplicate-candidate, and DNS-conflict tests
  continue to pass.
- The summary includes policy, observation, eligibility, and endpoint-coverage
  evidence.

### nctl Component Tests

Add or update:

- `test_drift_evaluation.py`: policy/observation truth table and evidence
- `test_drift_comparators.py`: endpoint identity in the node-targeted diff
- `test_reconcile_classify.py`: eligible codes are automatic and new codes are
  manual review
- `test_reconcile_planner.py`: the action pins exact eligible endpoint ids
- `test_reconcile_ledger.py`: empty, missing-id, count-mismatch, out-of-scope,
  skip/conflict, and happy-path artifact validation
- `test_reconcile_executor.py`: partial-mutation evidence and truthful terminal
  state

### Real Multi-round Test

Add one scenario that passes through the real drift engine and planner/executor,
not merely a hand-written sequence of drift results:

```text
round 0 snapshot:
  external/static endpoint has explicit 192.0.2.10
  linked Device reports primary_ip_address=192.0.2.10
  no IPAddress and no realized_ip_address link

round 0 assertions:
  missing_actual_ip_address exists
  reconcile_ipam action exists
  exact endpoint id and matching-observation evidence are pinned
  Job plan is non-empty and create/link is applied

round 1 snapshot:
  matching IPAddress exists
  endpoint.realized_ip_address points to it

round 1 assertions:
  missing_actual_ip_address is absent
  reconcile_ipam is not planned again
  operation terminates converged
```

Run observation-missing/mismatch, observation changing between drift and Job
execution, and artifact `endpoints: 0` as negative multi-round or component
cases. None may write or report false success.

### Standard Local Commands

From the repository root:

```bash
python3 -m unittest discover -s nintent/nautobot_intent_catalog/tests
uv run --project nctl pytest nctl/tests
git status --short
git -C nintent status --short
git -C nctl status --short
```

Record each command's exit code and test count, and confirm that verification
leaves no unintended worktree changes.

## Nautobot-backed and Live Verification

### 1. Pre-deployment Evidence

- Save scoped `nctl drift --host agdnsmasq --json` output.
- Confirm that the `nctl reconcile agdnsmasq` dry plan contains
  `reconcile_ipam:agdnsmasq` with the expected endpoint id.
- Record the desired endpoint policy/IP, linked realized object's
  `primary_ip_address`/`last_seen`, and absence of a matching `IPAddress` using
  read-only checks that do not expose secrets.

### 2. Deploy nintent

- Commit the nintent change.
- Ask the user to push; the agent does not push it.
- After the push, build and restart all three web, worker, and scheduler
  services from the same commit under `devenv/nautobot`. Verify the
  image/package commit so that the worker executing the Job cannot remain on an
  old image.
- Confirm
  `nautobot-server makemigrations nautobot_intent_catalog --check --dry-run`
  reports no changes.
- Confirm updated Job discovery and description.
- Run the Job in dry-run mode with `desired_node=agdnsmasq`. Its summary must
  show `endpoints: 1`, the expected endpoint id, matching observation, and a
  Host-type create/link plan. The dry run must not change the `IPAddress` or
  link.

### 3. Scoped Apply

Present the dry plan to the user and obtain explicit approval before any live
write. Only after approval, run:

```bash
uv run --project nctl nctl reconcile agdnsmasq --yes
```

Confirm positive evidence for all of the following:

- The action actually processed the expected `agdnsmasq` endpoint.
- The summary plan is non-empty and reports create/link applied or a safe
  existing-candidate link.
- The `IPAddress` host is `192.168.0.2` and its type is the Host equivalent.
- `DesiredEndpoint.realized_ip_address` and source=`derived` are saved.
- The Job artifact contains no endpoint from another node.
- Fresh drift no longer contains `missing_actual_ip_address`.
- An immediate `nctl reconcile agdnsmasq` dry plan does not contain another
  `reconcile_ipam` action.
- The dnsmasq service/content, SSH policy, and other nodes' desired/actual state
  remain unchanged.

### 4. Negative Boundaries

Do not falsify desired IPs or actual observations on the real cluster for
testing. Verify these boundaries with unit/component tests or a disposable
Nautobot fixture:

- An external/static endpoint whose observed IP does not match
- A missing observation
- Conflicting Device/VM observations
- Host/DHCP type conflict
- Duplicate `IPAddress` candidates
- A Job artifact with `endpoints: 0`
- Observation changing after drift but before the Job

Do not weaken policy, stop a real service, or manually rewrite actual custom
fields to make a test run.

## Completion Criteria

Record this initiative as `complete` only when every applicable item is
satisfied:

- [ ] The eligibility truth table is implemented and tested in both nctl and
      the Job.
- [ ] `static`/`external` never writes automatically without a matching
      self-observation.
- [ ] A non-DHCP address is never created or linked as DHCP type.
- [ ] An empty Job, skip, conflict, or coverage mismatch cannot become false
      success.
- [ ] A real planner/executor multi-round test proves action execution and
      non-repetition.
- [ ] The full nintent and nctl local suites pass.
- [ ] Nautobot migration check, Job discovery, and worker deployment are
      verified.
- [ ] The scoped dry run selects exactly one `agdnsmasq` endpoint.
- [ ] An approved scoped apply creates or links the `IPAddress`.
- [ ] Fresh scoped drift and the next dry plan prove non-repeating
      convergence.
- [ ] Operation evidence contains no secrets, raw inventory, or unnecessary
      personal information.
- [ ] The root, nintent, and nctl worktrees contain no unintended changes.

If code and local tests are complete but live deployment has not occurred,
report `implemented, not deployed`. If the dry run or live apply did not
actually process the target endpoint, report `partially complete`. Never treat
`endpoints: 0` or an unexecuted action as successful evidence.
