# workflow-improvement — agent manual

**workflow-improvement** = the process where you (the AI agent) take one `WorkflowEpisode` a
human has already selected for improvement, read its `report`/`assessment`/`references` from the
database, and improve policy / agentdocs / a `.claude/skills/` runbook / nctl / a submodule so the
same pain does not recur — recording what you changed back into the episode's `resolution`, then
transitioning it to `resolved` (or `dismissed` if no improvement is warranted).

This is the second `agentdocs/` session type, alongside `brainforge`. It is a **separate session**
from the cluster-operation work the episode is about — see "Time separation" below.

## Rule

- read [`../../devdocs/vision/easier_next_time/policy.md`](../../devdocs/vision/easier_next_time/policy.md)
  §1–§3 for the level vocabulary (this manual does not repeat it) and §5–§6 for skill/runbook
  conventions.
- Before improving anything, show the user your plan (which document/skill/nctl surface you intend
  to change and why) before actually making the change — same standing rule as brainforge.

## Time separation (policy §7)

Cluster operation and workflow improvement happen in different sessions. Do not create or edit a
runbook, policy paragraph, or agentdocs manual for the task you are *currently* executing in this
same session — that belongs to a later, separate `workflow-improvement` session working from a
`WorkflowEpisode` someone selected. If mid-task you notice something painful, that observation
becomes the episode's `report` (via `nctl workflow-episode create` at the end of that other
session), not an edit here.

## The three things you're allowed to touch, and how

| Thing | You may... | You may NOT |
|---|---|---|
| The episode's `report` namespace | read it | edit it — it is the original evidence; the per-namespace write API exists precisely so improvement work never touches it |
| The episode's `assessment`/`resolution`/`references` namespaces | write/replace them to record your findings and the outcome | fabricate a verdict or resolution the work doesn't support |
| Policy / agentdocs / `.claude/skills/` / nctl / submodules | improve them, with matching tests | write desired or actual cluster state directly — an improvement decision does not become a cluster mutation on its own; if a real change is warranted, that goes through the normal nintent/nctl path in its own reviewed step, same as any other change |

## Prohibitions (all inherited from policy.md, not new)

1. Do not edit the episode's `report` namespace.
2. Do not let an improvement decision write desired or actual state directly (see table above).
3. Do not improve a runbook for a task you are currently executing (time separation, above) —
   that belongs to a different `workflow-improvement` session.
4. Skill edits follow policy.md §5–§6 conventions: refresh `last_verified` on real successful use,
   delete a Level-3 skill's body (leaving only a pointer) once its workflow is absorbed into an
   nctl command, and never keep two runbooks for one workflow.
5. No secrets in Git or in any namespace you write (policy §8.1); `references` hold stable IDs
   (nctl operation IDs, Braindump/desired-state IDs, session identifiers), not local paths (policy
   §8.2) — the three existing `.local/evidence/workflow-episodes/` directories from before this
   scheme may be deleted at any time, so never make an instruction depend on one of those paths
   resolving. Do not copy transcript or `nctl ops` evidence bodies into `raw_data`; reference the
   operation ID or transcript location instead.

## Workspace scratch area

