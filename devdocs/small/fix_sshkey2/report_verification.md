# Report — Documentation and automated verification

Date: 2026-07-22
Scope: `nctl` (submodule), root `devdocs/`
Status: **documentation and automated verification complete**. Live
verification A (non-default-port OpenSSH lookup) and Live verification B
(post-regeneration service/dnsmasq action) are **not yet run** — both touch
real infrastructure or a real SSH connection and are paused for explicit
operator confirmation per this project's execution convention. See
"Live verification status" below.

## Documentation

- `nctl/README.md` ("SSH trust configuration" section): documented that
  `known_hosts_file`/`lock_path` resolve relative to `nctl.toml`'s own
  directory (not the process cwd); that the managed store's key is always
  the bare alias independent of `ansible_port` (only legacy known_hosts
  promotion ever uses a port-qualified `[host]:port` name, and only for its
  own search); that `nctl apply dnsmasq`'s trust gate now covers the
  configured default inventory exactly like `--inventory`, in dry-run
  exactly like `--yes`, and includes an actual offered-key scan, not just a
  variable-presence check; and that `nctl reconcile --yes` binds its
  post-regeneration scan to the exact generation it just regenerated,
  failing closed instead of falling back to mDNS when a production route
  cannot be resolved.
- `ansible_agdev/README.md`, `ansible_agdev/README_ADMIN.md`: reviewed: both
  describe the SSH trust design at a level (`nctl ssh enroll` lifecycle,
  `HostKeyAlias`, "see `nctl/README.md` for full detail") that fix_sshkey2
  does not change, so no edit was needed.
- No separate "production inventory contract" doc exists beyond
  `nctl/src/nctl_core/production/contract.py` and its tests; not applicable.
- `devdocs/small/fix_sshkey/report_verification.md`: added a notice
  preserving all original facts/operation IDs/fingerprints unedited, marking
  that Step 7's live `--yes` round only ran `reconcile_ipam` (`ssh_preflight`
  was an empty list) and that the post-regeneration service/dnsmasq SSH path
  was not exercised there — that gap is what this document's Live
  verification B (once run) closes.

## Automated verification

```
$ uv run --project nctl pytest -q nctl/tests/test_ssh_trust.py nctl/tests/test_config.py
61 passed in 0.10s

$ uv run --project nctl pytest -q nctl/tests/test_ssh_enroll.py nctl/tests/test_ssh_preflight.py
46 passed in 0.30s

$ uv run --project nctl pytest -q nctl/tests/test_production_contract.py nctl/tests/test_production_composer.py nctl/tests/test_production_render.py
70 passed in 0.14s

$ uv run --project nctl pytest -q nctl/tests/test_dnsmasq_apply.py nctl/tests/test_reconcile_executor.py
50 passed in 0.39s

$ uv run --project nctl pytest -q nctl/tests
871 passed, 1 warning in 5.66s
```

Lint/type check: `ruff`/`mypy` are not installed and not listed in
`nctl/pyproject.toml`'s `[dependency-groups] dev`, so neither was run (same
as every prior step's report in this plan).

### Inventory generation and `ansible-inventory` validation against live Nautobot

With the local Nautobot instance running (`http://localhost:8000`,
containers `nautobot-nautobot-1`/`-worker-1`/`-scheduler-1`) and the token
from `.local/localenv_memo.md`:

```
$ nctl render hosts-intent --out ansible_agdev/inventories/generated
total_nodes: 5, exported_hosts: 5, skipped_nodes: 0, groups: [dnsmasq_server, ssh_hosts]

$ nctl render production --out ansible_agdev/inventories/generated
eligible: 3, included: 2, skipped: 1, out_of_scope: 2, placements: 1, active_placements: 1
```

- `ansible-inventory -i inventories/generated/hosts_intent.yml --list` and
  `-i inventories/generated/production.yml --list` both parsed as valid
  JSON.
