# Easier Next Time 2 — Development Roadmap

Status: adopted 2026-08-04. Detailed plans are written per phase (`pN/plan.md`)
when each phase starts; this document fixes only the goals, order, and settled
design decisions.

## Purpose

Implement the agreement in [`discuss_idea1.md`](discuss_idea1.md). Centralize
workflow-episode reporting, assessment, selection, and resolution in the
nintent DB: a human surveys improvement candidates in a read-only GUI and
selects one; an agent fetches everything it needs from the episode ID and
improves the workflow in a dedicated `workflow-improvement` session.

Premise: the improvement loop itself, defined in
[`../easier_next_time/policy.md`](../easier_next_time/policy.md), does not
change. What changes is the medium of record and selection (scattered local
files → nintent).

## Governing decisions

Settled during discussion; phases do not re-litigate them.

1. **Minimal model.** `WorkflowEpisode` carries only `title` / `status` /
   `raw_data` beyond the standard `PrimaryModel` fields. No other attribute
   gets a column up front; everything lives in `raw_data` and is promoted to a
   column only once it is actually consumed by frequent filtering, aggregation,
   or deterministic processing (same policy as Braindump).
2. **Status vocabulary is `candidate` / `selected` / `resolved` /
   `dismissed`.** policy.md's `outcome` vocabulary (`completed` etc.) describes
   how the original cluster task ended; `status` describes the improvement
   queue state. To avoid the collision, a finished improvement is `resolved`,
   not `completed`.
3. **Transitions are forward-only.** `candidate → selected → resolved |
   dismissed`, plus `candidate → dismissed`. No `selected → candidate`
   demotion; add it later if it is ever actually needed.
4. **Minimal raw_data validation.** Only the top-level namespaces
   (`report` / `assessment` / `references` / `resolution`) and
   `schema_version` are validated server-side as a closed set. Sub-fields are
   free-form. The only goal is preventing silent accumulation of typo
   namespaces.
5. **Write APIs are per-namespace.** Callers never replace the whole
   `raw_data`; each operation updates only the namespace it owns. This
   structurally prevents an improvement session from erasing the original
   self-report. No dedicated history model — rely on Nautobot's change log.
6. **Implement the happy path only.** No fallback machinery for a down
   Nautobot or a broken DB (local draft → later import, etc.). If episode
   creation fails, report that in the session and move on. Leaving a manual
   note in a local folder during trouble is operator discretion, not a
   mechanism.
7. **GUI is read-only.** List/detail only. All writes — add/edit/delete and
   status transitions — are centralized in the REST API + nctl. The human's
   `candidate → selected` action also goes through
   `nctl workflow-episode select`, and that procedure is documented as part of
   the `workflow-improvement` protocol in agentdocs.
8. **The 3 existing episodes are not migrated.** The existing directories
   under `.local/evidence/workflow-episodes/` are low-value data; build no
   import mechanism and do no import work. Leave them as-is; they may be
   deleted at any time.
9. **No backward compatibility.** Per the standing breaking-change policy,
   rewrite the self-report destination in policy.md and README_DEV.md to the
   new scheme and remove the old local-file workflow from the text. No dual
   writers, no feature flags.
10. **Out of scope** (discuss_idea1 §8): automatic collection of all sessions,
    copying transcript / ops-evidence bodies into the DB, feature-rich
    dashboards, speculative column promotion, auto-generating desired state or
    reconcile actions from a WorkflowEpisode, attachment or full-text-search
    infrastructure.

## Execution environment and implementer discretion

This is an experimental environment with no production users. The fixed
prohibitions are minimal:

- No secrets or tokens in Git-tracked files or in `raw_data`. `references`
  holds stable identifiers (session IDs, operation IDs, Braindump IDs,
  commits), not machine-local absolute paths.
- Do not copy transcript or operation-evidence bodies into `raw_data`.
- Do not record a status or completion the evidence does not show
  (README_DEV completion language).

Everything else — exact field naming, API URLs, nctl subcommand names, GUI
presentation details, the sub-structure of the JSON — is implementer's
discretion, to be fixed by use.

## Useful facts for implementers

