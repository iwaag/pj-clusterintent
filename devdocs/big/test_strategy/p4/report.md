# Test Strategy Phase 4 — Final Report

Parent: [plan.md](plan.md), [roadmap.md](../roadmap.md).

Status: **`complete`**.

## Outcome

The repository now has one root-owned command matrix, a maintained exact-local-source Nautobot
runtime gate in both reusable and clean modes, a tracked sanitized behavior manifest, and a
committed measurement method. The final suite remains focused on unique risks: consolidation and
removed surfaces lowered counts where behavior disappeared, while retained real-HTTP/ORM coverage
is visible where a highest-layer proof was needed.

## Final revision tuple

| Repository | Revision | Worktree |
|---|---|---|
| superproject | `55314fbc4e97235946f7d45dff0de800023d3548` before this closure commit | clean |
| nctl | `55f1a4bad9baffc998203a5003eee1cbcc005462` | clean |
| nintent | `055496d3e28d2ea6536f660a3ae352b8594279f3` | clean |
| nauto | `6dab422a725a2e2e4e24e98079e992d1111c0ef1` | clean |
| nodeutils | `775ed7fad5110a96186a737147b87d3bf450ced2` | clean |
| ansible_agdev | `66b31c89986d1b2ecfa187a72209d8bd96838fd4` | clean |

## Commands and results

All commands in the root matrix were run exactly as documented, except the production/external
row, which intentionally has no ordinary command and requires separate explicit approval.

```text
nctl ordinary                                     967 passed
nintent Django-free ordinary                       227 run, 14 expected skips
nauto ordinary                                     110 passed
nodeutils ordinary                                  54 passed
ansible helper ordinary                              4 passed
OpenSSH conformance                                  2 passed
Ansible conformance                                  1 passed
nodeutils privileged-helper integration              1 passed
Nautobot exact-local-source --keepdb                290 collected/passed
Nautobot exact-local-source --clean                 290 collected/passed; migration check clean
measurement entry point --runtime                   passed
```

One non-matrix attempt ran nauto discovery from the nintent directory and failed before collection;
the documented nauto command was then run from its specified directory and passed. It is recorded
as a procedural deviation, not substituted evidence.

## Measurement, skips, and manifest

The reproducible after-measurement is recorded in [report5.md](report5.md). Its important deltas
are: nctl retains 901 static definitions/967 collected cases; nintent now measures 290 supported
runtime cases; nauto adds four runtime-only definitions for real ORM coverage; nodeutils preserves
its 54 static definitions; and the Ansible helper is consolidated from eight to four diagnostic
cases. The fast nintent tier has 14 explicit optional-runtime skips and there are no active xfails.

[`MANIFEST.md`](../../../../devtests/test_strategy/MANIFEST.md) has 26 current behavior rows,
including automatic transitions, explicit mutations, deterministic reads, manual safe stops, and
compute inertness. Each names a passing owner/gate and positive evidence. The compute row remains
inert until a bounded first-realization roadmap supersedes it.

## Isolation, corrections, and deviations

The runtime gate stages exact checkout sources under a generated test-owned container path and
cleans it on both modes. A bounded correction made cleanup root-capable only for that exact stage,
because Docker copy can make its contents root-owned. The clean mode recreated only
`test_nautobot`; persistent Nautobot, PostgreSQL, and Redis containers stayed healthy. OpenSSH,
Ansible, and helper fixture state was removed. No production/external mutation, scratch-stack
redeploy, compute action, public-network test call, secret read, or policy weakening occurred.

## Roadmap definition of done

| Requirement | Verdict |
|---|---|
| active tests/fixtures have a tier and contract | complete — Phase 0 ownership plus tracked current manifest |
| removed behavior has no unexplained orphan | complete — Step 2 classified searches; no unexplained orphan |
| Tier A boundaries are positively exercised | complete — ordinary, runtime, OpenSSH, Ansible, and helper gates |
| supported transitions are multi-round/no-repeat where applicable | complete — manifested owners include dnsmasq, IPAM, and node link |
| node-link real HTTP and truthful evidence | complete — maintained GraphQL/PATCH/GraphQL owner |
| mutations have authority/write/confirmation evidence | complete — manifested App and nctl owners |
| normative external tools are exercised | complete — OpenSSH, Ansible, Nautobot/Django, helper gates |
| Tier B/C depth is controlled | complete — Phase 2 dispositions, matrix admission rules, measurement |
| durable artifacts remain readable | complete — operation evidence reader manifest row |
| no silent Tier A skip, public network, leak, or secret | complete — skip audit and final cleanup audit |
| documented matrix and clean reconstruction work | complete — README_DEV matrix plus both runtime modes |
| before/after measurements are reproducible | complete — committed measurement entry point and report5 |
| omissions/substitutions are visible | complete — production/external row remains explicit approval-only; no required proof substituted |
| suite is smaller or simpler for stated reasons | complete — measurement deltas identify removed surfaces, consolidation, and added runtime proof |

`nctl_modularization` may now proceed. User-owned pushes, deployment, and any external acceptance
remain outside this phase.
