# Developer Guide and Lessons Learned

This document records development rules learned from the `fix_sshkey` through
`fix_sshkey4` initiatives. It is not only a history of that incident. These
rules apply to any change that crosses nintent, nctl, generated inventories,
Ansible/OpenSSH, nodeutils, nauto, and Nautobot.

## The system is a control loop, not a collection of isolated commands

A typical reconciliation path is:

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

A change is not complete merely because each component works in isolation. It
is complete only when the relevant path through this loop is exercised and the
expected state transition is observed.

## What happened in the SSH/dnsmasq incident

The original live failure was straightforward: bootstrap connected to
`agdnsmasq.local`, while the regenerated production inventory connected to
`192.168.0.2`. OpenSSH did not know that both routes represented the same
logical node, so strict host-key verification correctly rejected the production
connection.

The first fix introduced the correct central design: route identity may change,
but trust identity is the stable DesiredNode UUID expressed through
`HostKeyAlias`. It also introduced a dedicated managed known_hosts store,
explicit verified enrollment, and strict inventory options.

That first implementation was nevertheless declared complete too early. Its
live replay did not actually plan or execute an SSH-requiring dnsmasq action.
The absence of a host-key error was treated as success even though the target
path had not run and the recorded production `ssh_preflight` was empty.

Later reviews and live attempts exposed three different classes of work:

1. **SSH contract defects:** non-default-port lookup semantics, cwd-dependent
   paths, stale generation snapshots, unsafe route fallback, incomplete
   inventory validation, and missing structured failure handling.
2. **A pre-existing convergence defect:** dnsmasq drift considered daemon state
   but not the contents of the nctl-managed records file. A desired DNS change
   could therefore remain undeployed while the service appeared converged.
3. **Hardening and proof gaps:** malformed store lines could be hidden, a
   post-mutation error could lose round evidence, the deployment destination and
   host scope had multiple owners, project metadata was not reproducible, and a
   required multi-round end-to-end test had been substituted with narrower
   tests.

The numbered `fix_sshkey*` directories therefore do not represent four rewrites
of one SSH bug. They represent one root SSH correction, missed boundary
conditions, a separate convergence capability needed to prove the correction,
and a final correctness/verification audit. Even so, much of the repetition
could have been avoided by applying the completion rules below from the start.

Historical details are preserved in:

- [`devdocs/small/fix_sshkey/`](devdocs/small/fix_sshkey/)
- [`devdocs/small/fix_sshkey2/`](devdocs/small/fix_sshkey2/)
- [`devdocs/small/fix_sshkey3/`](devdocs/small/fix_sshkey3/)
- [`devdocs/small/fix_sshkey4/`](devdocs/small/fix_sshkey4/)

`fix_sshkey4` is the authoritative completion baseline. Earlier reports remain
useful historical evidence but must not be read as the final contract where a
later report explicitly supersedes them.

## Core lessons

### 1. No error is not proof that the target path ran

An acceptance check must assert positive evidence for the intended behavior.
For an SSH-gated service change, this includes at least:

- the expected drift code was present;
- the expected action was planned;
- the expected action was executed;
- SSH preflight was non-empty and named the expected host;
- the production generation, route, port, and trust alias were recorded;
- Ansible ran against exactly the planned host set;
- the target was observed after actuation; and
- the next drift computation showed convergence without repeating the action.

If an action was not planned, the test did not exercise that action. A green
command exit, an unchanged host, or the absence of an SSH error does not change
that fact.

### 2. Tests can preserve a wrong shared assumption

The original implementation and its tests agreed on an incorrect non-default-
port known_hosts representation. Tests proved consistency with the assumption,
not correctness against OpenSSH.

For externally defined behavior, verify the assumption against the normative
implementation or documentation and add at least one test using the real tool.
This is especially important for OpenSSH option precedence, Ansible variable
precedence and templating, inventory parsing, filesystem path resolution, and
Nautobot API/Job behavior.

### 3. A generated artifact and its validation must share one generation

Never generate an inventory from one snapshot and validate a route, port, node
identity, or policy from an older snapshot. The render result should carry an
explicit generation context, and downstream preflight must consume targets
resolved from the artifact that was actually installed.

Missing membership in the installed generation is an error. Do not silently
fall back to a bootstrap route or another convenient source.

### 4. Every operational value needs one owner

Values such as the dnsmasq destination path, SSH alias, managed known_hosts
path, and scoped host set must be resolved once and passed explicitly through
all consumers. Duplicated literals and independently reconstructed host lists
will eventually diverge.

In particular, a host-scoped reconcile must use the same exact host set for:

```text
planning -> SSH scan -> inventory validation -> Ansible --limit
         -> action result -> post-actuation observation
```

Direct administrative commands may intentionally target a whole inventory
group, but that broader behavior must be explicit and separate from a scoped
reconcile action.

