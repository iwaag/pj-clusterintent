# Braindump Phase 3 Implementation Plan: Prove the Live Conversational Workflow

Parent: [roadmap.md](../roadmap.md) — Phase 3.

Contracts and completed handoffs:

- [Phase 0 plan](../p0/plan.md) — authoritative domain, authorship, freshness, and safety boundary;
- [Phase 1 plan](../p1/plan.md) and [live rollout report](../p1/report1.8.md) — authoritative nintent
  storage/UI/API contract; and
- [Phase 2 plan](../p2/plan.md) and [phase-close report](../p2/report2.8.md) — authoritative nctl
  commands, envelopes, live CRUD behavior, and isolation evidence.

Status: completed on 2026-07-22 (JST), with an accepted safe-stop boundary recorded in
`report3.8.md`. The read-only preflight used to prepare this plan did not create a Braindump,
change desired state, run reconcile, or actuate a host.

## Goal

Prove, through real interaction with the local cluster, that the two-row exchange diary is enough
to support a useful user/agent conversation without becoming a second intent or drift engine.

The phase must exercise all of these cases:

1. a direct, specific wish about a named host and workload;
2. a dynamic or vague placement preference that cannot honestly be reduced to a fixed host without
   more discussion; and
3. a freshly observed service that is absent from both the current Braindumps and structured desired
   state, handled first as **unexplained**, never automatically as unwanted.

At least one case must complete the entire authority-separated loop:

```text
user words -> Braindump -> AI review/question -> explicit confirmation
           -> structured desired-state write -> plan-only reconcile
           -> separate apply confirmation -> deterministic reconcile
           -> fresh observation/drift -> replacement review
```

Phase 3 is primarily live validation and documentation. It does not add an LLM runtime, prompt
framework, scheduler, background review worker, new nintent field/model, new nctl envelope, or new
actuation path. A production-code change discovered during the exercise stops the affected case and
requires a separately reviewed plan; it is not folded into this validation phase merely to make the
demo pass.

## Current state (read-only preflight on 2026-07-21)

- The parent repository is at `6e59982`; nctl is at `d33c58e`; nintent is at `aa5a052` (`0.9.0`),
  with migration `0014_braindump_exchange_diary` already deployed.
- The Phase 2 nctl suite closed with 733 passing tests and one existing warning.
- Authenticated `nctl braindump list --json` returns `count: 0`. There is no existing live diary row
  to preserve or reinterpret at phase start.
- Authenticated `nctl drift --json` returns schema `nctl.drift.v1`, six targets, summary
  `converged: 2, unknown: 4`, and two local observed dumps. This is a starting observation, not a
  frozen expected result for later live runs.
- The desired state visible in that drift contains five node targets (`agdnsmasq`, `agbach`, `aghub`,
  `agpc`, and `agstudio`) and one desired service target (`dnsmasq`). `agpc` and `agstudio` are active;
  their actual evidence is stale from 2026-06-26 and therefore cannot ground a current review as if
  it were fresh.
- The latest ingested service inventory currently names `prometheus` on `agpc` and `hatchet`,
  `nautobot`, `postgres`, and `redis` on `agstudio`, but those rows share the stale 2026-06-26
  observation. They are only candidate unexplained services until a fresh scoped collection confirms
  one still exists.
- `ansible_agdev/vars/deployment_profiles.yml` already contains supported reconciliation profiles
  for `prometheus` and several other services. This makes `prometheus` on `agpc` a plausible case for
  the confirmed desired-state loop, but the plan must not pre-decide that it is wanted, managed, or
  removable.
- A user-supplied local-only source exists under `.local/braindump_workspace/sources/`. It includes
  suitable named-host and resource-placement wishes for Cases 1 and 2. `.local` is git-ignored; raw
  private prose must not be copied into committed reports. `lan.txt` is currently empty and
  `mypc.txt` is the non-empty source.
- `nctl.toml` resolves the Nautobot token from `NAUTOBOT_TOKEN`. The shell did not have that variable
  set during the first preflight attempt. Execution must load the token from an approved local
  environment or token file without printing it, placing it in a command line, or committing it.

These facts select realistic candidates; they do not constitute user approval to write the diary,
change desired state, collect from a host, or run `reconcile --yes`.

