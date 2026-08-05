# Step 4 report — teach the cluster-agent

Status: **complete**

## Surfaces updated

- `nctl/README.md` — already gained the usage lines and a `### upload`
  section in Step 3, including the composition pattern
  (`nctl drift --json > f && nctl upload f`).
- Superproject `README.md` — `nctl upload` added to the Reconciliation CLI
  command list plus a paragraph stating the no-state-specific-export
  composition rule.
- `cagent/opencode/AGENTS.md` (the cluster-agent's instructions) — new
  capability bullet: `nctl upload` is allowed (writes only to the local MinIO
  outbox, never cluster/desired state), with the exact compose recipe
  (read-only command → temp file → upload → relay URL **and expiry**), the
  one-URL-per-invocation zip behavior, and a style rule to quote the printed
  URL/expiry verbatim, never fabricate one.
- `cagent/src/cagent_api/static/llms.txt` (what requesters read) — notes the
  agent can hand data back as a time-limited download URL. Served straight
  from disk per request, so no cagent-api restart was needed (verified via
  live `GET /llms.txt`).
- The cagent permission template needed no change: `nctl upload` is not
  covered by the deny rules (which pin `reconcile --yes` / `desired apply
  --yes`), and upload mutates no cluster state.

## End-to-end check (human entrance)

Request sent to the running cagent human entrance
(`https://agstudio.local:8789/requests`, bearer token from
`~/.local/state/cagent/human_token`, CA-verified TLS):
「クラスタのdesired/actual stateを1つのファイルにまとめて、ダウンロードURLをください」.

- **First attempt** `req_21d83c43310040709ab56f123c2b10e2` **failed**
  (`timeout: turn did not complete within timeout`, 300 s). Session evidence
  showed the agent — still running on the pre-update instructions loaded at
  OpenCode start — spending the whole turn source-diving for an export path
  and hand-rolling a snapshot script; it built the state file but never
  reached upload. Remediation: restarted the scratch cluster-agent OpenCode
  instance (`cagent/opencode/start.sh`, local scratch service — ordinary
  restart per `.local/localenv_memo.md`) so it loaded the updated AGENTS.md.
  cagent-api itself kept running.
- **Second attempt** `req_6760e478c04e4871a8571c451f8b017f` **completed in
  ~31 s**. Session transcript shows the intended composition: `nctl drift
  --json` and `nctl actual --json` into a temp dir, `jq` merge into
  `cluster-desired-actual.json`, then `nctl upload` (2 h TTL). The reply
  contained the presigned URL as a markdown link plus
  「有効期限: 2026-08-05 06:17:27 UTC」.
- **URL verified from the transcript, not trusted**: `curl` on the exact URL
  in the reply → HTTP 200, 70,501 bytes of valid JSON with top-level
  `schema` / `exported_at` / `drift` / `actual` keys.
- No mutation ran: every nctl command in both sessions was `--help`, a
  read-only reader, or `upload`.

## Notes

- The first-attempt timeout is a real finding about instruction freshness:
  OpenCode picks up `AGENTS.md` edits only for sessions created after a
  restart of the serving instance. Recorded here so the next instruction
  change budgets for that restart.
- Objects accumulate in `nctl-outbox` by design this phase (no lifecycle);
  the e2e run added one ~70 KB object plus Step 3's three small test objects.
