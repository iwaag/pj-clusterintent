# Step 3 report — Distribute (LIVE)

## What was done

User approval obtained (AskUserQuestion) before the first Ansible write
against agpc, per the plan's pause point.

1. `ansible-playbook --limit agpc playbooks/agent/setup_cagent_client.yml`
   from `ansible_agdev/` (pinned SSH key/inventory via its `ansible.cfg`).
   `ok=10 changed=3 skipped=1`, no failures — identical shape to Step 2's
   `--check` dry run, now for real.
2. Verified from agpc's own vantage point (not just play success,
   README_DEV lesson 1):
   - `~/.cagent/client.conf` matches the templated defaults
     (`CAGENT_API_URL=https://agstudio.local:8788`, correct cert/key
     paths, poll tuning).
   - `~/.local/bin/cagent` installed, mode `0755`.
   - `~/agent-work/AGENTS.md` has the `cagent_client`-marked cluster-agent
     block appended.
   - The enrollment-check task found agpc's real Phase 2 key/cert already
     present and skipped the not-enrolled warning, as expected — no new
     trust decision was needed.
3. Started the cluster-agent stack on the command node
   (`./cagent/opencode/start.sh`, then `CAGENT_API_HOST=0.0.0.0 cagent-api`
   — moved off loopback so agpc can reach it, matching Phase 2).
4. Ran the installed wrapper **from agpc itself** over the same
   `ansible_agdev/` ad-hoc path (`ansible agpc -m shell -a 'echo "..." |
   /home/eiji/.local/bin/cagent ask'` — needed `-m shell`, not `-m command`,
   since `command` doesn't interpret the pipe): a trivial question,
   `202` → polled to `completed` in a few seconds, correct answer ("2"),
   using agpc's existing Phase 2 enrollment with zero new trust decisions,
   exactly as the plan anticipated.

## Deviations from the plan

None. `-m shell` vs `-m command` for the ad-hoc verification is an
Ansible mechanics detail, not a deviation from anything the plan specified.

## State

`cagent-api` and the command node's cluster-agent OpenCode instance are
**left running** (needed for Step 5's live use-case proof, which follows
directly). agpc now permanently retains the wrapper, config, and
AGENTS.md section — this is the phase's intended exit state, not a
leftover to clean up.

## Next

Step 5 — drive the real node-agent on agpc (not a human typing curl) to
ask a cluster-resource question through its own OpenCode instance, and
preserve the exchange as `p3/e2e_transcript.md`.
