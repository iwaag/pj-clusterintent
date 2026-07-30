# Minimize dry-run — Implementation Plan

## Goal

Make dry-run a small, reliable planning interface rather than a parallel
execution mode. Preserve previews where they help an operator choose whether
to write or actuate; remove lower-level simulations that duplicate the apply
path without providing a dependable prediction.

The local Nautobot environment is experimental scratch state. This work should
favor a simple, observable control loop over additional safety machinery.

## Target policy

Keep these plan/apply boundaries:

- `nctl desired apply`: preview an atomic desired-state batch, then commit with
  `--yes`.
- `nctl reconcile`: show scope, drift, and planned actions without `--yes`;
  apply and then re-observe/recompute drift with `--yes`.
- Operations that destroy a resource or change SSH trust: show the exact
  target before the explicit write.

Do not require dry-run support below those boundaries. Ansible check mode and
Nautobot Job-local `dry_run` may remain as explicitly requested diagnostics if
they are useful, but are not part of the normal reconcile contract.

## Current reduction targets

1. `nctl apply dnsmasq` currently runs SSH preflight and Ansible check/diff in
   its default dry-run path (`nctl_core/dnsmasq_apply.py`). This is an external
   execution simulation, not a pure plan.
2. `nauto` ingestion and seed Jobs expose independent `dry_run` branches even
   though normal orchestration is owned by `nctl`.
3. Tests, events, output schemas, and documentation encode the resulting
   dry-run/apply duplication.

## Implementation sequence

### Step 1 — Make `nctl` plans pure

For each retained `nctl` plan command, compute and persist the resolved scope,
inputs, drift, and actions without SSH, Ansible, Nautobot Job execution, or
other external actuation. Keep useful local validation where it clarifies an
invalid input.

`reconcile --yes` remains free to fetch fresh state and stop if the plan no
longer applies. Retain its final observation and drift verification.

### Step 2 — Simplify dnsmasq operation modes

Change the ordinary `nctl apply dnsmasq` no-`--yes` path into a render/target
plan only. The `--yes` path owns SSH preflight, setup, and deployment.

If Ansible check/diff remains valuable during development, expose it as a
clearly named diagnostic option or command. It must not be presented as proof
that a later apply will succeed. Remove dry-run-only events, error codes,
output fields, and tests that no longer describe the normal interface.

### Step 3 — Remove redundant Job-local dry-runs

Review `Ingest Nodeutils Inventory` and `Seed Home Cluster` first. For each,
either remove the Job `dry_run` input and retain normal validation/logging, or
keep it only when it has an independent UI/operator use that cannot be served
by an `nctl` plan.

Do not retain a branch solely to mirror the old behavior. Update callers,
runtime tests, and Job descriptions together.

### Step 4 — Consolidate contracts and tests

Replace paired dry-run/apply assertions with tests of:

- pure plan content and absence of actuation;
- apply's exact actuation scope;
- stale-state handling where applicable; and
- post-apply observation plus final drift result.

Update CLI help, README examples, event documentation, and envelope schemas
to call retained previews `plan` consistently. Breaking changes are acceptable
in this development phase; do not add compatibility modes solely for old
dry-run output.

## Verification and completion

Run affected component suites and the relevant conformance/runtime gates from
`README_DEV.md`. A focused local replay should demonstrate:

```text
plan has no external actuation
  -> --yes applies the planned scope
  -> observation/ingest runs when required
  -> final drift reports the actual outcome
```

The change is complete when normal operator workflows have one clear plan/apply
boundary, no longer depend on external-tool check mode, and documentation names
any remaining diagnostics as diagnostics rather than guarantees.
