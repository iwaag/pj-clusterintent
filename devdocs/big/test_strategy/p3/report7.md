# Test Strategy Phase 3 — Step 7 Report: Prose Authority, Desired-MAC, and Compute Inertness

Parent: [plan.md](plan.md), Step 7.

Status: **`complete`**.

## Retained safety boundaries verified

The exact-local-source Nautobot runtime executed the retained Braindump/Alignment Review model,
read-only UI, API, GraphQL, authorization, and no-mutation cases: **32 passed**. These are the
authorized prose-writer/reader contracts and retain the separation from desired-state models.

The focused nctl boundary selection also passed: **5 passed**. It includes the real drift registry
and planner dispatch proof that valid non-empty desired compute collections produce no compute
target, diff, reconciler, manual-review record, unsupported record, or action. It also retains the
desired-MAC mismatch blocking render with no authoritative bytes/digest, the deterministic
resolution/recovery path, and planner classification as manual review rather than automatic
actuation. A maintained real-HTTP cross-authority case now creates a Braindump and Alignment
Review through nctl's authorized writers using only a test token, then recomputes the same real
desired/actual GraphQL snapshot, drift, and plan. The drift-code set and complete planned-action
records are unchanged; prose never becomes an input to desired-state reconciliation.

## Verification and isolation

```text
nautobot-server test nautobot_intent_catalog.tests.test_braindump --keepdb -v 0  32 passed
nautobot-server test nautobot_intent_catalog.tests.test_p3_node_link_http.DesiredNodeLinkRealHttpTests.test_authorized_prose_writes_do_not_change_real_drift_or_plan --keepdb -v 1  1 passed
cd nctl && uv run pytest -q tests/test_compute_actuation_inert.py tests/test_dnsmasq_render.py \
  tests/test_reconcile_planner.py tests/test_reconcile_executor.py -k 'compute or desired_mac'  5 passed
```

The runtime used only exact local source copied under `/tmp/p3-*`, the named test database, and
test-created rows. No root token/configuration, real inventory, SSH/Ansible, external host,
Proxmox endpoint, or public-network service was used. The temporary copies were removed after
this checkpoint.
