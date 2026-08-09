# Reconciliation Lessons Learned

**Status: informative, not normative.** This is a case-study collection distilled from past
incidents (primarily `fix_sshkey` through `fix_sshkey4`), not a rulebook. It exists to inform
review and design judgment, not to constrain it. When a lesson here conflicts with a current,
deliberate design decision, the current decision wins — record the divergence and move on.
The normative day-to-day material (command matrix, environment classes, completion vocabulary)
lives in [`README_DEV.md`](../../README_DEV.md); the completion checklist lives in
[`cross_component_dod.md`](cross_component_dod.md).

## Incident background: SSH/dnsmasq

The original live failure: bootstrap connected to `agdnsmasq.local`, while the regenerated
production inventory connected to `192.168.0.2`. OpenSSH did not know both routes represented
the same logical node, so strict host-key verification correctly rejected the production
connection.

The first fix introduced the correct central design — route identity may change, but trust
identity is the stable DesiredNode UUID expressed through `HostKeyAlias` — plus a dedicated
managed known_hosts store, explicit verified enrollment, and strict inventory options. That
implementation was nevertheless declared complete too early: its live replay never actually
planned or executed an SSH-requiring dnsmasq action. The absence of a host-key error was
treated as success even though the target path had not run and the recorded production
`ssh_preflight` was empty.

Later reviews exposed three classes of work: SSH contract defects (non-default-port lookup
semantics, cwd-dependent paths, stale generation snapshots, unsafe route fallback, incomplete
inventory validation, missing structured failure handling); a pre-existing convergence defect
(dnsmasq drift considered daemon state but not the nctl-managed records file, so a desired DNS
change could remain undeployed while the service appeared converged); and hardening/proof gaps
(hidden malformed store lines, evidence lost on post-mutation errors, multiple owners for the
deployment destination and host scope, non-reproducible project metadata, a required
multi-round end-to-end test substituted with narrower tests).

The numbered `fix_sshkey*` directories are therefore not four rewrites of one SSH bug: one root
correction, missed boundary conditions, a separate convergence capability needed to prove the
correction, and a final correctness/verification audit. Historical details:

- [`devdocs/small/fix_sshkey/`](../small/fix_sshkey/)
- [`devdocs/small/fix_sshkey2/`](../small/fix_sshkey2/)
- [`devdocs/small/fix_sshkey3/`](../small/fix_sshkey3/)
- [`devdocs/small/fix_sshkey4/`](../small/fix_sshkey4/)

`fix_sshkey4` is the authoritative completion baseline. Earlier reports remain useful
historical evidence but must not be read as the final contract where a later report explicitly
supersedes them.

## Core lessons

### 1. No error is not proof that the target path ran

An acceptance check must assert positive evidence for the intended behavior. For an SSH-gated
service change, this includes at least:

- the expected drift code was present;
- the expected action was planned;
- the expected action was executed;
- SSH preflight was non-empty and named the expected host;
- the production generation, route, port, and trust alias were recorded;
- Ansible ran against exactly the planned host set;
- the target was observed after actuation; and
- the next drift computation showed convergence without repeating the action.

If an action was not planned, the test did not exercise that action. A green command exit, an
unchanged host, or the absence of an SSH error does not change that fact.

The same rule applies to a gate itself. A test label that resolves to nothing makes Django exit
`0` after running zero cases, so a gate wrapper must state and check its collected case count
rather than forward that exit status. A gate that cannot name how many cases it ran has proved
nothing.

A shared test database is also part of the gate's contract. When a run is interrupted or fails
during database setup, the wrapper must drop the test-owned database instead of preserving it,
because a half-built schema makes every later reuse run stop on an already-existing column — at
a different column each time, which reads like a migration defect rather than abandoned setup
state.

### 2. Tests can preserve a wrong shared assumption

The original implementation and its tests agreed on an incorrect non-default-port known_hosts
representation. Tests proved consistency with the assumption, not correctness against OpenSSH.

For externally defined behavior, verify the assumption against the normative implementation or
documentation and add at least one test using the real tool. This is especially important for
OpenSSH option precedence, Ansible variable precedence and templating, inventory parsing,
filesystem path resolution, and Nautobot API/Job behavior.

### 3. A generated artifact and its validation must share one generation

Never generate an inventory from one snapshot and validate a route, port, node identity, or
policy from an older snapshot. The render result should carry an explicit generation context,
and downstream preflight must consume targets resolved from the artifact that was actually
installed.

