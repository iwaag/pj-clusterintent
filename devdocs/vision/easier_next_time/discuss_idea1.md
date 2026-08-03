# Easier Next Time — Discussion Summary and Final Proposal

Status: design proposal following the first discussion of `idea.txt`

## 1. Summary

The Easier Next Time policy is a retrospective improvement loop for cluster
operations. The cluster-agent should first complete, safely stop, or clearly
fail the current request using the best means currently available. A separate
review later examines the work and decides whether a similar request can be
made easier, cheaper, safer, and more reliable next time.

The practical objective is not automation for its own sake. It is to reduce
the amount of reasoning, context, tool composition, and safety-policy recall
required at execution time until a small and inexpensive local model can
reliably carry out the task. This matters because a small model may
hallucinate command combinations, lose track of a multi-step sequence, or
forget a prohibition even when all the required nctl commands already exist.

The final proposal therefore retains a single four-level execution-difficulty
hierarchy. Higher levels mean that more choices and safety obligations have
been removed from the executing model and embedded in a runbook or a bounded
deterministic command. Human approval is treated separately: an operation can
remain Level 4 while requiring approval of a dry plan.

Reusable, non-secret workflow knowledge should be kept in Git. Private raw
evidence, operator inputs, secrets, runtime state, and scratch work should be
kept locally under a disciplined directory policy. Nautobot should continue
to hold cluster semantic state rather than becoming a general session-log or
runbook database.

## 2. Relationship to the existing architecture

The policy adds a learning loop outside the existing cluster control loop:

```text
current request
  -> interpret confirmed intent
  -> desired state
  -> plan and actuation
  -> fresh observation
  -> actual state and drift
  -> report or safe stop

later retrospective
  -> inspect the episode and its evidence
  -> identify model reasoning and failure points
  -> propose a simpler execution path
  -> create or improve a runbook, configuration, or deterministic command
  -> verify it with a small-model replay
  -> publish the reusable workflow
```

Cluster operation and workflow improvement should normally occur at different
times. This keeps the operational path bounded and avoids allowing an agent to
modify its own execution policy while it is operating the cluster. If
concurrent improvement is ever needed, it should use a separate experimental
cluster or disposable fixture rather than modifying the active operational
environment.

The policy also preserves the existing authority boundaries:

- Braindump records user-originated meaning and constraints.
- Confirmed nintent data records executable desired state.
- Nautobot and nodeutils record supported actual state and observations.
- nctl drift is the deterministic convergence assessment.
- nctl operation evidence records what an operation attempted and proved.
- An Easier Next Time review records what should become easier in a future
  workflow; it is not actuation authority.

An Easier Next Time review must not be stored as an Alignment Review. An
Alignment Review explains the current relation between a wish, desired state,
and actual state, has only one current value, and must not become executable
workflow input.

## 3. Execution-difficulty levels

The level describes the capability required to execute a particular version
of a workflow. It does not describe which model happened to execute one run.
A large model invoking a bounded task command is still executing a Level 4
workflow. A small model that happens to succeed at an improvised SSH repair is
still executing a Level 1 or Level 2 workflow.

### Level 1 — Collaborative exploration

The human and agent determine the approach while working.

Typical properties:

- The request or acceptance condition is still ambiguous.
- The procedure is not established.
- SSH, node-agent, diagnostic commands, and existing tools are combined ad
  hoc.
- There are open-ended branches based on intermediate findings.
- Unexpected human judgment is required during execution.
- Some success criteria may only become clear during investigation.

This level generally requires a capable model and close human collaboration.
It is acceptable for unusual diagnosis, one-off recovery, unsupported provider
work, and other tasks for which permanent automation has not yet been
justified.

### Level 2 — Agent-led orchestration

The goal and available tools are known, but the agent must compose and manage
the workflow.

Typical properties:

- The agent selects among nctl, Ansible, node-agent, or an approved SSH path.
- It decides the order of multiple commands.
- It interprets output to select the next step.
- It must remember global prohibitions and safety rules.
- It decides when an unexpected result requires a safe stop.
- The procedure is repeatable in principle but is not yet encoded as a
  bounded runbook.

