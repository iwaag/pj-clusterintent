# Step 2 report — Ansible role `cagent_client`

## What was done

Added `ansible_agdev/roles/cagent_client/` (pattern-matched `opencode_agent`
for layout, kept deliberately smaller — no service, no archive pinning):

- `defaults/main.yml` — `cagent_client_api_url` (default
  `https://agstudio.local:8788`, the address agpc already dials per
  p2/report5b.md), bin/conf dir paths, poll tuning, and
  `cagent_client_ca_cert_src` pointing at the control machine's
  `.local/cagent-ca/ca_cert.pem` (three `playbook_dir` levels up from
  `playbooks/agent/`).
- `tasks/main.yml` — installs the wrapper (`files/cagent`, mode 0755) to
  `~/.local/bin/cagent`; ensures `~/.cagent/`; installs the public CA cert;
  templates `client.conf` (mode 0600). Enrollment is checked, never
  generated here (per the plan: enrollment stays the p2 Step 5b manual
  procedure) — a `stat` on `node_key.pem`/`node_cert.pem` followed by a
  `debug` warning (not a `fail`) if either is missing, naming the p2 Step
  5b procedure. Also ensures the node-agent working directory
  (`cagent_client_agent_workdir`, same default as
  `opencode_agent_workdir`, intentionally duplicated rather than
  cross-role-referenced) and installs the cluster-agent section of its
  `AGENTS.md` via `blockinfile` with an owned marker — this role owns just
  that block, not the whole file, so it can coexist with any other content
  a future role adds there.
- `files/cagent_agents_section.md` — the node-agent instructions text
  (Step 4's content, installed here since it's a static file with no
  per-node templating needed): ask-first via `cagent ask`/`continue`,
  guidance-only, no self-directed cluster changes.
- `playbooks/agent/setup_cagent_client.yml` — targets `node_agent_hosts`,
  same explicit-`--limit` requirement pattern as `setup_opencode.yml`.

Folded Step 4 (node-agent instructions) into this step's role rather than a
separate later step, since the plan left the owner/timing to the
implementer and the content is static — no reason to template/distribute
it in two separate live touches.

## Verification

- `ansible-playbook --syntax-check playbooks/agent/setup_cagent_client.yml`
  — OK.
- `ansible-playbook --check --limit agpc playbooks/agent/setup_cagent_client.yml`
  from `ansible_agdev/` — **this performs a real (read-only) SSH connection
  and fact-gathering against agpc** (Ansible's `--check` mode skips writes,
  but `gather_facts`/`stat`/`assert` always run for real; this is the same
  read-only class of action as `ansible agpc -m ping` and is what the plan
  itself directs Step 2 to run — the Step 3 pause is specifically about the
  first *write*). Result: `ok=10 changed=3 skipped=1`, no failures. The
  three simulated changes are exactly the three files this role would
  write. The enrollment-check task found agpc's real Phase 2
  `node_key.pem`/`node_cert.pem` already present and correctly skipped the
  not-enrolled warning. The CA-cert-install task reported `ok` (not
  `changed`) — agpc's existing `~/.cagent/ca_cert.pem` from its real Phase
  2 enrollment already matches the control machine's CA, confirming
  `cagent_client_ca_cert_src` resolves to the right file.
- Did not run `devtests/test_strategy/test_ansible_conformance.py`: that
  gate owns the inventory-trust/SSH-host-key-alias boundary
  (`nctl_core.inventory_trust`/`ssh_trust`), which this role's addition
  does not touch — no inventory generation or SSH trust logic changed,
  only a new role/playbook using the existing, unmodified SSH config.

## Deviations from the plan

Folded Step 4's content into this step (noted above); otherwise none.

## State

No test suite changes this step (Ansible-only). No live write performed —
`--check` only. Target set for Step 3 realistically remains **agpc**
(reachable, already enrolled); agbach/agdnsmasq stay unreachable as
expected, matching the plan's noted known state.

## Next

Step 3 — distribute for real (**LIVE, needs user approval** before the
first Ansible write against agpc).
