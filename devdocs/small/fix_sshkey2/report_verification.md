# Report — Documentation and automated verification

> Superseded for the previously blocked Live verification B by
> [`fix_sshkey3`](../fix_sshkey3/report_verification.md). This report preserves
> the original attempt, operation IDs, and facts unchanged: its safe fixture
> exposed the real dnsmasq content-convergence gap that `fix_sshkey3` closes.

Date: 2026-07-22
Scope: `nctl` (submodule), root `devdocs/`
Status: Documentation and automated verification **complete**. Live
verification A (non-default-port OpenSSH lookup) **complete**. Live
verification B (post-regeneration service/dnsmasq action) **attempted, not
completed** — blocked by a structural property of the reconciliation drift
model unrelated to fix_sshkey2's own changes; all live state was restored
and confirmed converged. See "Live verification status" below.

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

## Live verification A — OpenSSH lookup on a non-default port

Date: 2026-07-22. Target: real `agdnsmasq`. No permanent host configuration
was changed.

1. A temporary `ssh -i ~/.ssh/ansible_key -L 127.0.0.1:12222:localhost:22
   eiji@agdnsmasq.local -N -f` port-forward was started: local port `12222`
   tunnels through an ordinary SSH connection to `agdnsmasq` into `agdnsmasq`'s
   own `localhost:22`, i.e. its real sshd, presenting its real host key --
   without touching `agdnsmasq`'s sshd configuration at all.
2. A disposable known_hosts file was built containing only
   `nctl-node-27818c12-fe15-4c9f-83d0-7949523f6c33 ssh-ed25519 <the same
   already-trusted blob from the real managed store>` (bare alias, no
   endpoint name, no port).
3. `ssh -p 12222 -o HostKeyAlias=nctl-node-27818c12-fe15-4c9f-83d0-7949523f6c33
   -o UserKnownHostsFile=<disposable bare file> -o StrictHostKeyChecking=yes
   -o CheckHostIP=no -o UpdateHostKeys=no eiji@127.0.0.1` **succeeded**
   (`bare-alias-non-default-port-OK`) -- confirming OpenSSH itself looks up
   the bare alias regardless of the non-default connection port, exactly the
   `ssh_config(5)` `HostKeyAlias` behavior fix_sshkey2 Step 1 fixed nctl's
   lookup helpers to match.
4. The same command against a disposable file containing only the obsolete,
   pre-fix_sshkey2 `[nctl-node-27818c12-...]:12222 ssh-ed25519 <same blob>`
   form **failed** (`No ED25519 host key is known for nctl-node-...`, exit
   255) -- confirming the bracketed form is not what a real non-default-port
   connection looks up, so a store containing only that form is correctly
   treated as unenrolled.
5. `nctl`'s own real functions (not just the `ssh` CLI) were exercised
   directly against the tunnel, with no Nautobot mutation: `ssh_trust.managed_lookup_name`
   confirmed the bare, port-independent lookup name;
   `ssh_enroll.default_ssh_probe_runner()` + `scan_offered_keys(probe,
   "127.0.0.1", 12222, ...)` scanned the real offered keys
   (`ssh-rsa`/`ecdsa-sha2-nistp256`/`ssh-ed25519`); `ssh_enroll.entries_for_lookup_name`
   against the *real* managed store (`~/.local/state/nctl/ssh/known_hosts`,
   untouched) found all 3 entries under the bare alias; the offered/managed
   key-pair intersection was non-empty -- the same READY determination
   `reconcile.ssh_preflight.verify_offered_keys` would make.
6. Cleanup: the port-forward process was killed, and
   `/tmp/nctl-live-verify-A/` (the two disposable known_hosts files) was
   removed. The real managed known_hosts store was never opened for writing
   during this verification (read-only for the whole procedure) and remains
   exactly 3 lines under the one alias, as before.

## Live verification B — attempted, blocked by a structural finding, not completed

Date: 2026-07-22. Target: real `agdnsmasq` and the live Nautobot instance.
**Not marked complete** -- see the finding below and plan.md's own
instruction: "If a safe fixture cannot be created, do not mark this
verification complete. Record the reason and the requirements for an
alternative fixture."

### What was attempted

1. Confirmed steps 1-4 of plan.md's Live verification B were already
   satisfied by the automated-verification section above: managed store
   bare alias/fingerprint/permissions/absolute path; identical
   alias/`ansible_ssh_common_args` with differing routes across both
   generated inventories; a passing dry-run of `nctl apply dnsmasq
   --inventory <bootstrap>`; a passing dry-run of `nctl apply dnsmasq`
   (production).