This is the main danger zone for small local models. The individual commands
may all exist while the model still hallucinates their composition, skips a
verification step, broadens scope, or forgets a prohibition.

### Level 3 — Selected runbook execution

A workflow has been selected before execution, and the executor receives only
that workflow's bounded instructions and parameters.

Required properties:

- A workflow ID and version are already selected.
- Inputs are typed and validated.
- Permitted commands and tools are explicitly limited.
- Step order is fixed.
- Permitted branches are enumerated.
- Prohibitions, approval boundaries, and stop conditions appear in the
  runbook itself.
- Each checkpoint has a machine-readable success test.
- Free-form shell construction is not required.
- Retry and maximum-step bounds are explicit.

A small model should only read the selected runbook or a generated task card,
not search the entire manual collection and infer which workflow applies.

### Level 4 — Single bounded task command

The executor supplies typed arguments to one task-level interface and reports
the structured result. The command owns the multi-step safety and convergence
workflow.

A Level 4 interface must cover, as applicable:

- input validation;
- exact target-scope resolution;
- a read-only dry plan;
- explicit apply authority;
- safety and trust preflight;
- actuation;
- fresh post-actuation observation;
- a bounded convergence or safe-stop decision;
- durable operation evidence; and
- idempotence or proof that a repeated run does not repeat the mutation.

One command is not automatically Level 4. A command that invokes a
non-deterministic black box, omits observation, or leaves the model to
interpret an unstructured result does not qualify. Conversely, a Level 4
workflow may intentionally require a human to approve its dry plan before the
same plan is applied.

`nctl reconcile HOST` is the model for this level. A standalone Ansible
playbook is normally a component inside Level 4 unless it also owns the plan,
scope, observation, final decision, and evidence contract.

## 4. Approval, outcome, and level are separate

Required human authorization must not lower the execution level. For example,
a destructive Level 4 command may have the following fixed states:

```text
planned
  -> waiting_for_approval
  -> applying
  -> observing
  -> converged | safe_stop | failed
```

Waiting for approval requires no model judgment. It is different from asking a
human an unexpected question because the workflow has no rule for the current
state.

Each execution should therefore record attributes separate from the level:

- `human_guidance`: `none`, `approval_only`, or `judgment_required`;
- `execution_mode`: such as `ssh`, `node_agent`, `runbook`, `nctl`, or
  `ansible`;
- `assurance`: whether scope, plan, observation, and no-repeat proof exist;
- `outcome`: `completed`, `partially_completed`, `failed`, `interrupted`, or
  `safe_stop`.

A safe stop can be the correct successful terminal behavior of a mature
workflow. The executor must not improvise a workaround when a Level 3 or Level
4 contract returns `manual_intervention_required`.

## 5. The unit of review: a workflow episode

A cagent session is not a reliable audit unit. One session may contain several
requests and operations, while one operational task may cross session
boundaries. The retrospective should instead review a workflow episode that
correlates relevant evidence:

```text
episode_id
  |- cagent session and request IDs
  |- relevant Braindump IDs
  |- desired-state submissions
  |- nctl operation IDs
  |- node-agent request IDs
  |- approved manual SSH or console steps
  `- final outcome