Missing membership in the installed generation is an error. Do not silently fall back to a
bootstrap route or another convenient source.

### 4. Every operational value needs one owner

Values such as the dnsmasq destination path, SSH alias, managed known_hosts path, and scoped
host set must be resolved once and passed explicitly through all consumers. Duplicated literals
and independently reconstructed host lists will eventually diverge.

In particular, a host-scoped reconcile must use the same exact host set for:

```text
planning -> SSH scan -> inventory validation -> Ansible --limit
         -> action result -> post-actuation observation
```

Direct administrative commands may intentionally target a whole inventory group, but that
broader behavior must be explicit and separate from a scoped reconcile action.

### 5. Convergence must measure the state that the action changes

Process health is not configuration convergence. If an action deploys a managed file, drift
must compare deterministic desired bytes or a digest with an observation of that exact deployed
path. A running daemon with stale content is still drifting.

Desired artifacts must also be deterministic. Volatile timestamps, operation IDs, or ordering
must not change their bytes when the semantic inputs are unchanged.

### 6. Fail closed, but also fail truthfully

Security-sensitive input must not be silently ignored. A missing managed SSH store is different
from a corrupt or unreadable store, and both are different from an unenrolled host, an
unreachable route, and a mismatched offered key. Each condition needs a structured error with
the correct remediation.

Fail-closed behavior alone is not sufficient if it misreports corruption as a normal enrollment
problem or lets an exception escape the public operation boundary.

### 7. Preserve evidence after side effects

Once a round starts, and especially once a mutation succeeds, later failures must not erase the
round, completed actions, preflight results, generation identity, or progress flag. Refresh
final drift when possible; if that refresh also fails, report that failure without rewriting
history as though no action occurred.

Operation evidence must contain public fingerprints and identifiers, not raw key blobs, private
keys, credentials, or managed file contents.

### 8. Use layered tests, including one real control-loop test

Unit and component tests remain valuable, but every cross-component feature needs at least one
test that follows the real planner and executor through the state transition it claims to
support.

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

Add focused variants for malformed state, missing evidence, stale or wrong path identity,
multiple hosts, scoped execution, and post-actuation failure. Not every variant must reproduce
an entire live cluster, but every contract must be covered at the highest practical layer.

### 9. Completion language is part of correctness

Do not mark a plan or report complete when a required acceptance check was omitted,
substituted, or never triggered. Use the precise states defined in
[`README_DEV.md`](../../README_DEV.md) (complete / partially complete / implemented, not
deployed / blocked / superseded).

Do not use `blocked` for a recoverable local test-environment defect, stale fixture, cleanup
failure with an exact target, or procedural deviation that can be recorded and corrected.
Repair or recreate only the affected scratch resource and continue. When a safe
production/cluster fixture cannot be created, record the limitation and stop. Do not
reinterpret narrower unit tests as the live proof that the plan required.

### 10. Classify the environment before applying safety rules

Use the three environment classes defined in `README_DEV.md` (production/external, persistent
local scratch, test-owned disposable). Keep approval, exact scope, rollback, and live-evidence
requirements for the first class only; repair scratch environments without treating ordinary
breakage as a live incident; isolate disposable state by name, transaction, or fixture scope.

Isolation does not mean rebuilding an entire environment for every command. Prefer the smallest
boundary that prevents cross-test interference. During iteration run focused tests, then the
affected component suite. Reserve clean environment and repository-wide runs for migration
changes, integration boundaries, and milestone/final verification.

### 11. Live safety boundaries are intentional

Do not weaken strict SSH verification, stop a real service, fabricate actual state, or broaden
a desired-state mutation merely to make an acceptance test run. Use disposable OpenSSH fixtures
and reversible desired-state changes. Require explicit approval before production/external
mutations, and record cleanup separately from the successful forward path. Local scratch
mutations do not require the same approval unless they can reach those external targets.

A safe stop can be the correct result. It should be described as a safe stop, not converted
into a completion claim.

## Case: models without a human-readable view

`DesiredWorkspace` went live as API/CLI-only with no way for a human to casually inspect it in
the Nautobot UI, and the gap went unnoticed for multiple phases. Hence the standing rule in
`README_DEV.md`: a new nintent model (or a new human-relevant field) gets a minimal read-only
list/detail view following the existing `Desired*` pattern in the same change or a prompt
follow-up.

## Final principle

The strongest completion evidence is not the number of passing tests. It is a traceable
statement that the intended action was planned, securely authorized, executed against the exact
scope, observed through the supported path, and shown by fresh drift not to require repetition.