## Decisions taken head-on

### 1. This phase validates operation; it does not add a fourth implementation layer

The live workflow uses only already supported boundaries:

| Concern | Required surface |
|---|---|
| Braindump/review reads | `nctl braindump list/show --json` over GraphQL |
| Braindump/review writes | `nctl braindump create/update/review` over REST with GraphQL confirmation |
| Direct user entry | existing Nautobot Braindump UI |
| Desired/actual comparison | `nctl drift --json` |
| Structured desired-state write | the existing nintent CRUD or strict YAML-import owner selected in preflight |
| DesiredNode lifecycle-only change | `nctl lifecycle`, only if lifecycle is the confirmed field |
| Reconcile plan/apply | `nctl reconcile SCOPE` then, after separate confirmation, `nctl reconcile SCOPE --yes` |
| Operation evidence | `nctl ops show OPERATION_ID --json` and operation artifacts |

There is no Phase 3 `nctl converse`, `review-all`, automatic evaluator, stored prompt, agent model,
review Job, signal, webhook, or polling daemon. The external agent is the conversational runtime.

### 2. Every review reads the complete relevant context, not just its paired row

Immediately before composing or replacing a review, the agent must:

1. list all Braindumps and show every document relevant to the same hosts, services, or placement
   preference;
2. read their current reviews to detect overlap or contradiction;
3. run a fresh `nctl drift --json` and inspect the desired, actual, and observation timestamps used
   by the relevant target;
4. inspect fresh service inventory only through supported read paths when the question concerns an
   observed workload; and
5. distinguish a current review timestamp from the age of its supporting actual evidence.

Cross-document contradictions are stated in each affected natural-language review. They do not
create a global review, link table, conflict code, or alignment status. `review_present` remains only
the Phase 2 diary-timestamp fact; it must not be rendered in a report as “aligned” or “fresh.”

### 3. Authorship follows provenance, not who ran the command

Case input must use these exact rules:

- prose directly entered in the Nautobot UI or supplied verbatim by the user is `user_direct`, even
  when the agent invokes nctl to transport that exact supplied text;
- prose reorganized, summarized, or written by the agent from conversation is
  `agent_transcribed`, and is written only after the user confirms that exact transcription; and
- an agent recommendation, inferred requirement, candidate host, or unconfirmed service disposition
  never enters a Braindump. It stays in the Alignment Review as a question or proposal.

When extracting a case from the local source document, show the exact proposed body and authorship
to the user first. Do not silently split, paraphrase, trim, or combine it. Use `--file` for multiline
or shell-sensitive text. The live database may hold the user's real current prose; committed reports
must record only case label, UUID, authorship, timestamps, and a non-sensitive behavior summary.

### 4. Freeze three live cases without pre-answering them

The minimum case matrix is:

| Case | User-originated input | Required demonstration | Allowed outcome |
|---|---|---|---|
| A — direct/specific | a confirmed named-host wish such as keeping Ollama and a recent Qwen model available on `agstudio` | AI-mediated write and review in the same interaction; compare against current desired/actual evidence | already satisfied, unsupported, drifting, ambiguous, or a proposed desired change |
| B — dynamic/vague | a user-entered preference about placing an LLM or container workload on the best/currently suitable machine | UI row is visibly unreviewed first; review preserves conditionality and asks for missing policy | prose-only clarification is a valid result; no forced host assignment |
| C — unexplained actual | one service confirmed by a fresh observation, absent from all Braindumps and desired services/placements | ask whether it is intentional, a project, unmanaged, or should be managed/removed | manage, leave unmanaged, investigate, or remove only after explicit confirmation |

The examples do not authorize their own contents. The execution interaction pins the actual user
words. Case C should prefer `prometheus` on `agpc` if a fresh observation still sees it and GraphQL
still proves it absent from desired state; otherwise select another freshly observed candidate and
record why the candidate changed.

### 5. The unexplained-service question is deliberately soft

The initial Case C review must not say that the service is rogue, drift, unwanted, noncompliant, or
safe to remove. It should say, in natural language:

- what was observed, on which host, and at what observation time;
- that no matching current Braindump statement or desired service/placement was found;
- that absence from those sources does not determine intent; and
- whether the user wants it documented, brought under management, left intentionally unmanaged,
  investigated further, or removed.

