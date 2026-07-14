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