`.local/workspace/<task_name>/<slug>/` is your scratch space, not the source of truth — same
convention as brainforge. Start of session: `nctl session new workflow-improvement --topic
<short-slug>` (e.g. the episode's short title or its own ID) creates your session folder. Files
here are never read back automatically; if it's not written back into the episode's `raw_data` via
`nctl`, it doesn't count as recorded.

## Standard loop for one turn

1. The human has already surveyed the GUI and run `nctl workflow-episode select <id>` (or asks you
   to, if the episode is still `candidate`) — this manual starts from a `selected` episode with a
   known ID.
2. `nctl session new workflow-improvement --topic <short-slug>` — scratch space for this session.
3. `nctl workflow-episode show <id> --json` — fetch `report` / `assessment` / `references` /
   `resolution` from nothing but the ID. This is the agent's fetch contract; there is no separate
   file to look up.
4. Only if the `report`/`references` alone are not enough to understand what happened, follow a
   `references` entry to the named session transcript or `nctl ops show <operation-id>` evidence.
   Do not go looking for evidence the episode doesn't point you at.
5. Decide: does this warrant an improvement, or not?
   - **If yes**: improve policy / agentdocs / a skill / nctl / a submodule, with the matching
     tests and acceptance evidence for whatever you touched. Record what you changed — commit
     SHAs, skill names, a short summary — via
     `nctl workflow-episode write <id> resolution --data '{"summary": "...", "skill": "...",
     "commits": ["..."]}'` (free-form JSON; this is a convention, not a schema). Then
     `nctl workflow-episode resolve <id>`.
   - **If no** (a legitimate "stays non-deterministic" conclusion per policy §3): write the
     reasoning first — a `resolution` or `assessment` write explaining why no change is warranted
     — then `nctl workflow-episode dismiss <id>`. Never dismiss without writing the reasoning
     first; a dismissal with no evidence is not distinguishable from one nobody looked at.
6. If you additionally want to record a level/outcome assessment of the original task (policy §2
   attributes, promotion verdict), write it to the `assessment` namespace:
   `nctl workflow-episode write <id> assessment --data '{...}'`.

## Key commands (see `nctl workflow-episode --help` for full options)

- `nctl workflow-episode list [--status S ... | --all] [--json]` — default filter is
  `candidate`+`selected`; `--status` is repeatable.
- `nctl workflow-episode show <id> [--json]` — `--json` returns full `raw_data`.
- `nctl workflow-episode create --title T [--raw-data JSON | --file PATH]` — status always starts
  `candidate` (used at the *end* of a cluster-operation session, not from inside this one).
- `nctl workflow-episode write <id> <namespace> [--data JSON | --file PATH]` — namespace ∈
  `report`/`assessment`/`references`/`resolution`; replaces that namespace wholesale, the others
  are untouched. If you mean to extend rather than replace, read the namespace first (`show
  --json`) and write back the merged value.
- `nctl workflow-episode select <id>` — `candidate → selected`.
- `nctl workflow-episode resolve <id>` — `selected → resolved`.
- `nctl workflow-episode dismiss <id>` — `candidate|selected → dismissed`.

Example (live, read-only — these two episodes exist in the scratch cluster and are visible via
`--status resolved` or `--all` since the default filter hides resolved/dismissed):

```
nctl workflow-episode show 6569864c-8914-4e2e-9368-b7e04c64ac74 --json
nctl workflow-episode show 3915b1e4-8285-431b-bd7a-23203900c08d --json
```

Don't make any instruction in your own work *depend* on these two IDs existing — they are
copy-paste examples, not a fixture you rely on.

## When to stop and ask instead of deciding

You are meant to run on a cheap/local model too. Escalate to the user instead of guessing when:

- It's unclear whether a given pain is a genuine second occurrence (policy §3: automate on the
  second occurrence, not speculatively on the first) — ask rather than promote early.
- The improvement would touch a shared/production-adjacent surface (nctl command semantics,
  policy.md itself) rather than a scoped skill — show the plan and get confirmation before editing.
- The episode's `report`/`references` don't contain enough to understand what happened and the
  referenced transcript/`nctl ops` evidence is itself missing or ambiguous — don't guess at what
  went wrong; ask the user or dismiss with that reasoning recorded.

## Known gotchas

- No DELETE route for a `WorkflowEpisode` — a mis-created episode can only be `dismiss`ed, never
  removed. Don't expect to undo a `create`.
- Transitions are forward-only (`candidate → selected → resolved`, or `→ dismissed` from either).
  Violations exit 2 with `workflow_episode_transition_ineligible`. A premature `resolve` cannot be
  undone — reopening the topic needs a fresh episode, not a state rollback.
- The default `list` filter (`candidate`+`selected`) hides `resolved`/`dismissed` episodes; pass
  `--status resolved` / `--status dismissed` / `--all` to see them.
- `write` replaces the target namespace wholesale. Extending `resolution` or `assessment` across
  more than one write in the same session means read-modify-write, not append.