```

The episode should classify the workflow version used for the task, not assign
one level to every unrelated activity in the surrounding conversation. One
user request may also contain subproblems at different levels. For example,
clarifying whether a VM should be removed may remain Level 1, while the
confirmed retirement and reconciliation path is Level 4.

## 6. Promotion between levels

### Level 1 to Level 2

Turn exploration into known operational knowledge:

- state the final goal and observable acceptance condition;
- record the successful tool choices and order;
- classify questions that required human judgment;
- identify prohibitions and risky operations;
- separate required inputs from incidental investigation context;
- preserve failed paths and safe stops as useful evidence.

The goal is not yet automation. It is to make previously implicit reasoning
visible.

### Level 2 to Level 3

Replace agent decisions with finite runbook branches:

- define typed inputs;
- list exact permitted commands;
- define accepted output schemas and codes;
- map each supported code to the next step;
- embed prohibitions in the workflow;
- identify fixed approval points;
- define `manual_intervention_required` conditions;
- define fresh observation and success evidence;
- bound retries and total steps.

For example, an SSH enrollment failure must not leave a small model to decide
whether to disable verification. The runbook should map `unenrolled` to a
specific enrollment dry plan and then stop for approval.

### Level 3 to Level 4

Move multi-step orchestration out of the model and into the task-level tool.
The implementation should absorb:

- command ordering;
- argument propagation;
- exact host and resource scope;
- preflight checks;
- structured output interpretation;
- retry bounds;
- stop conditions;
- observation and convergence checks; and
- evidence correlation.

The key improvement is not a longer model prompt. It is a CLI or equivalent
boundary that eliminates model choices.

Not every operation should be promoted. Promotion is most valuable when an
operation recurs, has a high small-model failure rate, requires many steps, or
affects destructive actions, identity, credentials, SSH trust, network
reachability, storage, multiple hosts, idempotence, or partial-progress
recovery. Rare read-only exploration may remain at Level 1 or Level 2.

A useful prioritization heuristic is:

```text
priority
  = frequency
  * failure impact
  * current reasoning burden
  * procedure length
  * observed small-model failure rate
```

## 7. Small-model execution package

Runbook selection and runbook execution should be separate responsibilities.
A human, a more capable model, or a future deterministic router selects a
workflow. The small executor receives a generated task card containing only
the selected contract.

Example:

```yaml
schema: clusterintent.task.v1
workflow_id: refresh-node-observation
workflow_version: 1
execution_level: 4

goal: Refresh the supported actual-state observation for agpc.

parameters:
  host: agpc

allowed_commands:
  - uv run --project nctl nctl reconcile agpc --refresh-observation --json
  - uv run --project nctl nctl reconcile agpc --refresh-observation --yes --json

forbidden:
  - direct ssh
  - direct ansible-playbook
  - disabling host-key verification
  - writing actual state directly

approval:
  required_before: apply

success:
  state: converged
  required_evidence:
    - observation_executed
    - ingest_verified
    - final_drift_computed

stop_when:
  - ssh_preflight_failed
  - manual_intervention_required
  - approved_plan_became_stale
```

The executor must not issue a command absent from `allowed_commands`. If no
workflow can be selected confidently, the request returns to Level 1 or Level
2 rather than asking the small model to improvise.

## 8. Workflow catalog and context selection

Reusable workflow definitions should live in Git, for example:

```text
agentdocs/workflows/
  <workflow-id>/
    workflow.yaml
    README.md
    examples/
```

The manifest should contain enough metadata to route without loading every
manual body:

```yaml
id: recover-dnsmasq-config
version: 1
execution_level: 3
summary: Diagnose and recover a managed dnsmasq content mismatch.
triggers:
  - dnsmasq_content_mismatch
  - dnsmasq_deployment_failed
excludes:
  - new_node_bootstrap
risk: production_external
entrypoint: nctl reconcile HOST
prerequisites:
  - ssh_enrollment
verification:
  - fresh_observation
  - final_drift_converged
  - no_repeated_action
last_verified: 2026-08-03
```

The routing layer first searches the small manifests. Only the selected one to
three manuals are loaded. A vector database or semantic retrieval service is
not needed for the first implementation; a validated manifest catalog and
simple exact-field search are sufficient.

## 9. Evidence and audit records

cagent already persists a request, state transitions, and terminal response or
error. That is useful but insufficient to reconstruct tool choices, approval
boundaries, model decisions, and links to nctl operation evidence.

The first implementation should add or derive a small structured episode
record rather than indiscriminately copying every prompt and tool output. It
should capture:

- decisions and why they were required;
- selected action type and exact target;
- dry-plan and approval boundaries;
- references to existing operation evidence;
- unexpected human interventions;
- missing functionality or policy gaps;
- final outcome and safe-stop reason; and
- a redaction statement.

Detailed nctl evidence should be referenced by operation ID instead of copied.
Evidence must exclude secret values, private keys, bearer tokens, raw
credentials, and unnecessary private user prose.

An initial episode layout may be:

```text
.local/evidence/workflow-episodes/
  20260803T120000Z_retire-guest/
    episode.yaml
    references/
      nctl-operations.json
      cagent-requests.json
    review.yaml
    redaction-report.yaml
