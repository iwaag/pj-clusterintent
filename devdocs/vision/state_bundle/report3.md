# state_bundle Step 3 report — end-to-end through the cluster-agent

Status: **complete** (the original request, sent through the cagent human
entrance, returned a working download URL whose zip is a valid
`nctl.bundle.v1` bundle).

## Definitive run

- Request (human entrance, `POST /requests`, bearer-token auth):
  「desired state/actual stateを全てファイルにまとめてダウンロードURLを
  示してください」
- `request_id`: `req_26bd97133d57498893117de91d8e6c92`
  (`session_id`: `ses_02f92d917ffeMDcCF2aNrPv4hq`), 2026-08-05.
- State reached `completed`; the reply presented one presigned MinIO URL
  (object `2026-08-05/053810-284164/cluster-state-20260805T053734Z.zip`)
  with its expiry quoted (2026-08-05 07:38:10 UTC, 120 min TTL).
- The session's command log shows the agent followed
  `nctl/docs/state-bundle.md` verbatim: `mkdir .local/tmp/cluster-state-…`,
  `nctl desired export` + `drift`/`actual`/`relations --json`,
  `git -C nctl rev-parse HEAD`, self-written `manifest.json` (checked with
  `jq` before upload), `nctl upload DIR --zip --ttl 2h`. All read-only, as
  the recipe requires.
- The URL was downloaded and verified independently: the zip contains
  exactly `manifest.json`, `desired.yaml`, `drift.json`, `actual.json`,
  `relations.json`; `manifest.json` is `schema: nctl.bundle.v1` with
  `nctl_git_sha 5cc7fe4176c11a1b4bd70ac787dc911eb04833a1` and four
  `contents` entries whose inner envelope schemas all match;
  `desired.yaml` parses as the batch envelope with 38 operations —
  identical shape to Steps 1–2. Manifest copy retained (git-ignored) at
  `.local/state_bundle_step3_manifest.json`, alongside the raw
  request/response JSON (`.local/state_bundle_step3_*`).

## Two defects found by the first attempt, fixed en route

The first end-to-end attempt (`req_4bbbba5bf6994aec969c41221808214b`, same
day) failed with `{"code": "timeout"}` after the cagent worker's fixed
300-second turn bound aborted a turn that was legitimately still working.
Its transcript exposed two real frictions:

1. **Recipe used `mktemp -d`** (outside the working directory), and the
   OpenCode read tool cannot read outside the workdir — the agent burned
   turn time on failing `read` calls. Fix: `nctl/docs/state-bundle.md` now
   builds the bundle under the repo's git-ignored `.local/tmp/`, with the
   reason stated in the recipe.
2. **`TURN_TIMEOUT_SECONDS` was a hard-coded 300.0** in
   `cagent/src/cagent_api/worker.py`. A multi-command composition plus the
   backing model's latency can legitimately exceed that. Fix: the bound is
   now `CAGENT_TURN_TIMEOUT_SECONDS` (default unchanged at 300, documented
   in `cagent/README.md`'s env table; the timeout value is not pinned by
   any frozen phase contract). cagent's suite passes: **92 passed**.
   The local cagent-api was restarted with
   `CAGENT_TURN_TIMEOUT_SECONDS=1800` (scratch-service restart per
   `.local/localenv_memo.md`).

A second, intermediate attempt (continuing the timed-out session) also
timed out before the fixes; both failed request IDs and their evidence
remain in `~/.local/state/cagent/evidence/`. With both fixes in place, the
fresh definitive run above completed well inside even the old bound —
the recipe friction, not the recipe length, was the dominant cost.

## Notes

- The failed attempts performed no writes beyond MinIO outbox uploads;
  nothing needed rollback.
- Per README_DEV's caller-side rule, a `WorkflowEpisode` self-report was
  created for this exchange (the timeout pain and its fixes) — cagent
  itself does not self-report.
