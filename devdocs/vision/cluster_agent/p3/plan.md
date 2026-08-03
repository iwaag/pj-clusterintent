# cluster_agent Phase 3 Plan: distribution + first use-case proof

References: [roadmap.md](../roadmap.md), [refined_idea.txt](../refined_idea.txt),
[p1/contract.md](../p1/contract.md), [p2/contract.md](../p2/contract.md),
[p2/report5b.md](../p2/report5b.md), [p2/e2e_transcript.md](../p2/e2e_transcript.md)

## Goal

Distribute a thin curl wrapper to the target nodes via an Ansible role, teach
the node-agent how to call the cluster-agent, and prove the first real use
case: a node-agent on a real node asks a resource question ("I want
S3-compatible storage" style) through the wrapper and receives useful
guidance, preserved as evidence.

## Exit criteria (from the roadmap, restated)

1. The wrapper is distributed to the target nodes by an Ansible role (fixed
   URL + TLS settings baked in as role configuration).
2. At least one node-agent sends a resource question through the wrapper and
   receives useful guidance back.
3. The example is preserved as evidence (cagent evidence on the command node
   plus a transcript in this directory).

## Scope and freedom

Experimental cluster, breaking-change phase. No API/contract change is
expected this phase (the wrapper is a client of the frozen p1+p2 contract),
but if a small contract adjustment turns out to be genuinely useful for the
wrapper, break it freely and update `p2/contract.md`'s successor accordingly.

Only the three roadmap-wide prohibitions apply:

1. Responses remain reads + plan presentation only. Nothing in this phase
   gives a node-agent any mutation path — the wrapper is read/ask only.
2. OpenCode instances stay on 127.0.0.1 (both the cluster-agent's and each
   node-agent's). The only LAN/VPN surface remains the mTLS cagent API.
3. No secrets in Git, binaries, or evidence. The wrapper script contains no
   tokens or keys — it only *references* the per-node key/cert paths that
   Phase 2 already placed. Node private keys never leave their node.

Everything else — wrapper name, argument syntax, config resolution, role
layout, whether enrollment gets any automation — is the implementer's
choice, recorded in the report. **Do not build the Go CLI** (roadmap: only
if the wrapper proves insufficient, and that complaint has not appeared).

## Steps

House style: one step at a time, `p3/reportN.md` + one commit per step.
Steps 0–2 touch only the command node and are approval-free. **Step 3 is the
first Ansible/SSH action against agpc — pause for user approval there.**
Steps 3–5 are live but low-risk (file placement + read-only requests).

### Step 0 — Wrapper interface decision + local prototype

Decide and write down (in the report, not a separate contract doc — this is
a client, not an API):

- **Command surface, kept minimal** (roadmap requirement — minimize what the
  node-agent prompt must be taught). Suggested:
  - `cagent ask` — new request; body text from stdin; prints the JSON
    response (request ID + session ID).
  - `cagent continue <session_id>` — follow-up turn, body from stdin.
  - `cagent status <request_id>` — one status/response fetch.
  - Strongly consider a `--wait` flag (or make waiting the default for
    `ask`/`continue`) that polls until a terminal state and prints the final
    response text. Phase 2's real turn took **~221 s** — a node-agent that
    has to hand-roll a polling loop will get it wrong or time out; putting
    the loop in the wrapper is the single highest-value convenience here.
    Poll every few seconds, no overall timeout (or a generous one, ≥10 min).
- **Config resolution**: URL, CA cert, client cert/key paths. Suggested: a
  tiny `~/.cagent/client.conf` (shell-sourceable or plain KEY=VALUE)
  written by the Ansible role, so the script itself is identical on every
  node and contains no per-node values. Phase 2 already established
  `~/.cagent/{node_key.pem,node_cert.pem,ca_cert.pem}` on agpc — reuse that
  directory and those names as the defaults.
- **Language**: POSIX sh (agpc is Linux; a future macOS node should not
  break). Depend only on `curl`. **Avoid a hard jq dependency** — jq is not
  confirmed present on the nodes; either parse the few needed fields with
  grep/sed (the API's JSON is single-object and predictable), or check for
  jq and degrade to raw-JSON output. Raw JSON output is acceptable: the
  consumer is an agent, and agents read JSON fine.
- Body hygiene: always `--data @file` or `--data @-` (stdin), never inline
  argv (roadmap rule, already followed in Phase 2).
- Prototype it on the command node against the live stack (start
  `./cagent/opencode/start.sh` + `cagent-api`; the command node can use the
  server cert's `agstudio.local` SAN, or enroll the command node itself as
  a client if convenient — implementer's choice; a throwaway ledger entry
  is fine and can be revoked after).

Deliverable: the wrapper script committed (suggested home:
`ansible_agdev/roles/cagent_client/files/cagent`) + report0 with the
decided interface.

### Step 1 — Automated test for the wrapper

One real-TLS test, cheap by reuse: `devtests/test_strategy/`'s existing
mTLS conformance test (`test_mtls_conformance.py`) already builds a
throwaway CA, ledger, and a real loopback `cagent-api` with a fake OpenCode.
Add a test module (or extend that one) that drives the **actual wrapper
script** against that fixture: `ask` (with wait) → useful response text on
stdout, exit 0; `status` of the created request; a revoked-cert call →
non-zero exit + the forbidden envelope visible. That covers the wrapper's
whole job — TLS args, body-from-stdin, polling, error surfacing — with no
mock-only TLS (README_DEV lesson 2) and no live node.

Add/extend the README_DEV command-matrix row if this lands as a new gate
file; if it extends the existing mTLS gate, just note the new case count.

### Step 2 — Ansible role `cagent_client`

A small role in `ansible_agdev/roles/` (pattern-match `opencode_agent` for
layout, but this one is much simpler — no service, no archive pinning):

- Install the wrapper to `~/.local/bin/cagent` (mode 0755).
- Ensure `~/.cagent/` exists; install `ca_cert.pem` (public — fine to keep
  a copy in the role's `files/` or copy from `.local/cagent-ca/ca_cert.pem`
  on the control machine) and template `client.conf` with the role vars.
- Role defaults: `cagent_api_url: "https://agstudio.local:8788"` (the URL
  agpc actually dialed in Phase 2; the server cert's SANs are
  `agstudio.local` + `192.168.0.100`, so both work), key/cert paths.
- **Do not generate keys or sign certs in the role.** Enrollment (key+CSR
  on the node → sign bound to the DesiredNode UUID → register in ledger)
  stays the Phase 2 manual procedure; it is a per-node trust decision, and
  automating it is not needed while there is exactly one enrolled node. The
  role should instead *check* for `node_key.pem`/`node_cert.pem` and emit a
  clear "node not enrolled — see p2/plan.md Step 5b" message (warn or fail,
  implementer's choice) rather than silently installing a wrapper that
  can't authenticate.
- A playbook `playbooks/agent/setup_cagent_client.yml` targeting the
  node-agent hosts. Run `ansible-playbook --check`/`--syntax-check` locally;
  run the Ansible conformance gate if the change touches anything the gate
  owns.

Target set: the inventory's four nodes minus the known-unreachable ones.
**agbach/agdnsmasq being unreachable is expected** — limit the play (or
accept unreachable-host failures as the known state) and say so in the
report; do not treat it as a phase blocker. Realistically this phase
distributes to **agpc** (and optionally the command node itself).

### Step 3 — Distribute (LIVE — needs approval)

**Pause for user approval before the first Ansible action against agpc.**
Then run the Step 2 playbook from `ansible_agdev/` (its `ansible.cfg`
supplies the pinned SSH key and inventory — running from elsewhere silently
drops that config, README_DEV note).

Verify from agpc's vantage point, not just play success (README_DEV
lesson 1): with the cluster-agent stack running on the command node, an
ad-hoc `ansible agpc -m command -a "cagent status <old-request-id>"` (or an
`ask` with a trivial question) must return real API output through the
installed wrapper + installed conf. agpc's existing enrollment from Phase 2
(key/cert/CA under `~/.cagent/`, ledger state `active`, DesiredNode UUID
`c82421c3-c42a-4bea-91ce-7468ae8a249c`) should make this work with zero new
trust decisions.

### Step 4 — Node-agent instructions

Teach the node-agent to use the wrapper. The node-agent on agpc is the
`opencode_agent` role's OpenCode service (loopback :4096, workdir
`~/agent-work`). OpenCode reads `AGENTS.md` from its working directory, so
the natural mechanism is an `AGENTS.md` (or a cluster-agent section appended
to it) templated by a role — either a new task in `opencode_agent` or in
`cagent_client`; implementer's choice, but keep one owner for the file.

Content guidance — keep it short, the wrapper already minimized the surface:

- When you need a cluster resource or service (storage, database, DNS, a
  port, "does X exist here"), do not guess or install your own — ask the
  cluster-agent: `echo "question" | cagent ask` (waits, prints the answer).
- Follow up with `cagent continue <session_id>`.
- Answers are guidance only; the cluster-agent will not change the cluster
  for you, and you must not attempt cluster changes yourself.

Distribute via the same play (this is a second small live touch on agpc —
covered by the Step 3 approval unless the user said otherwise).

### Step 5 — First use-case proof (LIVE)

The exit-criteria run. With the cluster-agent stack up on the command node:

1. Drive the **real node-agent** on agpc — not a human typing curl — into
   asking the question. Practical method: talk to agpc's node-agent OpenCode
   instance over SSH-forwarded loopback (or `ansible ... -m uri` against
   127.0.0.1:4096 from agpc itself; the p1 research notes
   [p1/opencode_api_notes.md](../p1/opencode_api_notes.md) document the
   session API) and prompt it with a task that requires cluster knowledge,
   e.g. "You need S3-compatible storage for a job. Find out what this
   cluster offers before doing anything." The node-agent should, per its
   Step 4 instructions, run `cagent ask` itself.
2. Confirm the guidance is *useful*: grounded in actual cluster state, i.e.
   consistent with what `nctl relations --json` / `nctl drift` say (the
   cluster-agent's own OpenCode already runs in the superproject and can run
   those commands — Phase 2's answer correctly reported no S3-compatible
   storage exists, so either that same negative-but-grounded answer or a
   question about a service that *does* exist, e.g. DNS or the Ollama
   service relation, both count; asking one of each makes a stronger report).
3. Preserve evidence: `cagent-evidence list`/`show` on the command node must
   show the request with agpc's UUID/serial identity; save the full exchange
   (node-agent prompt → its wrapper call → cluster-agent answer) as
   `p3/e2e_transcript.md`.
4. Stop the manually-started processes when done (house pattern from p1/p2);
   agpc keeps the wrapper, conf, and instructions — that is the phase's
   exit state.

## Useful facts collected at planning time

- **API endpoints** (frozen, p1/contract.md): `POST /requests`,
  `POST /sessions/{sid}/requests`, `GET /requests/{rid}`,
  `POST /requests/{rid}/cancel`, `GET /sessions`,
  `GET /sessions/{sid}/requests`. Async: create returns `202 queued`,
  client polls. The wrapper only needs the first three.
- **Stack start** (manual, no supervision — unchanged since p1):
  `./cagent/opencode/start.sh`, then `uv run --project cagent cagent-api`.
  Env vars in `cagent/README.md`. There is no plaintext mode; every request
  needs the client cert.
- **agpc is already enrolled and active**: key/cert/CA at
  `~/.cagent/node_key.pem` / `node_cert.pem` / `ca_cert.pem`, UUID
  `c82421c3-c42a-4bea-91ce-7468ae8a249c`, dialing
  `https://agstudio.local:8788`. Phase 2 ended with the ledger entry
  reactivated and working. The wrapper defaults should simply match these
  paths so Step 3 needs no re-enrollment.
- **Turn latency is real**: the Phase 2 multi-step tool-calling turn took
  ~221 s; a trivial turn ~18 s. Design the wrapper's wait loop and any
  node-agent-side timeouts around minutes, not seconds.
- **Known node state**: agpc + agstudio reachable; agbach/agdnsmasq
  unresponsive is long-standing and expected. agstudio is the command node.
- **Run Ansible from `ansible_agdev/`** (or `ANSIBLE_CONFIG=...`): its
  `ansible.cfg` carries the SSH key, known-hosts and inventory defaults; an
  inventory path alone does not (README_DEV).
- **`nctl relations --json`** is the intended guidance material and is
  computed fresh on every call — nothing to precompute or cache for the
  cluster-agent; if its answers feel ungrounded, the cheapest fix is a line
  in the *cluster-agent's* own instructions telling it to run
  `nctl relations --json` / `nctl drift --json` before answering resource
  questions (that file is on the command node, no distribution needed).
- **mTLS conformance fixture** (`devtests/test_strategy/
  test_mtls_conformance.py`) already builds throwaway CA/ledger/server —
  Step 1 should reuse it rather than building a second TLS harness.
- The `opencode_agent` role is the closest in-repo pattern for Step 2's
  role, but note it does much more (pinned binary, service units); the
  cagent_client role should stay at "copy three small files".

## Out of scope for Phase 3

Go CLI, human/smartphone entrance and its auth (Phase 4), SSE, mutation or
approval flows, enrollment automation / key rotation, rate limits, session
TTLs, workspace-level identity, and re-enrolling or newly enrolling any node
beyond what Step 3's distribution needs (none, if agpc's Phase 2 material is
intact).