```

The review is a private working artifact. When a conclusion becomes reusable,
the generalized, non-secret result is promoted into the Git-tracked workflow
catalog.

## 10. Storage authority and local directory policy

Storage should be split by responsibility rather than placing all new data in
one database or one miscellaneous local folder.

### Git-tracked repository content

Use Git for reusable, non-secret knowledge and implementations:

- workflow manifests and runbooks;
- generic task-card templates;
- prohibitions, stop conditions, and verification contracts;
- reusable Docker Compose templates without cluster-private values;
- deterministic nctl, Ansible, nodeutils, or cagent implementation;
- tests and synthetic fixtures.

### Nautobot and PostgreSQL

Continue using the database for cluster semantic state:

- Braindumps and Alignment Reviews;
- confirmed structured desired state;
- actual-state ledger records and supported observations.

Do not use it as the initial store for raw sessions, workflow manuals, audit
scratch, or development evidence. A database-backed workflow catalog should
only be reconsidered if multiple controllers need concurrent discovery,
querying, access control, or distributed updates.

### Application-owned state under `~/.local/state`

Use XDG-style application state for data that an application writes and reads
as part of its runtime contract:

```text
~/.local/state/
  nctl/events/
  cagent/evidence/
  cagent/ledger/
  cagent/runtime/
```

This includes nctl operation evidence, cagent request evidence, the cagent
authorization ledger, and application runtime databases.

### Repository-local private data under `.local`

Use the repository's `.local` for private artifacts that an operator or agent
handles in the context of this checkout:

```text
.local/
  config/
    localenv_memo.md
    services/

  inputs/
    desired-state.yaml
    retirement/
    migrations/

  secrets/
    nautobot-token
    cagent-openai-key
    ca/
    tls/

  runtime/
    tunnels/

  workspace/
    brainforge/
    audits/
    development/

  evidence/
    acceptance/
    test-strategy/
    interface-contract/
    workflow-episodes/

  backups/
    postgres/
    nautobot/
    desired-state/

  cache/
  tmp/

  archive/
    legacy-root-files/
    completed-initiatives/