No stop, disable, uninstall, container deletion, desired-state retirement, or playbook run occurs
from this question alone. Removal requires explicit authority independent of the review text.

### 6. Confirmation is split into four observable gates

The phase uses separate gates so stored prose cannot masquerade as authority:

| Gate | Confirmation required | What it authorizes |
|---|---|---|
| Diary transcription | exact body/title/authorship confirmation unless the user entered it directly | write only the Braindump row |
| Structured proposal | confirmation of an exact desired-state diff and expected effect | write only those structured nintent records |
| Reconcile plan | no mutation approval; run without `--yes` | read state and persist a dry plan only |
| Reconcile apply | separate approval after the user sees scope/actions/fallbacks | run that exact scoped `reconcile --yes` operation |

Approval at one gate does not imply approval at another. A Braindump body saying “deploy this” is
context for a proposal, not the structured-write or reconcile-apply confirmation. If the user
declines or does not answer, preserve the diary/review and stop at the last authorized state.

### 7. Use the canonical desired-state owner and make the change reversible

Before proposing a structured change, inspect the matching nintent `IntentSource`,
`DesiredService`, `DesiredServicePlacement`, node lifecycle, and deployment profile. Determine who
owns the target row:

- if it is source/YAML-managed, change the exact canonical source and use the strict import path,
  first in its supported preview/dry mode;
- if it is intentionally manual, use the normal Nautobot CRUD screen/API for the smallest exact row;
  and
- use `nctl lifecycle` only for a confirmed lifecycle-only change, never as a generic approval
  mechanism.

Do not create a manual row that the next YAML import will erase, edit a generated row behind its
owner, invoke `disable_missing` across an unreviewed file, or use direct database/Django-shell
writes. The proposal records exact before/after values, affected IDs, deployment profile, scope,
expected reconcile actions, and a rollback procedure. Rollback is not executed automatically:
deleting or retiring a now-confirmed desired object is itself a destructive desired-state decision.

If Case C is confirmed as a managed `prometheus` workload and the existing profile/row ownership is
usable, it is the preferred narrow end-to-end change. If not, select another user-approved change
that already has a supported deterministic reconciliation path. Do not implement Ollama support or
invent a deployment profile inside this phase merely to force Case A to converge.

### 8. Safety-boundary evidence compares the right invariants

For a review-only replacement window, capture before and after:

- the full normalized desired projection (nodes, endpoints, services, placements, and operational
  overrides) through the existing pinned GraphQL reads;
- a fresh `nctl drift --json` envelope;
- the target review ID and `last_updated`;
- the nctl operation-event index and relevant generated inventory/artifact modification times; and
- the relevant actual observation identity/timestamp.

The review replacement must advance the same review row while the desired projection remains
identical. Compare drift schema, target identities, target statuses, and sorted diff-code sets;
ignore ordinary `generated_at`/`fetched_at` changes and time-derived evidence such as `age_hours`.
There must be no new reconcile/Ansible operation or host actuation attributable to the review.

External actual-state changes can occur during a live window. If an observation changes
independently, record it and repeat a narrow window; do not claim byte-for-byte cluster immobility or
discard inconvenient evidence.

### 9. Raw evidence stays local; committed reports prove behavior without publishing prose

Create a run-specific local evidence directory under `.local/braindump_workspace/evidence/` for raw
JSON, screenshots, proposed bodies, reviews, desired-state diffs, and operation artifacts. This
directory stays git-ignored.

Committed `report3.*.md` files may contain:

- revisions, commands, schemas, case labels, UUIDs, authorship, timestamps, counts, state
  transitions, normalized diff codes, operation IDs, and pass/fail results; and
- short paraphrases only when they do not disclose private user prose or credentials.

They must not contain API tokens, headers, full Braindump bodies/reviews, raw private source files,
secret values, host credentials, or unredacted command-line arguments containing prose. The report
may state that an exact-string comparison passed without reproducing the string.

### 10. Friction must earn structure through repeated evidence

Maintain a Phase 3 friction table with: case, task, obstruction, occurrence count, prose/ID/timestamp
workaround, outcome, and possible later change. A new structured field or runtime is considered only
when the same task fails clearly or reliably in at least two independent interactions and the
existing prose/ID/timestamp approach cannot provide a safe workaround.

