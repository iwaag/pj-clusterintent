# Fix 1 — Step 0 report: close the failed episode record

Status: **complete**.

## What was done

Wrote the policy §4 self-report for the failed Step 2 episode to
`.local/evidence/workflow-episodes/20260803_retire-agscratch1/selfreport.md`
(the episode directory already existed, created empty during the earlier
attempt, per the plan's expectation).

The self-report:

- references the four operation IDs from `failure1.md`
  (`01KZ3XHADPAMV7MHDB7KDP2J0Y`, `01KZ3XYBZXZ2V0ZR90W3PGTS7Z`,
  `01KZ3Y03VWJNCA155QWAD6XNG1`, `01KZ3Y5KTQ54XNF6JS7YVNPE5R`) and the
  Nautobot JobResult ID (`c104e2eb-8963-4f28-a5ed-f417f2c71a45`) without
  copying their evidence bodies;
- records the outcome precisely per the plan's Step 0 instructions: the
  skill use itself ended in a correct `safe_stop` at the unenumerated
  `compute_instance_missing` code; the surrounding scratch-create/recovery
  work was `partially_completed` and then `interrupted` by the pending
  ingest Job; the runbook reduced improvisation at the destructive boundary
  but the missing `dry_run` field and an unprepared fixture forced Level 2
  recovery; and the host-scope expansion was discovered only by inspecting
  durable evidence (`plan.json`), not from the CLI invocation or README
  description.

`last_verified` was not touched — it remains unset in the skill frontmatter,
as it has been since authoring.

Appended a short Fix 1 Step 0 note to `../report.md` pointing at the
self-report and this report, and restating that the earlier blocked
conclusion still stands.

## Verification

Re-read the written self-report end to end against policy §4's template
(all six sections present: what was requested/what happened, references,
improvised parts, skills used, second-occurrence feeling) and against the
plan's four specific outcome bullets (all four covered).

No live commands were run. No cluster or Nautobot contact. This step is
Git/documentation only.

## Next

Step 1: fix the `dry_run: true` gap in `nctl/README.md` and the skill, and
strengthen the skill's realized-compute precondition.
