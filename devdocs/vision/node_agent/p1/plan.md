# Node Agent — Phase 1 Implementation Plan: Single-Node Technology Spike

Status: planned.

This is a spike, not a framework. The goal is to prove, on one real node, that a
controller-side terminal can open and resume a useful local coding-agent
session without an interactive SSH shell, and to record what was learned. Code
quality, packaging, Ansible roles, and nctl integration are explicitly later
phases. Manual installation, ad-hoc configuration, and throwaway scripts are
all acceptable here.

## 1. Goal

At the end of Phase 1, from this controller PC:

```bash
<some documented command>   # e.g. the runtime's remote TUI client
```

opens an interactive agent session running as `eiji` on the target node, backed
by an Ollama-hosted tool-capable model, and the session can read/write/edit
files, run shell commands, be resumed, be cancelled, and survive a service
restart.

The durable output is knowledge: a findings report that Phase 2 (Ansible role)
and Phase 3 (nctl entry point) can be designed from directly.

## 2. Target environment

- **Target node:** `agstudio.local` (reachable, per `.local/localenv_memo.md`).
  Fall back to `agpc.local` if agstudio turns out to be unsuitable.
- **User:** `eiji`, via `~/.ssh/ansible_key` (confirm with the user before the
  first SSH, per the localenv memo; after that, routine SSH to the chosen spike
  node is approved for the rest of the phase).
- **Ollama:** already running at `http://agstudio.local:11434` (v0.31.1,
  verified 2026-07-31 with a successful tool-call round trip). Installed
  models include `qwen3.6:35b-a3b-coding-nvfp4` (the expected starting
  choice), `glm-4.7-flash`, `qwen3-vl`, `gemma3`, and `llava`. Use this
  endpoint; standing up a different one is only needed if it proves
  inadequate.
- **Working directory on the node:** implementer's choice; something like
  `~/agent-work/` is fine. Record it.

## 3. Scope of authority

This phase may freely, without further approval:

- SSH to the chosen spike node as `eiji` and install/remove packages,
  binaries, systemd user units, and configuration there;
- install and run Ollama and pull models on the chosen Ollama host;
- create, modify, and delete files under the chosen working directory;
- start, stop, and restart the spike services repeatedly.

Only these boundaries are mandatory (from the roadmap's minimum guardrails):

- do not commit or print credentials, tokens, SSH keys, or vault passwords;
- do not expose an unauthenticated shell-capable service beyond the LAN
  (binding to the LAN or localhost + SSH tunnel is fine; pick whichever is
  fastest and note it);
- do not touch nodes other than the chosen spike node;
- leave SSH/Ansible access intact as the recovery path.

Everything else — sandboxing, dedicated users, resource limits, TLS — is out of
scope and should not be built in this phase.

## 4. Steps

Follow the usual phase execution style: one short report note and commit per
step, but the reports here can be a few paragraphs each; this is a spike log,
not a contract document. Keep them in `devdocs/vision/node_agent/p1/`.

### Step 0 — Pick the runtime and the model (desk work)

- Survey the current state of OpenCode Server (leading candidate), Goose, Pi,
  and anything newer that fits: remote interactive sessions, session
  resume, Ollama/OpenAI-compatible backend support, single-binary or simple
  install.
- Pick one runtime and one tool-capable Ollama model to start with (context
  size and tool-calling reliability matter more than benchmark scores; a
  Qwen3-class or similar instruct model in the size the Ollama host can serve
  is the expected shape).
- Record the choice and the one-line reason. Do not write a comparison matrix;
  if the first choice fails in Step 2, switching is cheap and is itself a
  useful finding.

### Step 1 — Verify the Ollama endpoint (mostly done)

Already verified 2026-07-31 from the controller PC: `agstudio.local:11434`
answers, and `qwen3.6:35b-a3b-coding-nvfp4` completed a tool-call round trip
(correct function name and arguments; ~8 s total including model load,
~95 tok/s eval). Remaining work is only to pull a different model if Step 3
shows this one is inadequate.

### Step 2 — Install and launch the runtime on the node

- SSH to the spike node (user confirmation on first access), install the
  chosen runtime at a pinned version, point it at the Ollama endpoint, set the
  working directory, and launch it — foreground first, then as a systemd user
  service (or whatever the runtime's natural daemon shape is).
- Record the exact install commands, version, launch command, config file
  shape, and listen address. Exact commands matter here because Phase 2
  translates them into an Ansible role.

### Step 3 — Prove the interaction loop

From the controller PC, using the runtime's own remote client, verify and note
the result of each:

1. attach to a new interactive session;
2. have the agent read, write, and edit a file in the working directory;
3. have the agent run shell commands and observe output;
4. detach and re-attach to the same session with context intact;
5. cancel/interrupt a running generation;
6. restart the runtime service, then confirm old sessions are either resumable
   or cleanly listed as lost (either is acceptable — record which);
7. note terminal behavior: resize, colors, Ctrl-C passthrough, exit status.

A small real task (e.g. "summarize this directory and write NOTES.md") is a
better probe than synthetic checks. If a check fails, first try model or
config changes; switch runtimes only if the failure is architectural, and
record why.

### Step 4 — Findings report

Write `devdocs/vision/node_agent/p1/report.md` covering:

- selected runtime, pinned version, install and launch commands, config shape;
- Ollama placement, model, and observed quality/latency;
- results of each Step 3 check, including quirks and limitations;
- the attach command an operator uses today (this becomes the thing
  `nctl agent attach` wraps in Phase 3);
- what the Phase 2 Ansible role must install, template, and enable;
- anything that argues for changing the roadmap's assumptions.

## 5. Completion criteria

Phase 1 is complete when:

- all seven Step 3 checks have been attempted and their results recorded
  (individual failures with a recorded workaround or limitation do not block
  completion — an honest "resume does not survive restart" is a valid
  finding);
- the controller PC can open and resume a useful agent session on the spike
  node without an interactive SSH shell;
- `report.md` exists with the content above.

If the spike concludes that no candidate runtime is workable, that is also a
valid completion: record the evidence and the recommended alternative
(e.g. a small custom adapter) instead of forcing a broken choice into Phase 2.