```

The intended lifecycle is:

| Directory | Purpose | Manual editing | Retention |
|---|---|---:|---|
| `config/` | Long-lived non-secret local configuration | Allowed | Long |
| `inputs/` | Operator documents submitted to an authoritative system | Allowed | Until confirmed or superseded |
| `secrets/` | Tokens, credentials, and private keys | Restricted | Long, with protected backup |
| `runtime/` | Checkout-specific process state | Normally forbidden | Application-dependent |
| `workspace/` | Per-session or in-progress scratch | Allowed | Short |
| `evidence/` | Completed local audit and development evidence | Normally append-only | Policy-dependent |
| `backups/` | Recovery artifacts | Forbidden | Generational |
| `cache/` | Re-creatable data | Forbidden | Disposable |
| `tmp/` | Temporary data | Forbidden | Very short |
| `archive/` | Quarantined legacy material | Forbidden | Until reviewed |

New loose files at the `.local` root should be prohibited. The storage policy
itself should be tracked as a repository document, such as
`devdocs/local_storage_policy.md`, while `.local` remains entirely ignored to
reduce the risk of tracking secrets accidentally.

The current `.local` tree mixes operator inputs, secrets, certificates,
database dumps, cagent configuration and databases, logs, phase evidence,
temporary renders, scenarios, and miscellaneous notes. In particular, current
cagent data mixes secrets, configuration, runtime databases, logs, and test
artifacts. The proposed structure separates these by owner and lifecycle.

## 11. Migration of the existing `.local` tree

The existing tree should not be reorganized destructively in one operation.
References from configuration, scripts, and documentation must be discovered
and updated deliberately.

Recommended migration:

1. Publish the new storage policy and prohibit new root-level files.
2. Use the new layout for all newly created work.
3. Inventory every code and documentation reference to existing paths.
4. Migrate one active category at a time: configuration, secrets, runtime,
   operator inputs, and backups.
5. Update consumers and test the new path before moving the next category.
6. Move completed phase evidence into initiative-specific archive directories
   without deleting it.
7. Quarantine unowned root files under a dated
   `archive/legacy-root-files/` directory.
8. Define retention rules before deleting old logs, cache, or temporary data.

The migration must not read or print secret values merely to classify their
files. Existing evidence and backups should not be deleted as part of the
layout change.

## 12. Verifying that a workflow reached a higher level

Level assignment should be supported by replay with the intended small local
model and disposable or scratch fixtures. Useful measurements include:

- completion rate;
- attempted prohibited actions;
- false completion reports;
- missing observation or evidence;
- unnecessary human escalations;
- number of tool calls;
- number of free-form decisions;
- retries;
- input-token count;
- execution time.

Level 2 is expected to vary by model and run. Level 3 should show a high
completion rate with zero prohibited actions under the selected runbook.
Level 4 should make the model responsible only for parameter transfer,
approval handoff, and structured reporting, so model-to-model variance is
minimal.

A safety-policy violation, a mutation outside the planned scope, or a false
claim of completion prevents promotion regardless of the aggregate success
rate. Positive evidence must show that the intended action and verification
path actually ran.

## 13. Proposed first implementation phase

The first phase should remain deliberately small:

1. Adopt the Level 1 through Level 4 definitions in this document.
2. Define a minimal `workflow.yaml` schema and task-card schema.
3. Publish the `.local` storage policy and begin using the new layout for new
   artifacts.
4. Review one real operational episode using references to existing cagent and
   nctl evidence.
5. Convert that episode into one Level 3 runbook.
6. Replay it several times with the target small local model in a safe fixture.
7. Move recurrent model decisions and failure points into the runbook.
8. If the workflow is sufficiently valuable and stable, implement a bounded
   Level 4 nctl command or an equivalent task-level interface.

Do not begin with automatic self-improvement, a new database model, semantic
search, capture of every internal model event, or a general-purpose workflow
engine. First prove that one real episode can produce one reusable workflow
that materially increases small-model completion reliability.

## 14. Final proposal

Adopt Easier Next Time as a formal retrospective policy with these principles:

1. Finish or safely stop the current cluster task before improving its
   workflow.
2. Treat execution difficulty as the reasoning burden placed on the executor.
3. Progress from collaborative exploration, through agent orchestration and a
   selected runbook, to a single bounded task command.
4. Preserve explicit human approval where risk requires it; approval does not
   reduce the automation level.
5. Give small models a selected, finite task contract rather than the complete
   manual collection.
6. Encode recurrent decisions, prohibitions, scope, observation, and recovery
   boundaries in deterministic tooling whenever their risk or cost justifies
   it.
7. Use workflow episodes and evidence references for retrospective review.
8. Keep reusable workflow knowledge in Git, semantic cluster state in
   Nautobot, application state under `~/.local/state`, and private
   checkout-specific artifacts under a structured `.local` tree.
9. Promote a workflow only after replay demonstrates better completion
   reliability without weakening safety or evidence requirements.
10. Allow unusual work to remain flexible when its rarity and risk do not
    justify permanent automation.

Under this policy, Easier Next Time becomes a practical pipeline for reducing
both operational cost and model-induced failure: each valuable real-world
episode can remove more reasoning from the next execution until a cheap local
model can safely invoke a bounded, verified workflow.