### 5. Convergence must measure the state that the action changes

Process health is not configuration convergence. If an action deploys a managed
file, drift must compare deterministic desired bytes or a digest with an
observation of that exact deployed path. A running daemon with stale content is
still drifting.

Desired artifacts must also be deterministic. Volatile timestamps, operation
IDs, or ordering must not change their bytes when the semantic inputs are
unchanged.

### 6. Fail closed, but also fail truthfully

Security-sensitive input must not be silently ignored. A missing managed SSH
store is different from a corrupt or unreadable store, and both are different
from an unenrolled host, an unreachable route, and a mismatched offered key.
Each condition needs a structured error with the correct remediation.

Fail-closed behavior alone is not sufficient if it misreports corruption as a
normal enrollment problem or lets an exception escape the public operation
boundary.

### 7. Preserve evidence after side effects

Once a round starts, and especially once a mutation succeeds, later failures
must not erase the round, completed actions, preflight results, generation
identity, or progress flag. Refresh final drift when possible; if that refresh
also fails, report that failure without rewriting history as though no action
occurred.

Operation evidence must contain public fingerprints and identifiers, not raw
key blobs, private keys, credentials, or managed file contents.

### 8. Use layered tests, including one real control-loop test

Unit and component tests remain valuable, but every cross-component feature
needs at least one test that follows the real planner and executor through the
state transition it claims to support.

For content reconciliation, the minimum automated scenario is:

```text
content mismatch
  -> real drift classification and planning
  -> deployment action
  -> simulated observation/ingest of the deployed digest
  -> fresh drift
  -> matching digest
  -> no repeated deployment action
```

Add focused variants for malformed state, missing evidence, stale or wrong path
identity, multiple hosts, scoped execution, and post-actuation failure. Not
every variant must reproduce an entire live cluster, but every contract must be
covered at the highest practical layer.

### 9. Completion language is part of correctness

Do not mark a plan or report complete when a required acceptance check was
omitted, substituted, or never triggered. Use precise states:

- **complete**: all stated exit criteria were exercised and passed;
- **partially complete**: useful work landed, but named criteria remain;
- **implemented, not deployed**: code and local tests pass, live rollout is
  pending;
- **blocked**: a named external condition prevents the required proof; and
- **superseded**: a later report replaces an earlier completion claim.

When a safe live fixture cannot be created, record the limitation and stop. Do
not reinterpret narrower unit tests as the live proof that the plan required.

### 10. Live safety boundaries are intentional

Do not weaken strict SSH verification, stop a real service, fabricate actual
state, or broaden a desired-state mutation merely to make an acceptance test
run. Use disposable OpenSSH fixtures and reversible desired-state changes.
Require explicit approval before live mutations, and record cleanup separately
from the successful forward path.

A safe stop can be the correct result. It should be described as a safe stop,
not converted into a completion claim.

## Required definition of done for cross-component changes

Before declaring a reconciliation, inventory, SSH, observation, or actuation
change complete, verify and record all applicable items below.

### Contract and ownership

- [ ] The desired state transition and observable acceptance target are stated.
- [ ] Every route, identity, path, generation, and host-set value has one owner.
- [ ] External-tool assumptions were checked against normative behavior.
- [ ] Security policy cannot be overridden through an adjacent variable or
      arbitrary inventory field.

### Automated verification

- [ ] Focused unit and error-path tests pass.
- [ ] A real planner/executor multi-round test proves the intended transition.
- [ ] The test asserts that the intended action and preflight actually ran.
- [ ] Non-default ports, relative/canonical paths, malformed input, stale
      snapshots, multi-host scope, and post-mutation failures were considered.
- [ ] Repository-standard commands are reproducible from their documented
      working directories and leave every worktree clean.

### Live or environment-backed verification

- [ ] The initial state and reversible fixture are recorded.
- [ ] The dry plan names the exact expected action and target set.
- [ ] Apply uses the same generation and exact target set.
- [ ] Post-actuation observation records the exact state the action changed.
- [ ] Fresh drift proves convergence and no repeated action.
- [ ] Negative boundaries use disposable state and do not weaken policy.
- [ ] Cleanup restores the original desired, actual, service, trust-store, and
      repository state as applicable.

### Reporting

- [ ] Results distinguish the feature under test from unrelated cluster drift.
- [ ] Empty evidence is treated as an unexercised path, not a pass.
- [ ] Every omitted or substituted check is visible and prevents an unqualified
      `complete` status.
- [ ] Reports contain no tokens, credentials, raw SSH key blobs, or private
      user prose.

## Final principle

The strongest completion evidence is not the number of passing tests. It is a
traceable statement that the intended action was planned, securely authorized,
executed against the exact scope, observed through the supported path, and
shown by fresh drift not to require repetition.
