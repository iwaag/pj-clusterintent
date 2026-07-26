# Phase 4 Step 7 Report — Apply, refetch, and prove repeat idempotence

Plan: [plan.md](plan.md), Step 7.

Status: **complete**. `Import Intent Sources` was applied with explicit user approval, the commit
was confirmed, GraphQL refetch matches the approved plan, the repeat `apply=true` made zero writes,
and a final `apply=false` preview shows the full 22-row unchanged state. Live writers remain frozen
pending Step 8/9.

## 0. Approval

Explicit operator approval to run `apply=true` was obtained after presenting Step 6's re-run
preview totals (0 unauthorized field losses, 13 pre-classified cosmetic/benign updates, 9
unchanged) — "はい、apply=trueを実行". Per plan Section 3.4 approval #2.

## 1. Pre-apply precondition recheck (plan item 1)

`.local/interface-contract/p4/20260726_step7/pre_apply_fingerprint.txt`: `intentsource=2`,
`desirednode=5`, `objectchange=902`, max `time` `2026-07-26 02:04:49.553337+00:00` (the prior
GitRepository sync's own timestamp — no write since), active `JobResult=0`. All five
`DesiredNode.description` values sampled and confirmed still their real live text
(`agbach`="main macbook", etc.) — the exact target-row precondition Step 6's re-run preview was
generated against.

## 2. Apply run (plan item 2)

```
nautobot-server runjob -u admin -d '{"source_file": "", "apply": true}' \
  nautobot_intent_catalog.jobs.ImportIntentSources
```

Log: `SUCCESS`, `{"conflict": 0, "create": 0, "unchanged": 9, "update": 13}` — identical totals to
the immediately preceding preview, confirming no drift occurred in the ~6 minutes between preview
and apply.

## 3. Commit and confirmation (plan item 3)

Artifact (`intent-import-apply1.json`, `sha256:9797b1f8...59abf1`): `mode: apply`; `writes:
{"attempted": true, "committed": true, "requested": true}`; `transaction: {"status": "committed",
"error": null}`; `confirmation: {"status": "confirmed", "mismatches": []}`; `source.sha256` matches
the fixed file; `errors: []`; `conflicts: []`.

## 4. GraphQL refetch (plan item 4)

A real HTTP GraphQL query (not an ORM shell read) against the live API:

```graphql
{ desired_nodes { name lifecycle description } }
```

confirms all 5 nodes with their correct `lifecycle` (`agbach`/`aghub`=APPROVED,
`agdnsmasq`/`agpc`/`agstudio`=ACTIVE, all unchanged) and their real `description` text preserved —
proof through the actual retained read surface, not just direct DB inspection.
(`graphql_refetch_desired_nodes.json`.)

## 5. Comparison against the approved plan (plan item 5)

`ObjectChange` write-attribution query for the exact apply window
(`2026-07-26T02:12:54.7Z`–`02:12:55Z`) returned **exactly 13 rows**, matching the artifact's
`update` total precisely: `IntentSource`×2, `DesiredNode`×5, `DesiredIPRange`×3,
`DesiredEndpoint`×3 — the same 13 identities named in Step 6's re-run preview, no more, no less.
No `Device`, realized-link, `JobHook`, `DesiredService`, `BrainDumpDocument`, or `AlignmentReview`
row appears in this window.

Realized links spot-checked post-apply: all 5 `DesiredNode.realized_device_id` and all 5
`DesiredEndpoint.realized_ip_address_id` values are present and non-null (unaffected — Import never
writes these fields, per `desired_node_update_fields()`/`desired_endpoint_defaults()` not including
them). `JobHook` "AI Resource Auto Review" still `enabled=True`, untouched.

No conflict, error, delete-like action, lifecycle overwrite, or realized-link write occurred.

## 6. Repeat apply=true (plan item 7)

```
nautobot-server runjob -u admin -d '{"source_file": "", "apply": true}' \
  nautobot_intent_catalog.jobs.ImportIntentSources
```

Log: `{"conflict": 0, "create": 0, "unchanged": 22, "update": 0}`. `ObjectChange` count/max-`time`
identical to immediately after the first apply (`915`, `2026-07-26 02:12:54.982341+00:00` — the
first apply's own last write). Every `DesiredNode.last_updated` value identical to the first
apply's timestamps (checked per-row). No semantic write, no changed timestamp, no new
`ObjectChange` for any row — full idempotence proven, not merely claimed by the "unchanged: 22"
label.

## 7. Final apply=false preview (plan item 8)

```
nautobot-server runjob -u admin -d '{"source_file": "", "apply": false}' \
  nautobot_intent_catalog.jobs.ImportIntentSources
```

Log: `{"conflict": 0, "create": 0, "unchanged": 22, "update": 0}` — the same all-unchanged state.
`ObjectChange` count/max-`time` unchanged again after this run (still `915`,
`2026-07-26 02:12:54.982341+00:00`), and `JobHook` unaffected — the preview itself made zero
writes, as required for `apply=false`.

## 8. Versioned artifacts (plan item 9)

| File | Mode | SHA-256 |
|---|---|---|
| `intent-import-apply1.json` | apply (first) | `9797b1f83497b73d305da187e1a3e3c18fdc8dc3713be9b9cdeb7c16db59abf1` |
| `intent-import-apply2_repeat.json` | apply (repeat) | `01e93075ab5cf892ec4408b283567462e5386a3c8cc227e5e7880afae120cef6` |
| `intent-import-final_preview.json` | preview (final) | `3c3832fb445d0804fedac26a3dc32a88df056ee5e9a9a9706f390851ae087d85` |

(Step 6's `.local/interface-contract/p4/20260726_step5b/intent-import-result.json`, the preview
immediately preceding this apply, is the fourth in the sequence and is retained in that step's
evidence directory.)

## 9. Intended ObjectChanges recorded separately (plan item 10)

The 13-row write-attribution query in Section 5 above is the isolated intended-change record for
this apply; it excludes the unrelated `GitRepository`/`Job` sync rows from Step 6's re-run
(`extras_objectchange` rows at `02:04:49.x`, already attributed in report6b.md Section 5) and any
other cluster history.

## Evidence retention

`.local/interface-contract/p4/20260726_step7/` (directory mode `0700`, files mode `0600`):
`pre_apply_fingerprint.txt`, `import_apply_run.log`, `intent-import-apply1.json`,
`post_apply_fingerprint.txt`, `import_repeat_apply_run.log`, `intent-import-apply2_repeat.json`,
`post_repeat_fingerprint.txt`, `final_preview_run.log`, `intent-import-final_preview.json`,
`post_final_preview_fingerprint.txt`, `graphql_refetch_desired_nodes.json`. Checked for
tokens/credentials before setting permissions — the GraphQL query was authenticated via a token
read from `.local/secrets` at request time and never written to any evidence file or this report.

## Verification

- Pre-apply fingerprint matched the preview's baseline exactly (no drift between preview and
  apply).
- Apply artifact: `writes.committed=true`, `transaction.status=committed`,
  `confirmation.status=confirmed`, zero errors/conflicts.
- GraphQL refetch (real HTTP, not ORM) confirms descriptions and lifecycles for all 5 nodes.
- `ObjectChange` write-attribution for the apply window: exactly the 13 expected identities, no
  more.
- Realized device/IP links and the JobHook are unaffected.
- Repeat `apply=true`: `unchanged: 22, update: 0`; `ObjectChange` count/max-time and every
  `DesiredNode.last_updated` identical to the first apply — zero semantic write proven at the row
  level, not just via the summary label.
- Final `apply=false` preview: `unchanged: 22, update: 0`; zero further write.
- All artifacts preserved with SHA-256 digests.

Next: Step 8 (live retained/removed interface and Job smoke matrix) and Step 9 (preservation audit,
resume, VM handoff) — both still pending. Live writers remain frozen.
