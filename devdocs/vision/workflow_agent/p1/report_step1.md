# Phase 1 — Step 1 report: Plan artifact contract

Date: 2026-08-04.

## What was done

Wrote [`../plan_contract.md`](../plan_contract.md), the frozen contract file
per plan.md Step 1 / roadmap decision 3 and 6.

Contents, matching the plan's design hints exactly:

- §1: exactly four required `##` sections (`goal`, `steps`, `stop
  conditions`, `success evidence`), with per-section rules (steps must be
  executor-turn-sized, name the known workflow when one applies, inline
  their own branches/retries).
- §2: the approval-mark rule — exact marker syntax (`**approval required**`
  on its own line under the step), the hard rule verbatim (a step without
  the marker must not contain `--yes` or `--allow-destroy`), and a note that
  the marker does not substitute for the human approval the flag itself
  gates.
- §3: storage convention (`.local/evidence/workflow-plans/<plan-id>/` with
  `plan.md`/`transcript.*`/`report.md`, `<plan-id> = <date>_<slug>`) and the
  WorkflowEpisode linkage convention (`references.workflow_plan_id`, plan ID
  only, never a path, bodies never copied into `raw_data`).
- §4: one inline minimal complete example (read-only, zero approval marks —
  `nctl drift --json` + `nctl relations --json`), plus one approval-marked
  step snippet trimmed from the `retire-proxmox-lxc` skill's `--allow-destroy
  --yes` step, shown for the marker instance only (not a full second plan).
- §5: one-paragraph scope note (not an executor prompt, not a catalog, not a
  schema/allowlist/replay gate).

## Fixed-constraint check

1. No secrets/tokens/private payloads — the file contains only public
   hostnames-as-examples-already-in-devdocs, command syntax, and a slug; no
   token values. Confirmed by re-reading the written file.
2. The hard rule appears verbatim in §2: "a step without `**approval
   required**` must not contain `--yes` or `--allow-destroy`."
3. No completion claims beyond what this step did — this report only
   describes writing one contract file, not the manual or example (those are
   Steps 2–3).

## Verification

Re-read the written file in full after writing it (via the Write tool's
returned content) to check section count, marker literal, and example
completeness match the plan's design hints. No test suite applies —
documentation-only step, no code touched.

## Exit status

Step 1 done. Step 2 (planner manual) is next; it will link this contract
file.