Even then, Phase 3 records a follow-up proposal; it does not alter the two-model schema. Convenience,
one awkward review, desire for a score, or the fact that an agent had to reread current drift is not
enough evidence for a status, finding schema, fingerprint, object link, review history, or scheduler.

## Authority and side-effect matrix

| Action | Writer/trigger | Side effect allowed | Forbidden inference |
|---|---|---|---|
| UI Braindump create | user | one user-authored diary row | automatic review or desired write |
| nctl Braindump create/update | agent transporting direct or confirmed words | exact confirmed diary row only | recommendation becomes user intent |
| nctl review create/replace | agent | one current AI prose row | alignment/convergence status change |
| fresh drift/read | nctl | reads and local output only | stale actual becomes current |
| scoped observation/reconcile plan | established nctl operation | only the explicitly invoked plan/read effects | authority from Braindump text |
| structured desired write | user or agent after exact confirmation | named nintent records only | broader service/host approval |
| scoped reconcile apply | nctl after separate confirmation | actions shown in the reviewed scoped plan | open-ended cluster actuation |
| unexplained-service removal | established service owner after explicit removal confirmation | exact named workload only | absence means unwanted |

## Step 3.1 — Freeze the live baseline, evidence policy, and case candidates

Before any Phase 3 write:

1. record parent/nctl/nintent/ansible/nauto/nodeutils revisions and dirty-worktree state;
2. load the Nautobot credential through an approved environment or token file and verify it is not
   printed in commands, shell tracing, artifacts, or reports;
3. run `nctl braindump list --json`, `nctl drift --json`, and the relevant read-only desired/actual
   queries into the local evidence directory;
4. record the complete Braindump count, desired node/service/placement identities, actual
   observation timestamps, and event-index baseline;
5. confirm the local user source file and select provisional text for Cases A and B without writing
   it or copying it into a report;
6. record provisional unexplained-service candidates, explicitly marking stale candidates as
   unusable until refreshed; and
7. freeze the report-redaction and normalized drift-comparison procedure from Decisions 8–9.

If the deployed diary API no longer matches the Phase 2 schema or authenticated read access fails,
stop before all writes. Fix configuration or revise the coordinated contract; do not add a fallback
store or guessed endpoint.

Deliverable: `report3.1.md` with revisions, redacted baseline counts/timestamps, candidate labels,
and zero-write confirmation.

## Step 3.2 — Exercise the direct named-host case in one AI-mediated interaction

For Case A:

1. show the exact proposed title/body/authorship to the user; use `user_direct` only for verbatim
   supplied text, otherwise obtain confirmation for an `agent_transcribed` version;
2. create the Braindump with `nctl braindump create`, preferably from a UTF-8 file, and retain the
   returned UUID;
3. immediately list/show all current Braindumps, run current drift, and inspect the relevant host,
   desired service/placement, observation timestamps, and supported deployment profiles;
4. write one natural-language review in the same interaction with the four semantic elements from
   Phase 0: understood wish, current desired/actual relationship, evidence caveat, and next question
   or proposal;
5. show the pair through nctl and the Nautobot detail UI, confirming visual separation, exact
   authorship, one review row, and `review_present`; and
6. make no structured change or reconcile call unless the later Gates in Steps 3.6–3.7 are met.

The review must not pretend an Ollama/Qwen deployment is supported if the current desired catalog,
profile, or observation cannot prove it. “Not currently represented/supported; here is the next
question” is a successful alignment review.

Deliverable: `report3.2.md` with the row/review IDs, timestamps, exact-string check result,
grounding sources and ages, and confirmation that create+review happened in one interaction.

## Step 3.3 — Exercise a user-authored vague case and its visible unreviewed interval

For Case B:

1. ask the user to enter or paste their own dynamic placement preference through the existing
   Nautobot Braindump add UI with authorship `user_direct`;
2. before any agent write, call `nctl braindump list/show --json` and confirm the new row has
   `review_present: false`, `attention: unreviewed`, and no placeholder review;
3. confirm that no background worker, scheduler, signal, or hidden hook fills the review during the
   interval;
