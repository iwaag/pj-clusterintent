# pj-clusterintent

An experimental system for declaring the desired state of a PC cluster and letting AI and Ansible converge the actual state toward it. This repository is a collection of submodules.

## Concept

You declare the desired state of the cluster on Nautobot through the `nintent` plugin. `ansible_agdev` playbooks then set up PCs and services to match that desired state. `nodeutils` inspects the actual state of each PC and dumps it, and the `nauto` Job ingests that dump into Nautobot. The overall concept is to reconcile Nautobot's actual state with the `nintent` desired state.

To make this reconciliation status easy for humans and AI to inspect deterministically and reproducibly instead of re-improvising the steps every time, we built a unified CLI, `nctl`, as the core backend. See [devdocs/big/core_reconcile/roadmap.md](devdocs/big/core_reconcile/roadmap.md) for the detailed design philosophy and history.

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
- [devdocs/big/core_reconcile/](devdocs/big/core_reconcile/) — nctl reconciliation roadmap and phase reports

## Reconciliation CLI

From the repository root after configuring `nctl.toml` and `NAUTOBOT_TOKEN`:

```bash
uv run --project nctl nctl status
uv run --project nctl nctl drift --json
uv run --project nctl nctl render dnsmasq
uv run --project nctl nctl render hosts-intent --out ansible_agdev/inventories/generated
uv run --project nctl nctl render production --out ansible_agdev/inventories/generated
uv run --project nctl nctl reconcile
uv run --project nctl nctl reconcile HOST --refresh-observation
uv run --project nctl nctl reconcile --yes
uv run --project nctl nctl ops list
uv run --project nctl nctl ops show OPERATION_ID
```

`nctl drift` is the structured desired-vs-actual source of truth. Bootstrap/production inventory
composition and dnsmasq rendering are also nctl responsibilities; nintent stores desired state,
Nautobot stores actual ledger state, nodeutils supplies observations, and Ansible actuates
generated artifacts.
For dnsmasq, a healthy daemon alone is not convergence: nctl also compares the SHA-256 of its
deterministic, nctl-owned records/ranges file with the digest nodeutils observed on the target.
Only `/etc/dnsmasq.d/nintent-records.conf` is content-observed in this phase; other package and
daemon settings remain separate concerns.
Current cluster convergence is a fresh `nctl drift` computation, not a persisted dashboard — run it
(with `--json` for structured agent/tool consumption) whenever status needs updating. Past or
running operations are read through `nctl ops list`/`nctl ops show OPERATION_ID` over the durable
on-disk evidence each `nctl reconcile` run writes.

**`nctl reconcile --yes` is the routine path from drift to a freshly verified converged state** —
drift, required ledger/Ansible actions, fresh nodeutils collection, verified Nautobot ingest, and a
final drift check, all as one bounded operation (`nctl reconcile HOST` first for a single node, no
argument for the whole cluster). It replaces the old
`make bootstrap-inventory && make collect-ingest && make production-inventory` sequence in
`ansible_agdev` — that Makefile's `pipeline` target now runs this command directly. Run it without
`--yes` first to get a dry plan with zero writes. AI's role is to read the plan/drift/event
artifacts under `<events.log_dir>/<operation_id>/` only when a run stops short of `converged`, not
to re-derive the workflow steps by hand each time. See [nctl/README.md](nctl/README.md) and
[devdocs/big/core_reconcile/p4/](devdocs/big/core_reconcile/p4/) for the full contract.

Use `nctl reconcile HOST --refresh-observation --yes` when a fresh nodeutils
collection is explicitly required even though current drift is converged.
Observation deploys the exact nodeutils commit pinned by this superproject,
not mutable upstream `HEAD`, and records that SHA in the operation evidence.
