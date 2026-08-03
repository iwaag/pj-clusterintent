# Easier Next Time — Phase 1 Report

Date: 2026-08-03
Status: **complete**

Phase 1 of [`../roadmap.md`](../roadmap.md): write the policy and formats that
every later phase references. Documents only; no behavior change. Executed
directly without a separate `p1/plan.md` by explicit user instruction — the
roadmap's Phase 1 section served as the plan.

## Deliverables

| roadmap exit criterion | result |
|---|---|
| `policy.md` with level definitions, recorded attributes, target-level rule, promotion/demotion rules, decay rules | [`../policy.md`](../policy.md) §1–3, §6 |
| Self-report template and its location | `policy.md` §4; episodes go to `.local/evidence/workflow-episodes/<date>_<task>/selfreport.md`; the directory was created |
| Skill frontmatter convention | `policy.md` §5 (`version`, `execution_level`, `triggers`, `risk`, `prerequisites`, `last_verified`, `verified_against`) |
| README_DEV pointer so future sessions know the policy and end with a self-report | new section "Easier Next Time: end sessions with a self-report" in [`README_DEV.md`](../../../../README_DEV.md) |
| No behavior change yet | no code, configuration, or skill was created or modified |

## Decisions made while writing (within Phase 1 discretion)

- The self-report template and skill convention live inside `policy.md` §4–5
  rather than as separate template files — three small formats in one referenced
  document beats four files, and Phase 2/3 will adjust them from real use
  anyway.
- Added `verified_against` (submodule SHAs) next to `last_verified` in the skill
  frontmatter so the Phase 5 staleness check has something mechanical to compare
  against, per the discussion's decay concern.
- `review.md` (the audit's output with §2 attributes and the promotion verdict)
  is written beside `selfreport.md` in the same episode directory; its exact
  format is deliberately left to Phase 2.
- The fixed prohibitions were kept to the roadmap's three (no secrets in Git,
  reference operation IDs instead of copying evidence, no unevidenced
  completion claims); everything else is stated as implementer's discretion.

## Verification

- `policy.md` is consistent with the roadmap's governing decisions 1–7: level
  semantics from discuss_idea1 §3–4, mandatory `target_level` + reason,
  no new logging mechanism, skills as runbooks, decay rules, deferred items
  untouched, time separation stated (§7).
- README_DEV section is a pointer plus the self-report obligation only; it does
  not duplicate the policy content.
- `.local/evidence/workflow-episodes/` exists and is inside the ignored
  `.local` tree (nothing new became trackable).

## Next

Phase 2 — first retrospective: pick one tagged episode (or run one real cluster
task and self-report it), audit transcript + `nctl ops` evidence, and produce
the first `review.md` with an explicit promote / stay verdict.