4. read Case A and every other relevant Braindump plus current drift/actual resource evidence;
5. write a review that preserves the preference's conditional nature, explains what “best” cannot
   yet decide, and asks only the missing questions demonstrated by current evidence; and
6. confirm that the same row now has exactly one current review while its user-authored body and
   authorship remain unchanged.

Do not turn a vague preference into a fixed placement, score, host ranking field, or desired service
row merely because the agent can make a plausible guess.

Deliverable: `report3.3.md` with UI-to-nctl visibility, the observed unreviewed interval, relevant
cross-document reasoning, and the final one-review state without private prose.

## Step 3.4 — Refresh evidence and conduct the unexplained-service conversation

First obtain current evidence without silently broadening authority:

1. choose one reachable active host, initially `agpc`, and run `nctl reconcile HOST` without
   `--yes` to inspect the exact bounded plan;
2. if a fresh collection/ingest requires apply mode, show the plan and request explicit permission
   for that scoped observation operation; if the plan includes unrelated actuation, stop and narrow
   or select another supported collection path rather than accepting the extra action implicitly;
3. after permission, run the exact scoped operation, inspect `nctl ops show`, and verify a new
   observation timestamp through the supported actual-state read;
4. find one currently observed service name absent from all Braindumps, desired services, and active
   placements; prefer `prometheus` on `agpc` only if it still satisfies those checks;
5. ask the soft disposition question from Decision 5 in the live conversation before creating a
   Braindump, changing desired state, or touching the service;
6. only if the user directly supplies or confirms words to preserve, create a Braindump from that
   answer and write its grounded current review; the observation alone is never user intent; and
7. record the user's disposition as conversation state in the current body/review as appropriate,
   not as an invented status field.

If no fresh unexplained service exists, do not reuse stale evidence or fabricate one. Refresh a
second reachable host, or report that the required case is not yet demonstrated and keep the phase
open.

Deliverable: `report3.4.md` with scoped observation authorization, operation ID/result, observation
time, negative desired/Braindump lookup, soft-question evidence, and the user's selected branch.

## Step 3.5 — Prove that review prose alone has zero deterministic effect

Use one existing Phase 3 Braindump and its current review:

1. capture the normalized desired projection, drift invariants, actual observation reference,
   event index, and generated artifact timestamps from Decision 8;
2. replace only that review through `nctl braindump review`; do not update its Braindump, desired
   state, or any actual-state source in the window;
3. confirm the review UUID is unchanged and `last_updated` advanced;
4. refetch every baseline and apply the normalized comparisons;
5. confirm no reconcile plan/action, Nautobot Job, nodeutils collection, Ansible process, generated
   production inventory update, or host action was triggered by the review; and
6. if unrelated cluster activity invalidates the window, record it and repeat rather than weakening
   the assertion.

This step proves only isolation. It must not claim the replacement review is correct or that the
cluster is aligned because the timestamp advanced.

Deliverable: `report3.5.md` with before/after review identity, normalized desired/drift equality,
event/artifact isolation, and any ignored time-derived drift values.

## Step 3.6 — Propose and write one confirmed structured desired-state change

Choose the narrowest live case for which the user actually wants a deterministic change. Case C's
freshly observed supported service is preferred, but user intent controls the choice.

1. inspect canonical row ownership and deployment-profile support as required by Decision 7;
2. prepare an exact proposal containing current state, proposed records/fields, host scope,
   expected drift and reconcile behavior, known risks, and rollback;
3. place the proposal in the affected Alignment Review as AI prose, without changing desired state;
4. ask the user for explicit confirmation of that exact structured diff outside the stored review;
5. after confirmation, perform only the established canonical write (strict import or normal nintent
   CRUD), never direct SQL/ORM manipulation;
6. refetch through GraphQL/REST and compare every confirmed field, relation, lifecycle, placement,
   profile, and config value;
7. run `nctl drift --json` and replace the review to explain the new **desired** commitment and any
   current drift, while making clear that no host has been reconciled yet; and
8. if the user declines, record the prose-only outcome and select another genuinely approved case;
   do not mark this step complete without one structured change.

The write is a separate authorized action. Never parse or mechanically execute a command embedded
in a Braindump/review body.

