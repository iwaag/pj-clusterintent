# Test Strategy Phase 3 — Step 1 Report: Retained Multi-Round and Mutation Contracts

Parent: [plan.md](plan.md), Step 1.

Status: **`complete`**.

## Pinned primary proofs

The retained multi-round proofs are:

- `nctl/tests/test_reconcile_executor.py::test_real_multi_round_dnsmasq_content_convergence`
- `nctl/tests/test_reconcile_executor.py::test_real_multi_round_ipam_convergence_for_non_dhcp_endpoint`

Both invoke the production `run_reconcile` entry point. They replace only their real external
boundaries (Nautobot snapshot/Job, observation, or Ansible subprocess), not the drift engine,
classifier, planner, executor loop, or action-result calculation. The dnsmasq case proves stale
managed-file digest → `dnsmasq_config` deployment → exact production-route preflight → post-action
observation → fresh drift with no repeated playbook. The IPAM case proves eligible endpoint
selection and exact endpoint-ID pinning → mutation → fresh drift with no repeated IPAM action.

The following named focused cases remain the primary owner for the adjacent Tier A conditions:

- dry-plan preflight without mutation;
- post-PATCH node-link confirmation failure with retained `mutated=true` evidence;
- final-drift refresh failure after a mutation, reported as truthful unknown state;
- durable partial/corrupt event indexing;
- desired-MAC safe stop and deterministic recovery; and
- valid desired compute collections producing neither drift nor plan action.

## Verification

The pinned regression selection passed: **47 passed**. It included both multi-round tests, the
post-mutation confirmation and final-drift cases, dry-plan behavior, full planner and
desired-MAC renderer modules, durable-event corruption handling, and compute inertness.

Source review confirmed positive assertions for initial mismatch/action, actual mutation,
production preflight where required, fresh recomputation, and absent repeated action. No assertion
was moved into the planned environment harness, and no fixture refactor or focused-test correction
was needed.

## Boundary retained for later work

This does not close the known `DesiredNode` gap: its focused confirmation evidence still uses a
ledger boundary fake. Step 5 must add the required GraphQL/PATCH/GraphQL proof through actual
HTTP and preserve the focused test as its domain/evidence owner.

## Safety and cleanup

No production or external target, persistent database, local service, secret, or fixture process
was changed. Step 0's private evidence directory records the pinned IDs and result; no cleanup was
required.
