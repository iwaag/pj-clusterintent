# Phase 4 Step 6 Re-run Report — resolve the description-loss problem, redeploy, re-preview

Plan: [plan.md](plan.md), Step 6 (re-run after resolving [problem.md](problem.md)'s "Phase 4 Step 6
— Open Problem").

Status: **preview clean, apply approval requested but not yet given**. The user resolved the open
problem (option 1: add the live `description`/`notes` values to `nauto/seed/intent_sources.yaml`
so the next preview is a true no-op for those fields). This required a small re-run of Steps 3 and
5 (new candidate build with the fixed `nauto` commit, redeploy under a fresh maintenance freeze)
before Step 6's official preview could be re-executed against live Nautobot. The re-run preview
confirms the 5 unauthorized `DesiredNode.description` updates are gone; the remaining 13 updates
are exactly the cosmetic/benign set report6.md already classified as safe. Live writers remain
frozen pending the user's apply decision.

## 0. Decision and source fix

User chose resolution 1 from `problem.md`: add the current live `description` values for the 5
`DesiredNode` rows (and blank-safe `description`/`notes` entries matching live blank fields) to
`nauto/seed/intent_sources.yaml`, rather than changing importer field ownership. Values added
exactly match report6.md's table (`agbach` = "main macbook", etc.). No importer code changed.

- `nauto` commit `1c78af8` ("interface_contract p4 step6 fix: preserve live
  DesiredNode/Endpoint/IPRange description"), pushed by the user and confirmed via `git fetch
  origin` (`origin/main == 1c78af8`).
- Superproject commit `2fa125f` bumps the `nauto` submodule pointer to `1c78af8`, pushed by the
  user (`origin/main == 2fa125f`).
- Local suite re-run after the edit: `python3 -m unittest discover -s nautobot_intent_catalog/tests`
  in `nintent/` — 226 passed, 13 skipped, including
  `CanonicalFileIdentityCountTests.test_canonical_checked_in_file_matches_exact_confirmed_counts`
  (unaffected — it doesn't assert on `description`/`notes`).
- One inert byproduct found while verifying: `_optional_str()` in
  `nintent/nautobot_intent_catalog/loaders.py` treats `""` the same as an omitted key (both become
  `None`), so the `description: ""` entries added for 3 `DesiredEndpoint` and all 3
  `DesiredIPRange` rows, and `notes: ""` for the 5 `DesiredNode` rows, do not change loader output
  versus leaving them omitted. They are harmless (documents the blank as intentional) but do not by
  themselves make those specific cosmetic diffs disappear — only the `DesiredNode.description`
  fields (given real text, not `""`) actually changed the preview's diff, which is the fix that
  mattered per the user's decision.

## 1. Candidate rebuild (repairs Step 3's tuple)

Because the previously deployed candidate image bakes the exact `nauto` commit's
`intent_sources.yaml` in at build time (`devenv/nautobot/Dockerfile`'s `COPY
nauto/seed/intent_sources.yaml`), the local source fix had no live effect until a new image was
built from the updated `nauto` checkout.

- `Dockerfile`'s `ARG NAUTO_COMMIT` bumped from `2635e648...` to `1c78af8b...` (the only change;
  `NINTENT_COMMIT` unchanged at `e8732f1...`).
- `docker build -f devenv/nautobot/Dockerfile -t nic-p4-candidate:20260726c .` — disposable-only,
  no running service touched (plan Section 3.4 pre-approved).
  - Image ID: `sha256:a4c20f6ad4b3d3d8b14cd483e8fb23c78943dd4701cef259f449cb1b065ad94a`
  - `/opt/nautobot/build_info.json`: `{"nintent_commit": "e8732f17ae35d8c72d4d593e8d7311bd234fc0bf",
    "nauto_commit": "1c78af8bdbfc69cafdc293b4082f866de9f271b0"}`
  - `/opt/nautobot/intent_sources.yaml.sha256`: `f6cdcbb195fe...557455b` — matches
    `sha256sum nauto/seed/intent_sources.yaml` on the checked-out submodule exactly.
- Disposable triplet `nic-p4-step6c` (fresh Postgres/Redis, port `18003`, distinct from live and
  every prior disposable project), single `nautobot` service used for verification (web only, same
  image the worker/scheduler would run):
  - `nautobot-server test nautobot_intent_catalog`: **304/304 pass**, 0 failures/errors.
  - `nautobot-server makemigrations nautobot_intent_catalog --check --dry-run`: "No changes
    detected", exit 0.
  - `load_intent_sources(Path('/opt/nautobot/intent_sources.yaml'))` via `nautobot-server shell`:
    `errors=[]`; `agbach.description == "main macbook"`, and equivalently for the other 4 nodes —
    proves the fix resolves correctly through the real ORM-adjacent loader, not just a text diff.
  - Teardown: `docker compose -p nic-p4-step6c down -v`; containers/volumes/network confirmed
    absent by name afterward. Live `nautobot-*` containers were running, untouched, throughout
    (`docker ps` unchanged before/after).
- Evidence: `.local/interface-contract/p4/20260726_step6_rebuild/` (`docker-compose.yml`,
  `nautobot_startup.log`, `app_suite_pass.log`), directory mode `0700`, files `0600`.

## 2. Approvals

Two explicit operator decisions were obtained before any live action, per plan Section 3.4:

1. The original Step 6 blocking problem: user chose resolution 1 ("YAMLに説明文を追加") via
   `AskUserQuestion`.
2. Before redeploying: user approved re-freezing live writers and redeploying the new candidate,
   understanding this repeats Step 5 and re-enters a maintenance window ("はい、進めてください").

## 3. Pre-freeze fingerprint

`.local/interface-contract/p4/20260726_step5b/pre_freeze_fingerprint.txt`: `intentsource=2`,
`desirednode=5`, `device=5`, `objectchange=898`, max `time` `2026-07-25 18:57:17.841395+00:00`,
active `JobResult=0` — identical to report6.md's post-preview fingerprint. No write occurred on
live between the original Step 6 preview and this re-run's start.

## 4. Maintenance freeze and redeploy

```
docker compose --env-file ../.env stop nautobot-scheduler nautobot-worker   # 02:02:12Z-02:02:15Z
docker compose --env-file ../.env stop nautobot                              # 02:02:15Z-02:02:17Z
docker tag nic-p4-candidate:20260726c nautobot-nautobot:latest
docker tag nic-p4-candidate:20260726c nautobot-nautobot-worker:latest
docker tag nic-p4-candidate:20260726c nautobot-nautobot-scheduler:latest
docker compose --env-file ../.env up -d --no-build nautobot
docker compose --env-file ../.env up -d --no-build nautobot-worker nautobot-scheduler
```

All three healthy within ~30s. No `docker compose build` ran (`--no-build`), so the Dockerfile's
`ARG` defaults were not re-resolved during the window — the already-built, already-verified image
was reused, same pattern as report5.md.

`.local/interface-contract/p4/20260726_step5b/deploy_verification.txt`: all three containers
(`nautobot-nautobot-1`, `nautobot-nautobot-worker-1`, `nautobot-nautobot-scheduler-1`) report the
identical image ID, identical `build_info.json` (`nauto_commit: 1c78af8...`), and identical
`intent_sources.yaml.sha256` (`f6cdcbb1...`). `showmigrations` ends at `0016`; `makemigrations
--check --dry-run` clean; `PLUGINS_CONFIG` resolves to `/opt/nautobot/intent_sources.yaml`.

## 5. nauto GitRepository sync

Live `GitRepository` (`main`) was still at the previously approved `2635e64...`. Ran the built-in
`Git Repository: Sync` Job (`nautobot.core.jobs.GitRepositorySync`) — read-only refresh of Git
checkout/Job/config-context registrations, same action Step 5 took for the prior tuple.
`current_head` after sync: `1c78af8bdbfc69cafdc293b4082f866de9f271b0` — matches the pushed commit
exactly. `extras_objectchange` rose from 898 to 902 (+4: the `GitRepository` row plus 3 refreshed
`Job` rows, matching the log's "Refreshed Job record for..." lines); `intentsource`/`desirednode`/
`device` counts unchanged.

## 6. Official live preview re-run (apply=false)

```
nautobot-server runjob -u admin -d '{"source_file": "", "apply": false}' \
  nautobot_intent_catalog.jobs.ImportIntentSources
```

Log: `SUCCESS`, `{"conflict": 0, "create": 0, "unchanged": 9, "update": 13}` — same totals as
report6.md's original run (13 rows still touched), but the *content* of those 13 updates changed.

Artifact (`intent-import-result.json`, schema `nintent.intent-import.v1`, `mode: preview`,
`source.sha256: f6cdcbb1...` matching the new file): every `update` action's `changed_fields`:

| Model | Identity | Field | Old | New | Disposition |
|---|---|---|---|---|---|
| IntentSource | infrastructure | `source_config` | `{}` | computed defaults | benign (unchanged from report6.md) |
| IntentSource | manual | `source_config` | `{}` | computed defaults | benign (unchanged) |
| DesiredNode | agbach/agdnsmasq/aghub/agpc/agstudio (×5) | `notes` | `""` | `null` | cosmetic (unchanged from report6.md; `description` **no longer appears** — fix confirmed) |
| DesiredEndpoint | agdnsmasq/agpc/agstudio primary (×3) | `description` | `""` | `null` | cosmetic (unchanged) |
| DesiredIPRange | dhcp-reserved/network-infra/dhcp-unreserved (×3) | `description` | `""` | `null` | cosmetic (unchanged) |

Verified programmatically: no `object` with `model == "DesiredNode"` has `description` in its
`changed_fields` — the 5 unauthorized real-content erasures from report6.md are gone. `conflicts:
[]`, `errors: []`.

## 7. Independent zero-write proof

`.local/interface-contract/p4/20260726_step5b/post_preview_fingerprint.txt`: `intentsource=2`,
`desirednode=5`, `objectchange=902` (unchanged from post-sync), max `time` unchanged
(`2026-07-26 02:04:49.553337+00:00` — the sync's own timestamp, not touched by the preview), and
`agbach.description` sampled live as `"main macbook"` (unchanged, as expected for `apply=false`).

## 8. Gate disposition

Per plan Section 6 Step 6: the artifact totals and every proposed change are now fully explained
and, per report6.md's already-recorded classification (unchanged by this re-run for the 10
cosmetic/2 benign rows), none is create/conflict/delete-like or unexplained. The prior blocking
finding (5 unauthorized `DesiredNode.description` erasures) is resolved. Live writers remain
frozen; **apply approval has not yet been requested from the user in this turn** — see "Next"
below.

## Evidence retention

`.local/interface-contract/p4/20260726_step6_rebuild/` and `.local/interface-contract/p4/20260726_step5b/`
(directory mode `0700`, files mode `0600`): fingerprints, build/deploy/sync/preview logs, the
artifact JSON. Checked for tokens/credentials/private prose before setting permissions — none
found (only aggregate counts, public hashes, and the artifact's own non-secret domain-field diffs).
Not committed (matches Section 5.5).

## Verification

- `nauto` and superproject fix commits pushed and confirmed via `git fetch origin` equality.
- New candidate image built, disposable-proven (304/304 App suite, clean `makemigrations`, loader
  resolves the fixed `description` values), and torn down cleanly.
- Live maintenance freeze: writers stopped 02:02:12Z–02:02:17Z before any container swap.
- All three live containers (web/worker/scheduler) report identical image ID, `nauto_commit`, and
  YAML digest after redeploy.
- `GitRepository.current_head` after sync == pushed `nauto` commit exactly.
- Official `apply=false` preview: `source.sha256` matches the new file; 0 `DesiredNode.description`
  changes (previously 5); all remaining 13 updates match report6.md's pre-existing cosmetic/benign
  classification; 0 conflicts/errors.
- Independent pre/post `ObjectChange` count and max `time` identical across the preview run; a
  sampled live field confirmed unchanged.

Next: request the user's separate apply approval (plan Section 6 Step 6 item 8 / Section 3.4
approval #2) before running Step 7 (`apply=true`, refetch, repeat idempotence). Live writers remain
frozen until that decision.
