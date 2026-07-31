# Node Agent — Phase 2 Plan: Repeatable Ansible Deployment

Status: not started.
Input: [Phase 1 findings](../p1/report.md), [roadmap Phase 2](../roadmap.md).

## Goal

Turn the Phase 1 manual OpenCode install on `agstudio.local` into an
idempotent `ansible_agdev` role and playbook that can install, upgrade,
restart, and health-check the agent service, and prove it by deploying the
same playbook to a second node (`agpc.local`) without manual setup.

## Scope and decisions

- Runtime: **OpenCode, pinned `v1.18.10`**, per-architecture release archive
  verified by SHA-256 (the darwin-arm64 digest is in the Phase 1 report;
  fetch and record digests for the Linux arch(es) actually deployed).
- Service manager: `launchd` user LaunchAgent on macOS (`agstudio`),
  systemd **user** unit + `loginctl enable-linger` on Linux (`agpc`).
  Same command in both: `opencode serve --hostname {{ listen }} --port {{ port }}`
  with the templated working directory.
- Bind loopback (`127.0.0.1:4096`) by default; access stays SSH local
  forwarding as in Phase 1. LAN binding is out of scope for this phase.
- Run as the inventory operational user (`eiji`). No dedicated Unix user,
  no sandboxing — this is the experimental posture the roadmap accepts.
- Ollama endpoint and default model are **role variables**, not hard-coded.
  Defaults: `http://127.0.0.1:11434/v1`, `qwen3.6:35b-a3b-coding-nvfp4`.
  `agpc` has no local Ollama; its host_var points at agstudio's endpoint
  (making agstudio's Ollama LAN-reachable is a small approval-gated side
  task inside Step 4 — or the implementer may choose an SSH tunnel instead).
- Out of scope: nctl integration (Phase 3), reconcile/intent integration
  (Phase 4), authentication beyond the loopback+SSH posture, multi-runtime
  abstraction.

## Minimum prohibitions (everything else is implementer's discretion)

1. No credentials, tokens, or key material committed or printed.
2. The agent HTTP port must not listen on a non-loopback address without an
   explicit separate decision.
3. Keep SSH/Ansible as the working recovery path (don't break the existing
   login or launchd/systemd session of `eiji` on a target).
4. Pin the OpenCode version and verify the archive digest before install.

## Deliverables

```text
ansible_agdev/roles/opencode_agent/
  defaults/main.yml        # version, arch->sha256 map, port, workdir, ollama url, model
  tasks/main.yml           # download+verify+install, config, service, health
  tasks/service_darwin.yml # plist template, bootstrap-or-kickstart
  tasks/service_linux.yml  # user unit template, linger, daemon-reload, restart
  templates/opencode.json.j2
  templates/com.clusterintent.opencode.agent.plist.j2
  templates/opencode-agent.service.j2
ansible_agdev/playbooks/agent/setup_opencode.yml   # hosts: agent_nodes (or --limit)
devdocs/vision/node_agent/p2/report.md
```

## Steps

Follow the usual style: one report section + commit per step; pause for
user approval before each live step (4 and 5).

### Step 1 — Role and playbook implementation (local only)

- Write the role per the Phase 1 report's "Implications for Phase 2":
  staged download to a temp dir, `shasum -a 256 -c` (or `sha256sum`) against
  the pinned digest, `install -m 0755` to `~/.local/bin/opencode`, templated
  `~/.config/opencode/opencode.json`, work dir creation, OS-specific service
  install, then a health `GET http://127.0.0.1:{{ port }}/doc` (uri module,
  retries) on the node.
- Upgrade semantics: compare `opencode --version` output to the pinned
  version; reinstall and restart only on mismatch or changed config/unit
  template (use handlers). Second run must report zero changes.
- macOS caveat from Phase 1: `launchctl bootstrap gui/UID` can fail over SSH
  when the job is already loaded — treat "already bootstrapped" as success
  and use `launchctl kickstart -k` for restarts. Handle this pragmatically;
  it does not need to be elegant.

### Step 2 — Static verification

- `ansible-playbook --syntax-check` from `ansible_agdev/` (its `ansible.cfg`
  supplies key/vault/inventory) and, if available, `ansible-lint` on the new
  role. No conformance gates are triggered: this adds a role, it does not
  change the SSH/inventory boundary.

### Step 3 — Dry review

- Run the playbook with `--check --diff --limit agstudio.local` as an
  optional diagnostic (per the dry-run policy this is not a required plan
  boundary; skip it if check mode fights the download/launchctl tasks and
  say so in the report).

### Step 4 — Live deploy to agstudio (approval required)

- Run against `agstudio.local`. The node already has the manual Phase 1
  install; the role must **adopt** it: converge config/plist/binary to the
  templated versions, restart, and pass the health check. Existing sessions
  in `~/agent-work` must survive (verify by attaching to the Phase 1 session
  through the SSH tunnel afterward).
- Re-run immediately: expect `changed=0` (idempotency proof).

### Step 5 — Live deploy to agpc, second-node proof (approval required)

- Decide the Ollama route for agpc (agstudio LAN endpoint recommended),
  apply any needed agstudio-side Ollama binding change, then run the same
  playbook with `--limit agpc.local` on a node with zero prior setup.
- Acceptance = the roadmap's completion criterion: from the controller,
  tunnel to agpc and get a working interactive `opencode attach` session
  (model responds, file write + shell probe in the work dir), plus a passing
  role health check and an idempotent second run.
- If agpc's CPU-only inference is unusably slow, record it as a finding —
  it does not fail the phase; the deployment mechanism is what Phase 2 proves.

### Step 6 — Report and close

- `p2/report.md`: pinned versions/digests, variable defaults, per-OS service
  facts, health/idempotency/attach evidence, limitations carried to Phase 3
  (notably the Ctrl-C vs interrupt-API finding from Phase 1).
- Commit in `ansible_agdev`, bump the submodule pointer, update the roadmap
  status line.

## Completion criteria

- One playbook deploys or repairs the agent on both agstudio (adopted) and
  agpc (fresh) with no manual node setup.
- Health check passes on both; second run changes nothing.
- Controller-side interactive attach works on both nodes.