Deliverable: `report3.6.md` with the confirmation gate, canonical writer, redacted exact diff,
refetch result, pre-apply drift, rollback description, and no-actuation-yet evidence.

## Step 3.7 — Run a separate scoped reconcile, observe again, and replace the review

For the confirmed change from Step 3.6:

1. run `nctl reconcile HOST` without `--yes` and retain the plan schema, operation ID, scope,
   actions, fallbacks, and expected mutations;
2. review the plan against the approved desired diff and stop if it targets another host/service,
   contains unsupported/manual-review fallbacks that defeat the test, or has materially changed
   since the proposal;
3. present the exact bounded plan to the user and obtain a separate apply confirmation;
4. run `nctl reconcile HOST --yes` with the approved scope and normal bounded round limit;
5. inspect `nctl ops show` plus the plan, nodeutils ingest, Ansible, and final-drift artifacts; never
   diagnose a failure by improvising unrecorded manual actuation;
6. run a fresh independent `nctl drift --json` and inspect the new actual observation timestamps;
7. replace the same Alignment Review row with the current explanation—converged if proved,
   otherwise the precise remaining drift/evidence gap and next question; and
8. show that the Braindump text itself did not change and the review history still consists of one
   current row.

A failed or partially converged deterministic operation is valid learning but does not satisfy the
end-to-end exit criterion until the selected case reaches an honestly described stable outcome. Do
not manually edit drift status or the review to call it converged.

Deliverable: `report3.7.md` with both reconcile gates, operation/action results, final drift and
observation evidence, same-row review replacement, and any bounded failure/rollback decision.

## Step 3.8 — Evaluate friction, run regression checks, and close the phase

After all three cases and the structured loop:

1. compile the friction table from Decision 10 and count repeated problems across independent
   interactions;
2. explicitly decide for every candidate whether prose/IDs/timestamps were sufficient, a Phase 4
   presentation improvement is justified, or a separately planned contract change is required;
3. verify all live Braindumps have the intended current review state and there are no synthetic,
   duplicate, empty, or accidentally transcribed rows;
4. preserve genuine current diary and desired-state records; do not delete them as test cleanup;
5. clean only local temporary files that contain no needed evidence, using exact paths, and retain
   the redacted proof necessary for reports;
6. rerun `uv run --project nctl pytest -q nctl/tests` and the focused nintent tests appropriate to
   any touched canonical desired source; if no code changed, record that fact rather than inventing
   new tests;
7. review repository/submodule diffs for accidental private prose, token material, compatibility
   shims, LLM dependencies, new review automation, or unrelated desired-state edits; and
8. write the final exit-criteria result and local commit IDs. Codex does not push.

Deliverable: `report3.8.md` with the three-case matrix, structured-loop result, safety proof,
friction decisions, final record inventory, regression counts, redaction review, revisions, and each
exit criterion marked pass/fail.

## Verification summary

### Closeout decision — accepted safe-stop boundary

The original gates below were intentionally stricter than the live validation needed to prove the
minimal diary contract.  During execution, two gaps remained: a direct Nautobot UI-entry interval
was not exercised, and the final configuration action could not authenticate the production SSH
connection because host-key verification correctly stopped it.  The user accepted a Phase 3
closeout that preserves both facts as follow-up work rather than weakening SSH verification or
altering the design merely to make the apply pass.

For this accepted closeout, Phase 3 is complete when the live workflow has proven the diary,
review, explicit desired-state authority, separate plan/apply gates, fresh observation, and
review-only isolation; when the blocked configuration path has a bounded, non-bypassing handover;
and when no minimal-contract structure was added to conceal either gap.  The original UI-path and
SSH completion gates remain follow-up acceptance criteria, not claims made by this phase.  See
`memo.py` and `report3.8.md`.

The following are the original, unamended gates.  The closeout decision above
records which two are deferred and is authoritative for this completed Phase 3:

1. the direct named-host case is stored and reviewed in one AI-mediated interaction;
2. a user-created UI row is observed as genuinely unreviewed before the agent fills it;
3. the vague case remains conditional until the user supplies the missing authority/policy;
4. a freshly observed service absent from both diary and desired state receives a soft question,
   not an unwanted classification;
5. a review-only replacement advances one review row while desired state, drift invariants, event
   artifacts, and host actuation remain unaffected;
