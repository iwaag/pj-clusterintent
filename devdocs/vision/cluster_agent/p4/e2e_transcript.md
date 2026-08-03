# Step 4 — smartphone-over-VPN exchange (exit-criteria run)

Live, 2026-08-03. Command node = agstudio (`https://agstudio:8789`,
Tailscale MagicDNS, tailnet `tailab7641.ts.net`). Client = the user's
phone (`iphone181`, iOS), reconnected to the tailnet for this run after
showing `offline` earlier in Step 0/4.

## Session

`ses_03a1af6faffeKoYjWBvxKDizX4`, 3 turns, all identity
`{"class": "human", "name": "operator"}`.

**Turn 1** (new request, `req_ab65b2f100784d9bbc567f6a44c6fb10`)
> User: こんにちは

> cluster-agent: こんにちは。ご用件をお聞かせください。

**Turn 2** (follow-up, `req_b31fc5dd142b49689f39303ba4ebfaf2`)
> User: (model self-identification check)

> cluster-agent: はい。私は `openai/gpt-5.6-luna` です。

**Turn 3** (follow-up, `req_b9dfd1761f17453e8f2becff0127903d`) — the real
resource question, asking the agent to summarize a braindump entry:

> cluster-agent: 以下の braindump を1件取得しました。
>
> **タイトル:** agpcにおけるSwarmUI・ComfyUIの運用とサービス兼用方針
> **ID:** `a19cfa29-1a9c-4316-b81a-70685b407000`
> **状態:** active
>
> **概要:**
> - agpc の GPU上で SwarmUI と ComfyUI を運用する。
> - GUI操作だけでなく、外部スクリプトからAPI経由でも利用したい。
> - agpc は日常利用PCのため停止や応答不能を想定し、SSHまたは
>   node-agent経由で再起動できるようにする。
> - agstudioからも、agpcの生成サービスを利用する想定。
> - Ansibleによる完全自動管理ではなく、手動運用と可逆的な監視・復旧
>   手段を組み合わせる方針。
>
> 付属レビューでは、サービス登録、agpcへの配置設定、HTTP監視、
> SSH/node-agentによる復旧手順の確立が提案されています。

The user confirmed live: "素晴らしい、braindumpの概要を説明させることに
成功しました。" ("Great, I got it to explain the braindump summary
successfully.") — the browser login, question, answer, and follow-up flow
worked end to end from the phone over the VPN.

## Evidence cross-check (command node)

`cagent-evidence list` shows the three `human:operator` entries for this
session interleaved with pre-existing `node:<uuid>` entries from
Phase 2/3 — human and node requests are distinguishable by entrance/
identity, per exit criterion 3. `GET /sessions/{id}/requests` on the
human listener (pulled via `curl` from the command node, not re-typed
from the phone) reproduces the same three turns/responses shown above
verbatim, confirming the evidence and the live browser exchange agree.

## Exit criteria (roadmap Phase 4 / p4/plan.md) — met

1. New request from a browser on a VPN-connected smartphone works, response
   readable. ✅ (turn 1, and turn 3's substantive answer)
2. Follow-up turns in the same session work from that browser. ✅ (turns 2
   and 3 continued `ses_03a1af6faffeKoYjWBvxKDizX4`)
3. Evidence distinguishes entrance/identity class. ✅ (`human:operator` vs.
   `node:<uuid>` in `cagent-evidence list`, and the class-tagged
   `identity` field in every request record)