2. `nctl reconcile agdnsmasq` showed no drift (`scope_summary:
   {"converged": 2}`), so step 5 required creating a temporary, reversible
   desired-state change to force a real SSH-requiring action -- per operator
   direction, this was done via the normal desired-state interface (the
   Nautobot intent-catalog REST API), not by hand-editing the database.
3. Created one new `DesiredEndpoint` on the real `agdnsmasq` node
   (`id 2ff268e0-b5dd-4f5f-b3fb-4d95a748d243`, `name
   nctl-fix-sshkey2-verify`, `endpoint_type service`, `dns_name
   nctl-verify-test.home.arpa`, `ip_address 192.168.0.5` -- inside the
   existing `network-infra` static-pool range, `generate_dnsmasq true`).
   Confirmed via `nctl render dnsmasq` that this produced one new
   `host-record=` line and via `nctl drift` that it entered the desired
   snapshot with no `manual_review` findings.
4. Ran `nctl reconcile agdnsmasq --yes`: `reconcile_ipam` and production
   inventory regeneration both succeeded, but the round ended
   `non_converged`/`no_progress` -- the plan **never** proposed a
   `dnsmasq_config`/`service_profile` action, and `ssh_preflight` stayed
   empty.

### Finding: this drift model cannot be forced by a desired-state content change alone

Reading `nctl_core/reconcile/reconcilers.py` (`plan_service_profile`) and
`nctl_core/drift/service_placement.py` (`evaluate_active_placement`/
`evaluate_placement_drift`) confirmed why: a `service_profile`/
`dnsmasq_config` action is only planned from a placement drift **gap** code
(`service_not_running`, `service_observation_missing`,
`service_observation_stale`, `service_observed_on_wrong_node`) -- all
derived from the last *observed* service state (`nodeutils`'s
`service_inventory` facts), never from a comparison against the freshly
rendered `dnsmasq.conf` content. Since the real `dnsmasq` daemon on
`agdnsmasq` was already observed running (from the `fix_sshkey` live
verification), adding a new DNS record produced zero placement drift no
matter how the record was added -- this is a property of the reconciliation
model, not something a desired-state fixture choice can work around.

The only ways to produce a real gap are actually more invasive than what was
authorized for this step: (a) briefly stopping the real `dnsmasq` daemon on
`agdnsmasq` so `nodeutils` observes it as not running (a real, if short,
service interruption on the actual host), or (b) writing a fabricated "not
running" observation into Nautobot's actual-state store directly (bypassing
`nodeutils`, misrepresenting the real machine's state -- explicitly the kind
of "not a substitute for a verified source" workaround this whole plan
exists to avoid). Presented to the operator; the operator chose to stop
rather than authorize either.

### Cleanup and restoration (completed)

- Deleted the test `DesiredEndpoint` via `DELETE
  /api/plugins/intent-catalog/endpoints/2ff268e0-.../` (`204`).
- Confirmed restoration: `nctl render dnsmasq` is back to the original 5
  `host-record=` lines (the test record is gone); `nctl reconcile agdnsmasq`
  is back to `state: planned`, `scope_summary: {"converged": 2}`, no errors.
- The managed known_hosts store was never written during this attempt
  (still exactly 3 lines). `git status` is clean in both the root repo and
  `ansible_agdev` (the regenerated inventories under
  `inventories/generated/` are git-ignored working files, not tracked
  changes).

### Requirements for a future safe fixture

To complete Live verification B without live-host disruption, a future
session needs one of: (1) a disposable/staging `agdnsmasq`-like host whose
`dnsmasq` service can be safely stopped/started for the test, or (2) the
drift model extended to compare rendered config content (not just observed
service state) -- out of scope for `fix_sshkey2`, which is a trust-contract
fix, not a drift-model change. Steps 8-9 (disposable-empty-store and
mismatch-fixture negative cases) were not attempted either, since they
require the same SSH-requiring plan this finding shows cannot be safely
forced right now; the equivalent behavior remains covered by
`nctl/tests/test_reconcile_executor.py`'s
`test_service_phase_blocks_on_mismatched_key_after_production_regen` and the
Step 3/4 unit-test suites (deterministic, disposable fixtures, exactly as
`fix_sshkey/report_verification.md`'s own Step 8 already concluded for the
equivalent pre-fix_sshkey2 case).

## Live verification status

- **Live verification A** — complete (above).
- **Live verification B** — attempted; **not completed**. Blocked by a
  structural property of the drift model (see above), not by anything
  `fix_sshkey2` changed or left unfixed. All live Nautobot state was
  restored and confirmed converged. Left as an open item for a future
  session with a safe fixture per the "Requirements" note above.
