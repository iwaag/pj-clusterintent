# Phase 4 Step 9 Report — Preservation audit, resume, and VM handoff

Plan: [plan.md](plan.md), Step 9.

Status: **complete**. Every difference from the Step 0 baseline is classified as an approved Import
change or an approved-and-cleaned-up synthetic probe; nothing unexplained. Operations resume
cleanly — there was nothing further to restart, since containers stayed up throughout and the
"freeze" was procedural (no mutating Job/nctl operation), not a container stop.

## 1. Preservation manifest repeat (plan item 1)

| Root | Step 0 baseline | Now | Difference |
|---|---:|---:|---|
| IntentSource | 2 | 2 | 0 (2 rows' `source_config` populated from `{}` — approved, Step 7) |
| DesiredNode | 5 | 5 | 0 (5 rows' `notes` `"" -> null` cosmetic; `description` preserved — approved, Step 7) |
| DesiredEndpoint | 5 | 5 | 0 (3 rows' `description` `"" -> null` cosmetic — approved, Step 7) |
| DesiredIPRange | 3 | 3 | 0 (3 rows' `description` `"" -> null` cosmetic — approved, Step 7) |
| DesiredNodeOperationalOverride | 0 | 0 | none |
| DesiredService | 6 | 6 | none |
| DesiredDependency | 0 | 0 | none |
| DesiredServicePlacement | 1 | 1 | none |
| DesiredComputePlatform | 0 | 0 | none — VM compute roots remain empty |
| DesiredComputeInstance | 0 | 0 | none — VM compute roots remain empty |
| BrainDumpDocument | 5 | 5 | one synthetic row created+deleted in Step 8, net 0 |
| AlignmentReview | 5 | 5 | none |
| Device | 5 | 5 | one synthetic row created+deleted in Step 8, net 0 |
| VirtualMachine | 9 | 9 | none |
| realized `DesiredNode.realized_device` links | 5/5 | 5/5 | none |
| realized `DesiredEndpoint.realized_ip_address` links | 5/5 | 5/5 | none |
| `JobHook` "AI Resource Auto Review" | enabled | enabled | none |
| Migrations | through `0016` | through `0016` | none |

## 2. Classification (plan item 2)

Every difference from Step 0's baseline is one of:

- **approved Import change** (Step 6/7): 2 `IntentSource.source_config` benign default
  populations, 5 `DesiredNode.notes` cosmetic nulls, 3 `DesiredEndpoint.description` cosmetic
  nulls, 3 `DesiredIPRange.description` cosmetic nulls — 13 total rows touched, all individually
  classified in report6b.md Section 6 and re-verified unchanged since, zero unauthorized content
  loss (the one candidate unauthorized case — 5 `DesiredNode.description` erasures — was fixed
  before this apply ran at all, per problem.md's resolution);
- **approved synthetic probe + cleanup** (Step 8): 1 synthetic `DesiredNode`, 1 synthetic `Device`,
  1 synthetic `BrainDumpDocument` created and fully removed; net row-count effect zero, 5 residual
  `ObjectChange` rows (all correctly attributed to real audited writes, per report8.md Section 3.6);
  and
- **no defect-class difference found.**

## 3. AI Resource Auto Review JobHook (plan item 3)

Confirmed unchanged (`enabled=True`, same name) in the Step 0 baseline, Step 5's post-deploy check,
Step 7's post-apply check, and this final audit. No custom-field definition or data change was
made by this phase (out of scope per plan Section 4.3, and no action in Steps 4-8 touched
`CustomField`).

## 4. No compute/Proxmox/host/SSH/Ansible change (plan item 4)

`DesiredComputePlatform`/`DesiredComputeInstance` remain `0`/`0` throughout (confirmed at Step 0,
Step 6's re-run preview scope, and this final audit). No Proxmox object, generated production
file, SSH trust entry (the synthetic host was never enrolled — its `reconcile --yes` attempt was
correctly *refused* at the SSH pre-flight gate, per report8.md Section 3.3), or Ansible target was
touched. `nctl ops list` shows no new operation entries beyond the dry `reconcile` (`state:
planned`, no execution) run in Step 8.

## 5. Migrations (plan item 5)

`nautobot-server showmigrations nautobot_intent_catalog` ends at
`0016_remove_reconciliation_dashboard_surfaces` on the live web container — unchanged from Step 0
through this final check (`.local/interface-contract/p4/20260726_step9/final_migrations.txt`).

## 6. Final matched tuple confirmation (plan item 6)

All three live containers (`nautobot-nautobot-1`, `nautobot-nautobot-worker-1`,
`nautobot-nautobot-scheduler-1`) run image `sha256:a4c20f6ad4b3d3d8b14cd483e8fb23c78943dd4701cef259f449cb1b065ad94a`
(`nic-p4-candidate:20260726c`), embedding `nintent_commit: e8732f17ae35d8c72d4d593e8d7311bd234fc0bf`
and `nauto_commit: 1c78af8bdbfc69cafdc293b4082f866de9f271b0`, with identical
`intent_sources.yaml.sha256: f6cdcbb1...`. All local repositories are at the tuple that produced
this image: superproject `1cfc550`, nintent `e8732f1` (unchanged since Step 3), nctl `79b6d6b`
(unchanged since Step 1), nauto `1c78af8` (this session's fix), all pushed and confirmed via `git
fetch origin` equality.

## 7. Resume (plan items 7-8)

No approval-gated restart was needed: `nautobot-nautobot-1`/`-worker-1`/`-scheduler-1` have been
continuously running since Step 5b's redeploy (`Up 24 minutes` and counting at the start of this
step) — the "freeze" in Steps 4-8 was a procedural hold on mutating Jobs and routine `nctl`
operations, not a container stop. `active JobResult` count is `0`
(`.local/interface-contract/p4/20260726_step9/final_jobresult_check.txt`); health/migration checks
above are clean. **Routine nctl mutation and Import/Analyze/IPAM Job submission are no longer held
back as of this report.**

## 8. VM Phase 3 handoff (plan items 9-10)

The deployed strict YAML/Import contract (nine canonical roots, `apply=false`-by-default Import
Job, exact nauto commit `1c78af8` baked into the live image at
`/opt/nautobot/intent_sources.yaml`) is now live and hands off to VM Phase 3 Steps 9-12 per
`devdocs/big/vm/p3/plan.md`.

**Explicitly**: VM compute rows (`DesiredComputePlatform`/`DesiredComputeInstance`), and any
proposed MAC/template seed content, were not touched, previewed, or applied in this phase. They
remain `0`/`0` live and still require their own separate reviewed preview and user approval before
any compute seed content is introduced — nothing here should be read as pre-authorizing that
future step.

## Evidence retention

`.local/interface-contract/p4/20260726_step9/` (directory mode `0700`, files mode `0600`):
`resume_start.txt`, `final_migrations.txt`, `final_jobresult_check.txt`. No secrets/private prose.

## Verification

- Every Step 0 → now difference traces to an approved Import change (Step 7) or a synthetic
  probe fully cleaned up (Step 8); no unclassified difference found.
- `JobHook`, compute roots, migrations, realized links all unchanged/empty as required.
- Final live tuple (image, nintent/nauto commits, YAML digest) matches across all three
  containers and matches the pushed, fetch-confirmed source tuple.
- No approval-gated resume action was required (containers never stopped after Step 5b); the
  procedural writer freeze is lifted as of this report.
- VM Phase 3 handoff stated explicitly, with the compute-seed non-authorization stated explicitly.

Next: Step 10 (final searches, measurements, consolidated final report.md).
