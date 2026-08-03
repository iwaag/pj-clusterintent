# Mid-progress report — written during Step 5, at the user's request

Written to checkpoint state while the user evaluates whether the node-agent's
local LLM is too slow/unreliable for this workflow, before deciding how to
continue. This is not a step report; Steps 0–3 have their own committed
reports (`report0.md`–`report3.md`). This file covers Step 5's in-progress
work and the timing/reliability question raised.

## Status summary

- **Steps 0–3: complete, committed** (commits `5f7f6ba`, `2e2f8a5`,
  `f2f7f71`/`c96e162`, `83d1eaa`). Two real, pre-existing bugs in
  `cagent-api` were found and fixed along the way (both with regression
  tests, unrelated to the model-speed question below):
  1. `GET`/cancel/list endpoints skipped identity checks entirely — a
     revoked cert (or any CA-signed cert at all, registered or not) could
     read/cancel any request and enumerate any node's sessions across the
     whole cluster. Fixed in `cagent/src/cagent_api/server.py`.
  2. A ~1-in-16-odds bug in certificate serial-number hex formatting
     (`cagent/src/cagent_api/ca.py`) that would have permanently locked out
     roughly 10% of future node enrollments with a confusing "not
     registered" error even though the ledger showed the cert `active`.
- **Step 4** (node-agent AGENTS.md instructions): folded into Step 2's role,
  committed.
- **Step 5** (first use-case proof, LIVE): **in progress, not yet
  committed.** This is what triggered the user's question.

## What happened in Step 5

1. Distributed to agpc, verified (Step 3, committed).
2. Started the cluster-agent stack on the command node
   (`cagent/opencode/start.sh` + `CAGENT_API_HOST=0.0.0.0 cagent-api`,
   currently still running, PID visible via `pgrep -fl cagent-api`).
3. Drove agpc's **real node-agent** (its own OpenCode instance, port 4096,
   not a human typing curl) via its session API, prompting it with a task
   requiring cluster knowledge, per the plan.
4. **First attempt** ("I want S3-compatible storage"): the node-agent
   correctly ran `cagent ask` (blocking/waiting form) three separate times,
   each killed by its own bash-tool timeout (120s, then 300s, then 30s)
   before the cluster-agent's answer was ready — even though the
   cluster-agent kept working server-side regardless and the *third*
   underlying request did complete correctly and usefully
   (`req_82b7dc4b91994d9590149ca24b7b384f`, evidence confirms: correct,
   `nctl drift`-grounded answer, no S3-compatible storage present). The
   node-agent itself never saw this answer — it gave up and asked the
   human for clarification instead. Root cause: my own Step 0/2 guidance
   told node-agents to expect "a few minutes" but didn't say to either use
   a long tool-timeout or a non-blocking pattern, so the model (reasonably)
   used its shell tool's ordinary timeout defaults.
5. **Fix applied** (uncommitted): rewrote
   `ansible_agdev/roles/cagent_client/files/cagent_agents_section.md` to
   recommend `cagent ask --no-wait` + separate `cagent status` polling
   instead of a single blocking call, and redistributed to agpc (small live
   write, same class of action already covered by the Step 3 approval).
6. **Second attempt** ("do you have a local LLM/Ollama service"): the
   node-agent's *first* try skipped `cagent` entirely and went straight to
   local system investigation (`ps`, `netstat`/`ss`, `curl` against a dozen
   local ports, `docker ps`, `kubectl`) — a real instruction-following miss,
   not a timeout problem. It concluded (incorrectly, from purely local
   evidence) that no LLM service existed.
7. Sent one follow-up in the same session explicitly telling it to use
   `cagent` per its own instructions. **This worked cleanly**: it ran
   `cagent ask --no-wait`, then polled `cagent status` three times over
   ~80s with increasing sleep/timeout, got a correct, grounded answer
   (`req_01bdb542a5d946b69e42111db0f19c5b`: Ollama at
   `agstudio.home.arpa:11434`, correctly noting a drift/relations
   discrepancy), and then **independently verified it itself** with a
   direct `curl` to that address before reporting back to the (simulated)
   caller with a correct, well-formatted final answer including the actual
   model list.

## The user's question: is the node-agent's model underpowered / too slow?

Raised because steps that should be simple are taking a long time compared
to the user's manual experience on the same (fast) hardware. Two distinct
things were actually observed, and they have different causes:

1. **Raw latency of the cluster-agent's own turn** (~80s for a simple
   lookup, up to ~300s timeout hit twice for the S3 question): this
   matches Phase 2's own baseline measurement (`p2/plan.md`: "Phase 2's
   real turn took ~221s, a trivial turn ~18s") — i.e., this is not a new
   regression introduced by Phase 3, it is the pre-existing, already-known
   cost of a multi-step tool-calling turn (the cluster-agent runs
   `nctl status`/`relations`/`drift`, then reasons over the output) on the
   local Ollama backend. Still slow in absolute terms, but consistent with
   what Phase 2 already measured and documented, not a Step-5-specific
   surprise.
2. **Instruction-following reliability** (skipping `cagent` on the first
   Ollama-question attempt): this is a separate axis from latency — a
   smaller/local model being inconsistent about following a written
   instruction under distraction (it had other plausible tool calls
   available and reached for those first). One explicit nudge fixed it
   immediately and cleanly, which suggests the model *can* do the right
   thing, just not with perfect reliability on the first try.

Neither observation definitively proves the model is "too weak" for this
workflow — the phase's exit criteria only need one real node-agent request
that gets useful, grounded guidance, and that has now happened twice
(S3 question, server-side; Ollama question, end-to-end including the
node-agent's own retrieval and verification). But the user's underlying
point — that this is taking noticeably longer than their own manual
experience on this hardware, and that local models have a track record of
this — is a fair one to weigh independently of whether Step 5's exit
criteria are technically met.

## Current live state (uncommitted / not cleaned up)

- `cagent-api` and the command node's cluster-agent OpenCode instance
  (port 4097) are **still running**.
- `ansible_agdev/roles/cagent_client/files/cagent_agents_section.md` has
  an **uncommitted** change (the `--no-wait`/`status` guidance rewrite),
  already redistributed live to agpc but not yet committed to git.
- Evidence on the command node now has several real requests from this
  step's testing, mixed completed/failed, all under agpc's real identity
  — nothing sensitive, no cleanup urgency.
- No `p3/report5.md` written yet; Step 5 is not finished (only one of the
  two suggested question types has a clean end-to-end node-agent-side
  proof so far; the S3 one only has a server-side proof).

## Resolution

The intended Step 5 proof was clarified after this checkpoint: a
development-assist agent must SSH to agpc and invoke the installed `cagent`
wrapper directly. It must not drive agpc's node-agent OpenCode instance as an
intermediate agent. The earlier test therefore remains useful evidence about
node-agent reliability and shared-Ollama contention, but is not the Phase 3
availability proof. The roadmap and plan were corrected accordingly; the
direct agpc proof is recorded in `report5.md` and `e2e_transcript.md`.
