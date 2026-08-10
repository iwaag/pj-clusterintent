# workflow-improvement — agent manual

**workflow-improvement** = taking one `WorkflowEpisode` a human has selected,
reading its `report`/`assessment`/`references` from the database, improving
policy / agentdocs / a `.claude/skills/` runbook / nctl / a submodule so the
same pain does not recur, recording what changed into the episode's
`resolution`, and transitioning it to `resolved` (or `dismissed`).

The second `agentdocs/` session type, alongside `brainforge`. It is a separate
session from the cluster-operation work the episode is about: the observation
that something was painful becomes an episode `report` at the end of that
session, and the improvement happens here, later, from the selected episode.

- [`../../devdocs/vision/easier_next_time/policy.md`](../../devdocs/vision/easier_next_time/policy.md)
  — §1–§3 the level vocabulary, §5–§6 skill/runbook conventions, §7 time
  separation, §8 secrets and reference IDs. The rule that gated improvement on
  a pain recurring twice was removed from §3 on 2026-08-07.

## The episode's namespaces

| Namespace | What it is |
|---|---|
| `report` | the original evidence, written by the session the episode came from |
| `assessment` | a level/outcome verdict on that original task (policy §2 attributes) |
| `references` | stable IDs — nctl operation IDs, Braindump/desired-state IDs, session identifiers |
| `resolution` | what this session changed: commit SHAs, skill names, a short summary |

`write` replaces a namespace wholesale and leaves the others untouched; the
per-namespace API is why improvement work and original evidence do not collide.

## Commands (`nctl workflow-episode --help` for full options)

- `nctl workflow-episode list [--status S ... | --all] [--json]` — default filter is `candidate`+`selected`; `--status` is repeatable.
- `nctl workflow-episode show <id> [--json]` — `--json` returns full `raw_data`; the ID alone fetches everything, there is no separate file.
- `nctl workflow-episode create --title T [--raw-data JSON | --file PATH]` — starts as `candidate`; used at the end of a cluster-operation session.
- `nctl workflow-episode write <id> <namespace> [--data JSON | --file PATH]` — free-form JSON by convention, not schema.
- `nctl workflow-episode select <id>` — `candidate → selected`.
- `nctl workflow-episode resolve <id>` — `selected → resolved`.
- `nctl workflow-episode dismiss <id>` — `candidate|selected → dismissed`.
- `nctl session new workflow-improvement --topic <short-slug>` — scratch space at `.local/workspace/<task_name>/<slug>/`; nothing reads it back, so what is not written into the episode via `nctl` is not recorded.

Read-only examples that exist in the scratch cluster (visible under
`--status resolved` or `--all`; copy-paste samples, not a fixture):

```
nctl workflow-episode show 6569864c-8914-4e2e-9368-b7e04c64ac74 --json
nctl workflow-episode show 3915b1e4-8285-431b-bd7a-23203900c08d --json
```

## Known gotchas

- No DELETE route for a `WorkflowEpisode` — a mis-created one can only be
  `dismiss`ed. A `create` does not come back.
- Transitions are forward-only (`candidate → selected → resolved`, or
  `→ dismissed` from either). Violations exit 2 with
  `workflow_episode_transition_ineligible`, and a premature `resolve` needs a
  fresh episode rather than a rollback.
- The default `list` filter hides `resolved`/`dismissed`.
- `write` replaces wholesale: extending `resolution` or `assessment` across two
  writes in one session is read-modify-write.
- The GUI list/detail views need a Nautobot browser session login; an
  `Authorization: Token` header gets a 302 to the login page. An agent cannot
  render or screenshot the GUI headlessly — `list/show --json` is the
  equivalent data, not equivalent verification of GUI presentation.
- The three pre-scheme `.local/evidence/workflow-episodes/` directories may be
  deleted at any time, so a local path there is not a stable reference.
