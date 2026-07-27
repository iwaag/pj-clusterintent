# Test Strategy Phase 3 — Step 7 Report: Prose Authority, Desired-MAC, and Compute Inertness

Parent: [plan.md](plan.md), Step 7.

Status: **`partially complete`**.

## Retained safety boundaries verified

The exact-local-source Nautobot runtime executed the retained Braindump/Alignment Review model,
read-only UI, API, GraphQL, authorization, and no-mutation cases: **32 passed**. These are the
authorized prose-writer/reader contracts and retain the separation from desired-state models.

The focused nctl boundary selection also passed: **5 passed**. It includes the real drift registry
and planner dispatch proof that valid non-empty desired compute collections produce no compute
target, diff, reconciler, manual-review record, unsupported record, or action. It also retains the
desired-MAC mismatch blocking render with no authoritative bytes/digest, the deterministic
resolution/recovery path, and planner classification as manual review rather than automatic
actuation.

## Remaining Step 7 work

This step is not complete yet. The maintained runtime suite still needs one combined proof that a
real authorized Braindump plus Alignment Review write leaves a pre-existing desired/actual
snapshot's drift codes, plan actions, render bytes/digest, and operation-call set unchanged. The
existing focused owners prove prose authorization and the desired-MAC/compute contracts separately;
they are not a substitute for that explicit cross-authority assertion.

## Verification and isolation

```text
nautobot-server test nautobot_intent_catalog.tests.test_braindump --keepdb -v 0  32 passed
cd nctl && uv run pytest -q tests/test_compute_actuation_inert.py tests/test_dnsmasq_render.py \
  tests/test_reconcile_planner.py tests/test_reconcile_executor.py -k 'compute or desired_mac'  5 passed
```

The runtime used only exact local source copied under `/tmp/p3-*`, the named test database, and
test-created rows. No root token/configuration, real inventory, SSH/Ansible, external host,
Proxmox endpoint, or public-network service was used. The temporary copies were removed after
this checkpoint.