6. one exact structured desired-state change is made through its canonical established interface
   only after explicit confirmation;
7. plan-only and apply reconcile are separate, scoped, observable confirmation gates;
8. the post-reconcile review is replaced in place and grounded in fresh actual/drift evidence;
9. all bodies/summaries remain opaque prose and all cross-document contradictions remain prose;
10. raw/private evidence and tokens stay out of Git and reports; and
11. the friction log supplies concrete evidence for adding no structure, or a separately scoped
    follow-up proposal, without changing the minimal contract during this phase.

## Out of scope

- Adding fields, models, migrations, review revisions, aggregate reviews, status/score/confidence,
  JSON findings, per-object links, provenance tables, fingerprints, or persisted freshness state.
- Adding an LLM SDK/runtime, model selector, prompt template registry, tool loop, agent service,
  scheduler, worker, signal, webhook, auto-review trigger, or background poller.
- Parsing Braindump or review prose into executable desired-state payloads or command lines.
- Treating an unmentioned observed service as unwanted, drift, or approved for removal.
- Implementing a new Ollama/Qwen deployment profile solely to make the example converge.
- Adding diary data to `SourceSnapshot`, drift codes/status, reconcile planning/classification,
  dashboard health, production inventory, Ansible variables, Jobs, or nodeutils probes.
- Adding Phase 4 `nctl serve` routes, dashboard cards, voice/3D UI, stronger authorization, review
  queues, or cluster-wide prose summaries.
- Bulk importing private local source files, publishing full bodies/reviews in reports, or moving
  secrets into the diary.
- Cleaning up genuine Braindumps or confirmed desired state merely because the validation phase
  ends.
- Unscoped `nctl reconcile --yes`, manual SSH actuation outside operation artifacts, or database
  writes that bypass supported nintent interfaces.

## Exit criteria

- [ ] Three live cases cover direct/specific, dynamic/vague, and freshly observed unexplained
      service input.
- [ ] Every Braindump has correct explicit authorship; any agent transcription was confirmed before
      write, and agent recommendations remain review prose.
- [ ] The direct case was written and reviewed in the same interaction after reading all relevant
      diary, desired, actual, drift, and freshness evidence.
- [ ] A user-authored UI entry was visibly `unreviewed` with no placeholder/background review before
      the agent processed it.
- [ ] The vague case was not converted into a fixed placement or structured policy without the
      user's missing decision.
- [ ] Case C used a fresh observation, proved absence from both Braindumps and desired
      services/placements, and asked a soft disposition question before any action.
- [ ] A review-only replacement kept the review UUID, advanced its timestamp, left the normalized
      desired projection and drift invariants unchanged, and triggered no operation/actuation.
- [ ] One exact desired-state change was confirmed separately, written through its canonical
      nintent interface, and confirmed by refetch before reconcile.
- [ ] Plan-only reconcile and scoped `--yes` apply used separate user confirmations and produced
      inspectable operation artifacts.
- [ ] Fresh observation and final drift grounded an in-place replacement review that describes the
      actual result without claiming unsupported convergence.
- [ ] Genuine current rows remain, unintended/synthetic rows do not, and there is still at most one
      review per Braindump with no history mechanism.
- [ ] Friction is documented across independent cases; no schema/runtime structure was added without
      repeated evidence and a separate plan.
- [ ] Regression checks pass, diffs contain no private prose/token/compatibility artifact, and
      `report3.1.md` through `report3.8.md` provide redacted evidence for every gate.

## Suggested commit order

1. Parent repository: this Phase 3 plan only.
2. Parent repository: redacted `report3.1.md`–`report3.5.md` after the three diary cases and the
   review-isolation window pass; no raw local evidence.
3. Canonical desired-state owner, only if Step 3.6 requires a tracked source change: one narrowly
   reviewed commit containing exactly the user-approved desired diff, followed by its verified
   parent submodule pointer if applicable.
4. Parent repository: `report3.6.md`–`report3.8.md`, verified pointers, and phase-close result.

Intermediate live database state is not a substitute for a commit when the canonical owner is a
tracked source file. Conversely, do not create a repository file merely to mirror an intentionally
manual nintent row. Do not push on the user's behalf.
