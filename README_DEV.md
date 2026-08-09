# Developer Guide

Practical reference for day-to-day work across nintent, nctl, generated inventories,
Ansible/OpenSSH, nodeutils, nauto, and Nautobot: the commands you actually run, the environment
classes, and the vocabulary for reporting results. Incident-derived lessons and review-time
checklists live under [`devdocs/lessons/`](devdocs/lessons/) — read them when designing or
reviewing, not as standing constraints.

## Test strategy command matrix

Run each command from its stated working directory. Evidence is summarized in the relevant
phase report and may be retained privately under `.local/test-strategy/`; never put
credentials, raw keys, or private payloads there. Cross-component completion requires the
affected ordinary suites and all applicable required Tier A/conformance gates below.

Run Ansible ad-hoc commands and playbooks from `ansible_agdev/` (or set
`ANSIBLE_CONFIG=ansible_agdev/ansible.cfg`). Its `ansible.cfg` supplies the approved SSH key,
vault, and default inventory settings; an inventory path alone does not load that
configuration.

| gate | working directory | command | tier owned | prerequisites / expected skips | evidence and cleanup | required |
|---|---|---|---|---|---|---|
| nctl ordinary | `nctl` | `uv run pytest -q --durations=20` | A–C nctl | local uv; no expected skips | pytest output; `tmp_path` owns artifacts | yes for nctl changes |
| compute conformance | superproject root | `uv run --project nctl pytest -q devtests/test_strategy/test_compute_conformance.py` | A contract ownership | sibling `nintent` checkout; no expected skips | generated owner fixture equals committed consumer fixture | required when either compute contract changes |
| nintent Django-free fast | `nintent` | `python3 -m unittest discover -s nautobot_intent_catalog/tests` | B plus static smoke | Python; **10** expected Nautobot/file-location skips | unittest output; no persistent state | yes for nintent pure-domain changes |
| nauto ordinary | `nauto` | `python3 -m unittest discover -s tests` | A–C ingest domain | Python; no expected skips | unittest output; fakes own state | yes for nauto changes |
| nodeutils ordinary | `nodeutils` | `uv run pytest -q --durations=20` | A–C collector | local uv; no expected skips | pytest output; temporary files | yes for nodeutils changes |
| Ansible helper ordinary | `ansible_agdev` | `python3 -m unittest discover -s roles/nodeutils_pvesh_helper/tests` | helper contract | Python; no expected skips | unittest output; no external helper | yes for helper changes |
| Nautobot runtime reuse | superproject root | `./devtests/test_strategy/run_nautobot_runtime_gate.sh --keepdb` | required runtime A + App B/C | healthy local Nautobot and PostgreSQL containers; one gate run at a time; no required skips | exact-local source paths/revisions; stated `cases=` count; exact stage cleanup | required for cross-component/App changes |
| Nautobot runtime clean | superproject root | `./devtests/test_strategy/run_nautobot_runtime_gate.sh --clean` | migration/final runtime A + App B/C | same; recreates only `test_nautobot`; no required skips | migration check, fresh named DB, stated `cases=` count, stage cleanup | required for milestone/final verification |
| OpenSSH conformance | superproject root | `uv run --project nctl pytest -q devtests/test_strategy/test_openssh_conformance.py` | A SSH trust | `ssh`, `sshd`, `ssh-keygen`, `ssh-keyscan`; no skips | pytest temp keys/store/process; fixture stops exact sshd | required when SSH boundary changes |
| Ansible conformance | superproject root | `uv run --project nctl pytest -q devtests/test_strategy/test_ansible_conformance.py` | A inventory/apply scope | `ansible-inventory`, `ansible-playbook`; no skips | temp inventory/playbook/markers | required when Ansible boundary changes |
| mTLS conformance | superproject root | `uv run --project cagent pytest -q devtests/test_strategy/test_mtls_conformance.py` | A cagent TLS/ledger trust + human bearer-token entrance | local uv (cagent's `cryptography` dev dep); no skips | pytest temp CA/keys/ledger/loopback TLS server (node + human listeners); fixture stops exact servers | required when cagent's mTLS/ledger/DesiredNode-check boundary or the human token/session-visibility boundary changes |
| privileged-helper integration | `nodeutils` | `uv run pytest -q tests/test_pvesh_helper_integration.py` | A helper traversal | sibling `ansible_agdev`; no skips in this superproject | temporary fake helper/sudo/pvesh/report | required when helper/Proxmox traversal changes |
| measurement | superproject root | `./devtests/test_strategy/measure_test_strategy.py --runtime` | reproducibility audit | above local tools and runtime gate | JSON output retained privately; runtime stage cleans | required for roadmap milestones |
| production/external acceptance | explicitly approved target directory | separately approved command only | external acceptance | explicit user approval, exact target, rollback | approved evidence and cleanup plan | never ordinary; out of scope by default |

Component documents link here rather than duplicating this matrix. Test tier definitions
(A/B/C) and admission criteria for new tests are in
[`devtests/test_strategy/README.md`](devtests/test_strategy/README.md).

## Environment classes

1. **Production or external target:** physical cluster nodes, Proxmox resources, external
   services, and data not explicitly designated as disposable. Requires approval, exact scope,
   rollback, and live evidence. Ordinary tests never contact or mutate these.
2. **Persistent local scratch environment:** the local Nautobot, PostgreSQL, Redis, and
   development containers documented in `.local/localenv_memo.md`. Migrate, restart, rebuild,
   populate, or repair freely; reuse across runs.
3. **Test-owned disposable state:** named test databases, synthetic rows, temporary trust
   stores, files, and processes. Isolated by name, transaction, or fixture scope; cleaned by
   their gate.

Prefer the smallest boundary that prevents cross-test interference: focused tests while
iterating, the affected component suite next, clean/repository-wide runs only for migrations,
integration boundaries, and milestone verification.

## The system is a control loop

```text
structured desired state
  -> drift computation and planning
  -> bootstrap observation and/or ledger actions
  -> production inventory generation
  -> SSH preflight
  -> Ansible actuation
  -> nodeutils observation
  -> Nautobot ingest
  -> fresh drift computation
  -> bounded convergence decision
```

A change is complete only when the relevant path through this loop is exercised and the
expected state transition is observed — not when each component works in isolation. For
cross-component changes, walk the checklist in
[`devdocs/lessons/cross_component_dod.md`](devdocs/lessons/cross_component_dod.md) before
declaring completion.

## Current phase: coordinated breaking changes

When an authoritative model, API, configuration key, output schema, or ownership boundary
changes, update all in-scope producers and consumers to the final contract and remove the
superseded implementation in the same rollout. Do not leave compatibility-only artifacts (dual
readers/writers, shadow fields, deprecated aliases, fallback routes, old configuration keys).
If live data cannot be translated without inventing intent or losing evidence, stop and request
an operator decision.

## Dry-run policy

Dry-run is an operator-facing **plan**, not a second implementation of every operation. Keep it
only at the boundaries where a user reviews a pending desired-state write, reconciliation
action set, destructive operation, or trust-store change; a plan is read-only and reports the
target and proposed actions. The apply path is the authority for correctness. Prefer one `nctl`
plan/apply boundary over duplicated dry-run/apply branches below it; external-tool check modes
(e.g. Ansible `--check`) are optional diagnostics.

## Completion vocabulary

- **complete**: all stated exit criteria were exercised and passed;
- **partially complete**: useful work landed, but named criteria remain;
- **implemented, not deployed**: code and local tests pass, live rollout is pending;
- **blocked**: an external condition, unresolved target, irreversible risk, or required user
  decision actually prevents further safe progress (never a recoverable local
  test-environment defect — repair the scratch resource and continue); and
- **superseded**: a later report replaces an earlier completion claim.

Empty evidence is an unexercised path, not a pass. A safe stop is reported as a safe stop, not
converted into a completion claim.

## Rules of thumb

- A new nintent model (or new human-relevant field) gets a minimal read-only list/detail view
  following the existing `Desired*` pattern in the same change or a prompt follow-up — never
  API/CLI-only.
- The VM platform is intentionally Proxmox-only. Before adding another compute provider, read
  [`devdocs/vision/vm/future_provider_advice.md`](devdocs/vision/vm/future_provider_advice.md).
- Service-specific observation knowledge stays out of nodeutils orchestration — see the design
  rule in [`nodeutils/README.md`](nodeutils/README.md).

## Easier Next Time: end sessions with a self-report

Operational workflows are improved retrospectively under the Easier Next Time policy:
[`devdocs/vision/easier_next_time/policy.md`](devdocs/vision/easier_next_time/policy.md)
defines the execution-difficulty levels, the mandatory target-level record, and the
runbook-skill conventions. After a session that did non-trivial cluster work — always when
something was painful or felt like a second occurrence — create a WorkflowEpisode via
`nctl workflow-episode create` as described there. Improvement sessions themselves are the
`workflow-improvement` agentdocs session type
([`agentdocs/workflow-improvement/README.md`](agentdocs/workflow-improvement/README.md)).
Do not build or edit runbooks for the task you are currently executing; record the pain and
move on.

The cluster-agent (`cagent`) answers guidance questions and does not itself end its OpenCode
turn with this self-report — its scope is one request/response, not a session boundary. If you
are the caller that dispatched work to `cagent` (directly or indirectly) and the exchange was
non-trivial, painful, or felt like a second occurrence, check whether a `WorkflowEpisode` was
created for it and, if not, create one yourself from what you observed.

## Further reading

- [`devdocs/lessons/reconciliation_lessons.md`](devdocs/lessons/reconciliation_lessons.md) —
  incident-derived lessons (informative case studies, not standing rules), including the
  SSH/dnsmasq incident background.
- [`devdocs/lessons/cross_component_dod.md`](devdocs/lessons/cross_component_dod.md) —
  completion checklist for cross-component changes.
- [`devdocs/small/fix_sshkey4/`](devdocs/small/fix_sshkey4/) — authoritative completion
  baseline for the SSH trust design.