- `dnsmasq_server` group: `["agdnsmasq"]` in both inventories.
  `ssh_hosts`: 5 hosts in bootstrap, 2 in production (`agdnsmasq`, `agpc`) —
  membership differs by design (production scope is narrower), not a defect.
- `ansible-inventory --host agdnsmasq` on both inventories: `nctl_ssh_host_key_alias`
  and `ansible_ssh_common_args` are byte-identical
  (`-o HostKeyAlias=nctl-node-27818c12-fe15-4c9f-83d0-7949523f6c33 -o
  UserKnownHostsFile=<absolute path> -o StrictHostKeyChecking=yes -o
  CheckHostIP=no -o UpdateHostKeys=no`) while the route differs: bootstrap's
  `ansible_host` is the literal `agdnsmasq.local`; production's is a
  `group_vars/all.yml` Jinja template that `ansible-inventory` reports
  unrendered (see the Step 4 fixup below).
- The real managed known_hosts store (`~/.local/state/nctl/ssh/known_hosts`,
  from the prior `fix_sshkey` live enrollment) is untouched: still exactly 3
  lines, all under the `nctl-node-27818c12-...` alias, no `[alias]:port` or
  IP/DNS-keyed entries.

### A real bug found live: unrendered Jinja `ansible_host`

Running `nctl apply dnsmasq --json` (dry-run) against the freshly rendered
production inventory initially **failed** with:

```
ssh-keyscan failed for {{
  tailscale_ip | default(local_connection_host, true)
  if connection_path == 'tailscale'
  else local_connection_host
}}:22: getaddrinfo {{: nodename nor servname provided, or not known
```

`ansible-inventory --host` reports every production host's `ansible_host`
as inherited from `group_vars/all.yml`'s Jinja template, *unrendered* --
`ansible-inventory` does not template variables. `inventory_trust.py`'s
route resolver treated that literal string as a real target. Fixed (see
`nctl` commit `7a2cdd7`, "fix_sshkey2 Step 4 fixup"): a per-host
`ansible_host` is only used verbatim when it contains no `{{`; otherwise
route resolution falls through to the `connection_path`/`local_ip`/
`local_dns_hostname`/`mdns_hostname`/`tailscale_ip` chain, which nctl *does*
export as literal per-host values. Added both a unit-level regression
(`nctl/tests/test_inventory_trust.py`) and a `dnsmasq_apply`-level one.

Re-running after the fix:

```
$ nctl apply dnsmasq --json   # configured production inventory
ssh_preflight: [{"slug": "agdnsmasq", "alias": "nctl-node-27818c12-...", "status": "ready", "detail": ""}]
mode: dry-run, setup exit_code: 0, ansible exit_code: 0, errors: []

$ nctl apply dnsmasq --inventory ansible_agdev/inventories/generated/hosts_intent.yml --json
ssh_preflight: [{"slug": "agdnsmasq", "alias": "nctl-node-27818c12-...", "status": "ready", "detail": ""}]
```

Both the configured production inventory and the bootstrap `--inventory`
override pass the full trust contract and offered-key preflight and
complete a real dry-run (`--check --diff`) end to end against
`agdnsmasq`, with zero writes to the managed known_hosts store (verified by
file content/line count before and after).

## Live verification status

- **Live verification A** (non-default-port OpenSSH lookup, temporary
  localhost port-forward to `agdnsmasq:22`) — not yet run.
- **Live verification B** (a real `service_profile`/`dnsmasq_config` action
  after production regeneration via `nctl reconcile agdnsmasq --yes`,
  including the disposable-empty-store and mismatch-fixture negative cases)
  — not yet run.

Both require either a temporary SSH port-forward against the real
`agdnsmasq` host or a real (small, reversible) desired-state change followed
by `nctl reconcile --yes` actuating Ansible against it — per this session's
established execution convention, these are paused for explicit operator
confirmation before proceeding, rather than run automatically.
