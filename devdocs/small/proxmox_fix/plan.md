# Proxmox Desired-Intent Usability Fix — Implementation Plan

## Goal

Reduce avoidable failures when registering an actionable Proxmox LXC intent,
without expanding dry-run into a second model-validation engine.

An `active` or `approved` compute instance requires exactly one usable primary
endpoint. For the current LXC contract that endpoint includes an explicit MAC,
mDNS name, and a valid static or DHCP-reserved address contract.

## Current Problem

The requirement exists in the model and compute contract, but the ordinary
operator path has no complete copyable LXC batch example. A batch without a
MAC can therefore preview as three creates and then roll back during
apply-time topology validation.

The server returns the useful transaction artifact, but
`nctl desired apply --yes` currently reduces an HTTP 409 response to:

```text
error: desired-state batch failed: HTTP 409
```

This hides `compute_primary_endpoint_missing` and other validation details.

## Implementation

### 1. Add one canonical LXC batch example

Add a compact current example to the Proxmox operator documentation in
`nctl/README.md`, or a focused linked document if that reads better. Include:

- `DesiredNode` with an actionable lifecycle;
- one primary `DesiredEndpoint`;
- explicit canonical MAC and mDNS name;
- static IPv4 CIDR and same-subnet gateway;
- `DesiredComputeInstance` with platform, VMID, resources, template, storage,
  bridge, and `unprivileged`;
- preview and `--yes` commands.

State that `planned`, `deprecated`, and `retired` intent is not creation-ready
and therefore does not require the complete actionable endpoint contract.
Also state that preview reports batch actions but final Django model validation
occurs during atomic apply.

Keep one example authoritative and link to it rather than duplicating slightly
different YAML across several documents.

### 2. Preserve batch failure artifacts in the CLI

Handle `DesiredWriteError` explicitly in the `nctl desired apply` command.

- With `--json`, emit the server artifact as JSON and exit nonzero.
- Without `--json`, show the HTTP failure plus the transaction error and useful
  per-operation conflict reasons.
- Retain the current concise fallback when the response has no valid artifact.

The exact renderer and stream choice are left to the implementer, provided
machine-readable failure output remains valid JSON and command failure retains
a nonzero exit status.

### 3. Add focused contract tests

In the nintent runtime tests, build an otherwise valid active LXC batch:

- without endpoint MAC: atomic apply rolls back and reports
  `compute_primary_endpoint_missing`;
- with endpoint MAC: the node, endpoint, and compute instance commit
  atomically.

In nctl CLI tests, mock a 409 batch response and verify that:

- `--json` exposes the complete artifact;
- text mode exposes the actionable reason; and
- both modes exit with failure.

Use the real response shape returned by `DesiredStateBatchView`.

### 4. Replay the agdummy input

After deploying the nintent change if one is needed, verify the corrected
scratch input:

```bash
uv run --project nctl nctl desired apply \
  -f .local/workspace/brainforge/2026-07-30_974e/sources/agdummy-desired-state.yaml \
  --json
```

It should plan three creates with no conflict. Separately exercise a copy with
the MAC omitted and confirm that a commit failure displays the server's exact
rollback reason. Do not commit the corrected `agdummy` intent as part of this
implementation task unless it is separately approved.

## Minimal Constraints

- Do not relax the existing actionable compute endpoint contract.
- Do not add MAC-specific simulation to the generic dry-run planner.
- Do not turn a rejected batch into a successful CLI exit.

File layout, renderer structure, test organization, and commit boundaries are
otherwise left to the implementer.

## Verification

Run the focused nctl tests, nintent tests, and Nautobot runtime gate. Confirm
`git diff --check` in modified components.

Completion requires a copyable valid LXC example, preserved 409 diagnostics in
both CLI output modes, explicit MAC/no-MAC contract coverage, and no new
external or apply-time simulation in dry-run.
