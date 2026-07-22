# pj-clusterintent

An experimental system for declaring the desired state of a PC cluster and letting AI and Ansible converge the actual state toward it. This repository is a collection of submodules.

## Concept

You declare the desired state of the cluster on Nautobot through the `nintent` plugin. `ansible_agdev` playbooks then set up PCs and services to match that desired state. `nodeutils` inspects the actual state of each PC and dumps it, and the `nauto` Job ingests that dump into Nautobot. The overall concept is to reconcile Nautobot's actual state with the `nintent` desired state.

To make this reconciliation status easy for humans to understand, and to let AI run these workflows deterministically and reproducibly instead of re-improvising the steps every time, we are building a unified CLI, `nctl`, as the core backend. See [devdocs/vision/core_reconcile/roadmap.md](devdocs/vision/core_reconcile/roadmap.md) for the detailed design philosophy and future vision.

## Submodules

| submodule | role |
|---|---|
| [nintent](https://github.com/iwaag/nintent) | Nautobot plugin that manages the desired state of PCs and services to be deployed |
| [nauto](https://github.com/iwaag/nauto) | Nautobot server definition; provides Jobs as a Nautobot Git Repository |
| [nodeutils](https://github.com/iwaag/nodeutils) | Scripts that inspect the actual state on each PC (OS, CPU, memory, Docker, etc.) and dump it locally |
| [ansible_agdev](https://github.com/iwaag/ansible_agdev) | Ansible playbooks that set up PCs and services according to the desired state |
| [nctl](https://github.com/iwaag/nctl) | CLI that ties the above four together, computing desired/actual drift (reconcile) and running standard workflows |

## Setup

```bash
git clone --recurse-submodules https://github.com/iwaag/pj-clusterintent.git
```

If already cloned:

```bash
git submodule update --init --recursive
```

## Developer Docs

- [devdocs/functions/](devdocs/functions/) — Design exploration logs for individual features
- [devdocs/vision/core_reconcile/](devdocs/vision/core_reconcile/) — nctl reconciliation roadmap and phase reports

## Reconciliation CLI

From the repository root after configuring `nctl.toml` and `NAUTOBOT_TOKEN`:

```bash
uv run --project nctl nctl status
uv run --project nctl nctl drift --json
uv run --project nctl nctl render dnsmasq
uv run --project nctl nctl render hosts-intent --out ansible_agdev/inventories/generated
uv run --project nctl nctl render production --out ansible_agdev/inventories/generated
uv run --project nctl nctl dashboard
uv run --project nctl nctl reconcile
uv run --project nctl nctl reconcile --yes
uv run --project nctl --extra serve nctl serve
```

`nctl drift` is the structured desired-vs-actual source of truth. Bootstrap/production inventory
composition and dnsmasq rendering are also nctl responsibilities; nintent stores desired state,
Nautobot stores actual ledger state, nodeutils supplies observations, and Ansible actuates
generated artifacts.
For dnsmasq, a healthy daemon alone is not convergence: nctl also compares the SHA-256 of its
deterministic, nctl-owned records/ranges file with the digest nodeutils observed on the target.
Only `/etc/dnsmasq.d/nintent-records.conf` is content-observed in this phase; other package and
daemon settings remain separate concerns.
`nctl dashboard` is the routine command for humans: it regenerates a self-contained static HTML
dashboard (green/yellow/red/gray tiles, one per node/service, with drift details in prose on
click) from a fresh `nctl drift` run and pushes each target's status back into nintent as a
derived cache. Run `nctl dashboard`, not `nctl drift`, whenever the page itself needs updating.

**`nctl reconcile --yes` is the routine path from drift to a freshly verified converged state** —
drift, required ledger/Ansible actions, fresh nodeutils collection, verified Nautobot ingest, and a
final drift check, all as one bounded operation (`nctl reconcile HOST` first for a single node, no
argument for the whole cluster). It replaces the old
`make bootstrap-inventory && make collect-ingest && make production-inventory` sequence in
`ansible_agdev` — that Makefile's `pipeline` target now runs this command directly. Run it without
`--yes` first to get a dry plan with zero writes. AI's role is to read the plan/drift/event
artifacts under `<events.log_dir>/<operation_id>/` only when a run stops short of `converged`, not
to re-derive the workflow steps by hand each time. See [nctl/README.md](nctl/README.md) and
[devdocs/vision/core_reconcile/p4/](devdocs/vision/core_reconcile/p4/) for the full contract.

**`nctl serve`** exposes the same `nctl_core` functions over HTTP + WebSocket (single bearer
token, LAN-only) so external processes — a future 3D/voice UI, scripts, AI tooling — can read
state and trigger operations as "just another subscriber," without any backend changes and without
going through the CLI. The CLI remains the primary, no-server way to drive the system day to day;
`serve` is groundwork for realtime UIs that need to watch operations progress live rather than poll
a terminal. See [nctl/README.md](nctl/README.md#serve-realtime-api) and
[devdocs/vision/core_reconcile/p5/](devdocs/vision/core_reconcile/p5/) for the full contract.