- **The model precedent is Braindump.** It is the existing example of the same
  shape: kept out of desired-state batches, with a dedicated REST API, a
  dedicated nctl command group, and a read-only GUI. Following its serializer,
  view, URL, and nctl client/command structure is the shortest path.
- **The GUI precedent is the existing `Desired*` view pattern and the
  DesiredWorkspace minimal GUI** (implemented in creative_workspace p2ex):
  the minimal set of list view / detail view / table / filterset / template /
  nav entry. This also satisfies README_DEV's "New models need a minimal
  read-only GUI" rule.
- **Detail display**: render `raw_data` not only as a raw JSON dump but as
  report / assessment / references / resolution sections (discuss_idea1 §5).
  Default list filter is `candidate` + `selected`.
- **Deploying nintent to the container** is "commit → push (ask the user) →
  `docker compose build` → restart". The build can silently cache a stale
  commit, so use `--no-cache` and check the resolved SHA in the build log
  (`.local/localenv_memo.md`).
- **Test gates** follow the README_DEV matrix: nintent Django-free fast, nctl
  ordinary, and the Nautobot runtime gate for cross-component changes
  (`--keepdb` while iterating, `--clean` for final). Scratch-environment reuse
  rules are in `.local/localenv_memo.md`.
- **Expected command surface** (names finalized at implementation time):
  `nctl workflow-episode create / list / show / select / resolve / dismiss`,
  plus per-namespace write operations for report / assessment / resolution if
  needed. These are plain CRUD; they need no reconcile-style plan/apply
  boundary (per README_DEV's minimal dry-run policy, do not add a dry-run
  merely because a command mutates). They are neither destructive nor
  external-reaching, so `--yes`-style confirmation can be minimal.
- **The agentdocs precedent is brainforge** — add `workflow-improvement` as
  the second session type. The start/finish flow is discuss_idea1 §6.
- **The time-separation rule stays**: never improve a runbook mid-task during
  a cluster operation; improvement happens in a separate
  `workflow-improvement` session (policy.md §7).

## Phases

Each phase gets its own `pN/plan.md` when started and runs in the established
step-by-step style (one report + one commit per step, pause before live or
hard-to-reverse actions). The exit criteria below are the fixed part.

### Phase 1 — nintent: WorkflowEpisode model + REST API + read-only GUI

Add `WorkflowEpisode(title, status, raw_data)` with migrations, a dedicated
REST API (CRUD + status transitions + per-namespace writes, with top-level
namespace / schema_version validation), and the read-only list/detail GUI, all
in one change. Deploy to the scratch Nautobot and verify API and GUI live.

Exit: model, API, and GUI work on the scratch Nautobot; an episode created via
the API is visible in the GUI list/detail; forward-only status transitions and
rejection of invalid namespaces are proven by tests.

### Phase 2 — nctl: workflow-episode command group

Add the `workflow-episode` command group to nctl (create / list / show --json /
select / resolve / dismiss, plus per-namespace writes if needed). The key
requirement: an agent can fetch report / assessment / references from nothing
but an episode ID.

Exit: the nctl ordinary suite passes, and a full
create → list → show → select → resolve round trip is smoke-verified against
the live scratch Nautobot.

### Phase 3 — agentdocs + policy update

- Add the `workflow-improvement` session type to agentdocs, covering the full
  procedure: human surveys the GUI → `nctl workflow-episode select` → start
  session → read from DB → improve → update `resolution` → `resolve`.
- Rewrite policy.md §4: self-report destination becomes `WorkflowEpisode`
  creation, the audit unit becomes the episode ID, and the later `review.md`
  becomes an `assessment` update. Update the matching README_DEV.md paragraph
  in the same change. Remove the old local-file workflow from the text.

Exit: every document a new session consults points only at the new scheme,
with no remaining references to the old one.

### Phase 4 — One real cycle and evaluation

In a real cluster-work session, create a self-report as an episode; have the
human survey the GUI and select one; run a `workflow-improvement` session end
to end through `resolution` / `resolved`. Based on that experience, make
minimal fixes to GUI presentation, commands, and the protocol, and record
whether any column-promotion candidate actually appeared.

Exit: one cycle completed on real data, with a short evaluation report. After
that, this continues as standing practice, not a roadmap.
