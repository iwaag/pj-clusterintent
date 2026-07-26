# Test Strategy Phase 3 — Step 0 Report: Frozen Baseline, Owners, and Prerequisites

Parent: [plan.md](plan.md), Step 0.

Status: **`complete`**.

## Frozen baseline

- Superproject: `05757dc72c6a064dfc95d63c6bd72766e51b75e6` on `main`.
- Submodules were clean and neither ahead nor behind their configured upstreams: `nctl`
  `4ac8b7c42b4c957b1788db68f25824a2dd982816`, `nintent`
  `2c1a8a4f0e774c7b683dd4758c6986451e571ddd`, `nauto`
  `1c78af8bdbfc69cafdc293b4082f866de9f271b0`, `nodeutils`
  `3a0fdf9817d970935847aafd46c35bf07133c20c`, and `ansible_agdev`
  `da0dffe6bc0124bfb2dbbc8125660e4740bcaaa9`.
- The only initial root change was the untracked Phase 3 plan directory supplied for this work.
  It contains no unrelated user file; this report and the plan are committed together below.
- The Phase 0 transition and external-boundary manifests were copied into the private Phase 3
  work queues. All 23 transition rows retain a current focused owner. Ten rows also require a
  bounded real-boundary proof in this phase; `desired_node_link` is the sole previously partial
  transition and Step 5 closes it. The six external rows are classified as real-boundary work for
  Steps 2–6 rather than as replacements for their focused owners.

## Prerequisites and source selection

The local scratch Nautobot web, worker, and scheduler containers, plus the documented Postgres
and Redis containers, were healthy. No database connection, container restart, service mutation,
real inventory, external host, or secret-bearing file was used.

Installed versions recorded in the private evidence include Python 3.14.2, uv 0.11.24, Docker
29.4.0 / Compose 5.0.1, OpenSSH 10.0p2, Ansible core 2.21.1, Django 5.2.14, and Nautobot 3.1.3.
Host `pytest`, `psql`, and `redis-server` commands are not installed; component-local `uv run`
and the persistent Docker services are the applicable commands/prerequisites.

The running persistent image has `nintent` commit
`e8732f17ae35d8c72d4d593e8d7311bd234fc0bf`, not the checked-out
`2c1a8a4f0e774c7b683dd4758c6986451e571ddd`. Its package provenance identifies that installed
revision, so it cannot accidentally stand in for the checkout. A throwaway container based on the
same image, with the checkout mounted read-only at `/p3/nintent` and `PYTHONPATH=/p3/nintent`,
resolved `nautobot_intent_catalog.__file__` from that mount. Thus Step 4 can select and prove the
exact local source without deploying it into the persistent scratch service.

## Focused Tier A baseline

All required existing focused owners passed before edits:

- `nctl`: ledger/executor, dnsmasq convergence and MAC safe-stop, SSH preflight, durable
  operation evidence, and compute inertness — **153 passed**.
- `nintent`: IPAM, Import, Analyze, and Braindump focused modules — **49 passed**.
- `nauto`: valid/stale/partial ingest-focused modules — **30 passed**.
- `nodeutils`: report and real helper boundary modules — **38 passed**.
- `ansible_agdev`: nodeutils helper tests — **4 passed**.

The `nctl` run includes the real multi-round dnsmasq and non-DHCP IPAM convergence tests; both
were among the named executed cases. No focused assertion gap was found in this baseline, so no
Step 1 correction is required before external-boundary work.

## Private evidence and isolation

Created `.local/test-strategy/p3/20260726T233011Z/` with mode `0700`; its evidence files have
mode `0600`. It contains revision/tool/source-resolution records, before-state fingerprints,
transition and boundary queues, protected Tier A ownership, and sanitized focused results. The
snapshot records only public container metadata and existing listener metadata; it contains no
tokens, authorization headers, key material, managed-store contents, prose, or request bodies.

The named `test_nautobot` database was intentionally not opened in this step. No fixture-owned
process, port, file, row, or environment variable was created, so no cleanup was due.

## Next step

Step 1 will pin the individual multi-round and post-mutation test IDs from this passing baseline
and inspect their positive action/evidence assertions without changing their primary ownership.
