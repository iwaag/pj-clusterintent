# Phase 4 Step 3 — Mark superseded active-roadmap goals

Parent: [plan.md](plan.md) Step 3.

Executed 2026-07-25.

## 1. `devdocs/big/core_reconcile/roadmap.md`

- Rewrote the Vision section's 3-way output split (dashboard/AI-JSON/CLI) into a 2-way split
  (humans+AI both read structured JSON/CLI text and disk operation evidence; CLI executes
  workflows), with a new paragraph stating Phase 3's dashboard and Phase 5's realtime API were built
  and removed, linking `remove_unused_surfaces/roadmap.md`.
- Renamed "Design conventions for a future UI" to "Design conventions" and annotated items 1 and 3
  to note the HTTP/WebSocket wrapper and in-process subscriber bus were built and later removed,
  without deleting the historical CLI/library-separation and JSONL rationale (both conventions are
  still true and still govern `nctl_core`).
- Added `**Superseded and removed by remove_unused_surfaces/roadmap.md**` headers to Phase 3
  ("Visualization dashboard") and Phase 5 ("Realtime API layer"), each explicitly pointing at the
  historical `p3/`/`p5/` reports as truthful records of what was implemented and later deleted. Each
  phase's original goal/body text is kept intact underneath, relabeled "Original goal" — not deleted
  or rewritten as though the feature never existed (plan §4.6/§4.3).
- Updated the "Rationale for phase ordering" bullet about Phase 5 from a forward-looking "doesn't
  need to start until..." to a past-tense "was built, then removed as unused."

## 2. `devdocs/big/braindump/roadmap.md`

- Retitled Phase 4 "Optional presentation and API integration (superseded)" and added a supersession
  paragraph: `nctl serve` and both dashboards were removed, so the phase's two options no longer have
  a host to build on; no remote/presentation extension is planned without a named consumer and a
  separate roadmap. The paragraph explicitly reaffirms that models, minimal Nautobot UI, GraphQL
  reads, REST mutations, nctl CLI workflow, authorship, and the non-executable prose boundary are
  all unaffected (plan §4.4's positive-preservation requirement).
- Struck through (`~~...~~`) the two now-impossible bullets (`nctl serve` endpoints; dashboard/
  Nautobot summary) rather than deleting them, and kept the third (cluster-wide summary/structured
  findings/stronger authorization) open for a future roadmap with its own consumer, matching the
  original "only when live operation supplies a specific use case" gate.
- No other section of this roadmap (models, minimal UI, GraphQL, REST, nctl CLI, non-goals) was
  touched.

## 3. `devdocs/big/vm/roadmap.md`

- Added a "Removed-surfaces note" directly under Purpose, naming the three removed surfaces
  (`nctl serve`, both dashboards, the reconciliation-status cache), stating every "dashboard"/"status
  effect" reference below means structured JSON drift + CLI text + reconcile classification +
  `nctl ops list/show` evidence, and explicitly confirming no desired-MAC/digest/planner/SSH-Ansible/
  recovery/scope/non-repetition requirement is weakened by this note.
- General finding-contract line (§ "Each code must define..."): replaced "dashboard/status effect"
  with "structured JSON/human-readable drift evidence."
- Phase 4 title: "...and dashboard explanation" → "...and drift-output explanation"; its "Add all
  compute findings to status, human drift rendering, JSON envelopes, dashboard tiles, and reconcile
  classification" bullet → "...structured JSON envelopes, human drift rendering, and reconcile
  classification (no dashboard or serve output; see the removed-surfaces note above)."
- Phase 9 bullet "Make dashboard and CLI views explain..." → "Make structured JSON and human-readable
  CLI drift output explain..."
- "Definition of done for each phase" inventory bullet: removed `dashboard` from the impact list,
  added a parenthetical pointing back to the removed-surfaces note.
- Re-grepped the file after all edits: the only remaining `dashboard` occurrences are inside the new
  removed-surfaces note itself (naming the surface to explain its removal, per plan §4.2's own
  exception) and the two pointers back to that note — zero operative dashboard/status requirement
  remains.

## 4. `devdocs/big/vm/p3/plan.md`

- Updated only the top supersession note's tense, per plan §4.5's narrow allowance: "are being
  removed by that separate, coordinated initiative" → "have been removed locally by that separate,
  coordinated initiative (Phases 0–4 implemented; the nintent removal migration `0016` and the
  matching nctl/root revisions are prepared but live deployment is still pending a coordinated
  maintenance window)," and added a note-provenance credit to this Phase 4 plan.
- Re-checked every other `dashboard`/`status`/`reconciliation_status` mention in the file (lines
  219, 973 and the surrounding Step 6/8/11 sections): all already state "no dashboard or serve
  output" / describe the surface solely to explain its supersession. No other change made, matching
  the Step 1 manifest's "narrow wording only" scope exactly.

## 5. Safety proof — no weakened VM/Braindump requirement

Diffed each changed file against its pre-edit version (`git diff`): every edit is a header addition,
a prose/vocabulary substitution ("dashboard tiles" → "JSON envelopes", "status effect" → "drift
evidence"), a strikethrough, or a tense change. No line defining desired-MAC mismatch/ambiguity
blocking, digest suppression, planner/direct-apply suppression, zero-SSH/zero-Ansible proof,
recovery, scope isolation, non-repetition, Braindump models/UI/API/CLI/authorship, or the
non-executable prose boundary was touched.

## Gate

No active roadmap asks future work to restore a removed surface, and no retained VM or Braindump
safety/authority condition was weakened. Step 3 gate met.
