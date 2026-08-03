# Easier Next Time — Phase 3 Report

## Step 0 — Author the skill

Created `.claude/skills/retire-proxmox-lxc/SKILL.md` per the plan's facts:
typed inputs (`GUEST`, `VMID`, `CONTROL_NODE`), the exact two-upsert
retirement YAML, the fixed step order (declare batch → dry apply → **user
approval** → apply → dry destructive reconcile → manual_review branch table →
checkpoint (fill-in fields, not prose) → **user approval** → destructive
apply → repeat dry reconcile (zero actions) → dry prune → **user approval** →
prune apply), the `manual_review` branch table (`no_realized_object`,
`actual_node_not_linked`, both from the audited episode — re-derived their
exact severities and messages from
`~/.local/state/nctl/events/01KZ2ZE44M3G766FN298HXCRJ8/plan.json` rather than
trusting `audit.md`'s prose summary alone), machine-checkable success
evidence, and prohibitions/stop conditions.

Frontmatter follows policy §5's fields. `last_verified` and
`verified_against` are `null` — explicitly unverified, per the plan and
policy §8.3 ("authoring alone never sets `last_verified`"); a note at the top
of the body states this and points at Step 2/3 as where it gets filled in.

One discrepancy found and resolved while authoring: `audit.md` reported
`actual_node_not_linked` as a "manual_review error" from the episode, but
`nctl/src/nctl_core/reconcile/classify.py`'s current table classifies that
code `AUTOMATIC` (`link_actual_node` reconciler) — it has been classified
that way since `dea9832` (2026-07-17), before the episode ran. Reading the
actual `plan.json` for that operation resolved the discrepancy: the code
appeared at `severity: warning`, not `error`, and only `no_realized_object`
(`severity: error`) was the blocking manual_review finding;
`actual_node_not_linked` was contextual explanation for why the one strong
actual-VM candidate couldn't be auto-linked at the *node* level (VM
realization belongs to `DesiredComputeInstance.realized_vm`, not
`DesiredNode`). The branch table encodes this precisely — treating
`actual_node_not_linked` as blocking only when it appears without
`no_realized_object` — rather than repeating the audit's flatter "two error
codes" framing into the skill.

Commit: this step is committed with this report.

## Step 1 — Static verification

Re-read `SKILL.md` end to end as the executor, with no outside knowledge
beyond the body and the two README sections it points to for background
(neither of which is required to *execute* — commands, order, checkpoint
fields, and the branch table are all inline, per the plan's advice).

Checks performed:

- Frontmatter parses as valid YAML (`python3 -c 'yaml.safe_load(...)'`
  confirmed) and lazy-loading works the same way as any other Claude Code
  skill — `name`/`description` are the only fields guaranteed always in
  context, and `description` is one specific sentence naming the exact
  workflow, per the plan's fact about `.claude/skills/` pickup.
- Every command in "Permitted commands" matches the exact flags used in
  `nctl/README.md`'s two retirement sections (`--allow-destroy --json` dry,
  `--allow-destroy --yes --json` apply, `--yes` alone refuses destruction —
  not relied on or mentioned as a trap here since the skill never emits that
  form).
- The step-6 checkpoint asks for three fill-in fields (slug, vmid, control
  node) sourced from the *immediately preceding* dry-plan output, addressing
  the audit's 3-second-gap near-miss directly (prohibition 5 in the body
  reinforces "re-read the fresh plan, don't reuse an earlier one").
- `.local/retire-GUEST.yaml` is confirmed git-ignored (`.gitignore` line 2:
  `.local`), satisfying prohibition 1 (no secrets/cluster-private paths
  committed).
- No step assumes information outside the guest slug, vmid, and control node
  the executor is told to obtain up front; every `--yes` step has its own
  explicit "STOP — user approval required" line rather than one blanket
  approval covering the whole run, matching Phase 3's prohibition 5.

No wording or command needed correction. No fix commit was necessary beyond
Step 0's.

Step 1 is complete: static verification found the body self-contained and
consistent with current `nctl`/README behavior. No live commands were run.

## Step 2 — attempted, blocked

Attempted later in this same session, at the user's explicit direction
(deviating from policy §7's time-separation rule — recorded as a deliberate
one-off exception, not a change to the rule). Full account in
[`failure1.md`](failure1.md): a scratch guest (`agscratch1`, vmid 199,
`aghub`) was created and declared retired, the skill correctly stopped at an
unenumerated `manual_review` code (`compute_instance_missing`) rather than
improvising past it, and two capable-model remediation attempts outside the
skill's declared scope both failed — the second on an external Nautobot
ingest-job timeout, not a skill or `nctl` defect. Work stopped there per the
user's instruction rather than continuing against a degraded Nautobot.

One real, confirmed skill-body defect was found and is **not yet fixed**
(prohibition 4 — the Step 2 executor does not edit the skill mid-use): the
embedded retirement YAML is missing the `dry_run: true` envelope field
`nctl desired apply` requires.

**Status: blocked**, per README_DEV.md §9. Phase 3's exit criteria (one
completed real use, `last_verified` set) are not met. `agscratch1`/vmid 199
is left live and undestroyed — see `failure1.md` for the exact state and
required follow-up. Step 3 cannot proceed until a clean Step 2 exists.

## Fix 1, Step 0 — Close the failed episode record

Recovery of this blocked state is tracked under
[`fix1/plan.md`](fix1/plan.md). Step 0 wrote the policy §4 self-report at
`.local/evidence/workflow-episodes/20260803_retire-agscratch1/selfreport.md`,
covering the `safe_stop` at `compute_instance_missing`, the
`partially_completed`/`interrupted` scratch-fixture recovery attempt, and the
two independent defects the episode surfaced (missing `dry_run: true`
envelope field, host-scope widening of `--refresh-observation`). See
[`fix1/report0.md`](fix1/report0.md) for the step report.

The blocked conclusion above still stands: Phase 3 is not complete, and
`agscratch1`/vmid 199 remains live and unresolved pending Fix 1's later
steps.
