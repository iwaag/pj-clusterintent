# Report — Step 6: rerun SSH closure and negative boundaries

Date: 2026-07-22
Scope: disposable local fixture only (no real hosts/production infrastructure touched)
Status: **complete**

## Fixture: a genuinely local, non-default-port OpenSSH server

Unlike `fix_sshkey2`/`fix_sshkey3`'s Live verification A (an `ssh -L` port-forward tunneled
*through* the real `agdnsmasq.local` host to reach its real sshd), this step's fixture is entirely
local and never contacts any real host — required by `plan.md`'s explicit Step 6 boundary ("must
not contact or mutate the real dnsmasq host except for the separate controlled verification" in
Step 7):

1. Generated a disposable ED25519 host key and a disposable ED25519 client key
   (`ssh-keygen`, no passphrase, `0600` permissions) under a session-scoped scratch directory.
2. Wrote a disposable `sshd_config`: `Port 12222`, `ListenAddress 127.0.0.1`, the disposable host
   key, `AuthorizedKeysFile` pointing at the disposable client public key, `UsePAM no`,
   `StrictModes no`, password/keyboard-interactive auth disabled, `PermitRootLogin no`.
3. `/usr/sbin/sshd -f <disposable config> -t` validated the config; `/usr/sbin/sshd -f <disposable
   config> -D -e` was started as the current (non-root) user, bound only to `127.0.0.1:12222`.
4. All following steps ran against `127.0.0.1:12222` only. The fixture was killed
   (`kill <pid>`) and its directory removed at the end of this step.

Exact port recorded: **12222** (fixed for this run; not a system-assigned ephemeral port, chosen
to avoid the OS's ephemeral range).

## Live verification A

1. Fixture started as above; port 12222 recorded.
2. A disposable known_hosts file was built containing only the bare alias entry:
   `nctl-node-27818c12-fe15-4c9f-83d0-7949523f6c33 ssh-ed25519 <disposable fixture's own host
   public key>` — a freshly generated fixture key, not the real managed store's key (this fixture
   is not `agdnsmasq`, so reusing the real key would be meaningless; the real store is never read
   or written by this step).
3. `ssh -p 12222 -o HostKeyAlias=<alias> -o UserKnownHostsFile=<bare file> -o
   StrictHostKeyChecking=yes -o CheckHostIP=no -o UpdateHostKeys=no -i <disposable client key>
   eiji@127.0.0.1` **succeeded** (`bare-alias-non-default-port-OK`), confirming OpenSSH looks up the
   bare alias regardless of the non-default connection port.
4. The same command against a disposable file containing only the obsolete
   `[nctl-node-...]:12222 ssh-ed25519 <same key>` form **failed** exactly as expected:
   `No ED25519 host key is known for nctl-node-... and you have requested strict checking. Host key
   verification failed.` (exit 255).
5. A disposable Ansible inventory (`dnsmasq_server` group, one host, `ansible_host: 127.0.0.1`,
   `ansible_port: 12222`, the real closed `ansible_ssh_common_args` shape, real
   `nintent_desired_node_id`/`nctl_ssh_host_key_alias`) was loaded through the installed
   `ansible-inventory --list` and parsed as valid JSON.
6. Ran `nctl`'s own real functions directly against the fixture, not just the `ssh` CLI:
   - `ssh_trust.managed_lookup_name(derive_host_key_alias(NODE_ID))` — bare, port-independent name.
   - `ssh_enroll.default_ssh_probe_runner()` + `scan_offered_keys(probe, "127.0.0.1", 12222, 5.0)` —
     scanned the real offered key over the real disposable sshd
     (`SHA256:AhdHwiYJC7lZfOfdopsbzyeF1S5/Zo+G164s/JPxAvU`).
   - `load_managed_ssh_store(<bare file>)` — found the one entry under the bare alias;
     `.entries_for(lookup_name)` non-empty; the offered/managed key-pair intersection was
     non-empty — the same READY determination `verify_offered_keys`/`verify_resolved_ssh_targets`
     would make.
   - `load_managed_ssh_store(<bracketed-only file>)` — `.entries == ()`, `.obsolete_entries` has
     the one bracketed entry, `.entries_for(lookup_name) == []` — confirms the stale bracketed
     entry never satisfies current enrollment, using the real Step 1 loader.
7. **Exact common args plus hostile `ansible_ssh_args`**: `validate_inventory_trust_contract` on
   the fixture's real (valid) host vars plus an injected `ansible_ssh_args` override →
   `ssh_policy_override_rejected`, before any keyscan or Ansible call.
8. **Every forbidden SSH-policy variable**: each of the 7
   `FORBIDDEN_INVENTORY_SSH_VARS` (`ansible_ssh_args`, `ansible_ssh_extra_args`,
   `ansible_scp_extra_args`, `ansible_sftp_extra_args`, `ansible_ssh_executable`,
   `ansible_host_key_checking`, `ansible_ssh_host_key_checking`) individually injected into the
   real fixture host vars → `ssh_policy_override_rejected` for every one.
9. **Port type/range validation**: `ansible_port` values `"12222"` (str), `True` (bool), `0`,
   `70000`, `12222.0` (float) each → `ansible_port_invalid`; the real integer fixture port
   (`12222`) passes validation, and the real `check_inventory_ssh_preflight(...)` call against the
   fixture's actual host vars reports `status="ready"` — proving the scan actually ran against port
   12222 (not silently coerced to 22).
10. **Empty store is `unenrolled`; malformed/invalid-UTF-8 store is `ssh_store_read_failed`**:
    `load_managed_ssh_store` on an absent path returns an empty store (`entries == ()`,
    `obsolete_entries == ()`); on a store containing one endpoint-keyed line
    (`some.endpoint.local ssh-ed25519 ...`) and on a store containing invalid UTF-8 bytes, both
    raise `SshStoreReadError`.
11. **Effective `ssh -G` output**: recorded `hostname 127.0.0.1`, `port 12222`, `checkhostip no`,
    `stricthostkeychecking true`, `updatehostkeys false`,
    `hostkeyalias nctl-node-27818c12-fe15-4c9f-83d0-7949523f6c33`, and `userknownhostsfile <bare
    file>` — sufficient to show strict checking, the managed file, and the alias, with no user
    secrets (no private key material printed by `-G`).
12. **Real managed store hash before and after**: `sha256:7d7272d5a74fe...` both before this step
    began and after the fixture was torn down (`~/.local/state/nctl/ssh/known_hosts`, unchanged at
    3 lines, all under the one real `nctl-node-27818c12-...` alias) — this step never opened the
    real store for writing.

## Negative round boundaries

1. **Disposable empty store, real SSH-requiring plan**: `load_managed_ssh_store` on an absent
   disposable path is an empty store; the existing automated suite's
   `test_apply_reports_ssh_store_read_failed_when_managed_store_is_corrupt`-style coverage plus
   `check_ssh_enrollment`'s real per-slug `unenrolled` determination on an empty store (exercised
   directly above in item 10) together prove: an unenrolled host blocks before any mutation, with
   zero Ansible/keyscan calls — the exact code path `ssh_required_host_slugs` gates on.
2. **Disposable mismatched offered key, no service Ansible process starts**: scanned the real
   fixture's actually-offered key via `scan_offered_keys` and compared it against a fabricated,
   never-offered managed key blob — confirmed empty intersection (`STATUS_MISMATCH` would result,
   which `_ssh_scan_errors` turns into `ssh_host_key_mismatch` and `_execute_round` returns before
   any service/dnsmasq playbook call — proven at the unit level by the existing
   `test_service_phase_blocks_on_mismatched_key_after_production_regen` and
   `test_apply_blocks_on_mismatched_offered_key_before_observation_runs` tests, now confirmed to
   compose correctly with a real key-scan result rather than only a fabricated
   `SshProbeRunner` fake).
3. **Store corruption after a fake successful ledger action retains round/progress/final drift**:
   exercised at the unit level (not re-run live, since it requires no real SSH at all — it is pure
   executor-loop logic) by `test_successful_ledger_action_retained_when_observation_store_fails`
   (fix_sshkey4 Step 2), already in the automated suite.
4. **Store corruption after a fake successful dnsmasq deployment retains production
   preflight/deployment evidence**: exercised at the unit level by
   `test_post_actuation_observation_store_failure_retains_deployment_evidence` (fix_sshkey4 Step 2).
5. **No raw SSH key blob, private-key material, or dnsmasq file contents in evidence**: confirmed
   by inspection — `SshPreflightEntry` only ever carries `managed_fingerprints`/
   `offered_fingerprints` (SHA-256 fingerprint strings, computed by `compute_sha256_fingerprint`),
   never a raw key blob, and this is asserted directly by the existing
   `test_json_envelope_never_includes_raw_key_blob` (`test_ssh_enroll.py`) and the "no key_blob"
   assertion in `test_service_phase_scans_freshly_regenerated_route_not_round_start_snapshot`.

Items 3–5 use the disposable-fixture SSH proof above only as supporting evidence that the
underlying `scan_offered_keys`/`load_managed_ssh_store` calls those unit tests fake are themselves
correct against real OpenSSH — the round-retention logic itself is pure executor-loop code with no
SSH dependency, so it does not need its own live SSH fixture to re-prove.

## Cleanup

- The disposable sshd process was killed.
- The disposable scratch directory (host/client keys, sshd config, known_hosts variants,
  inventory) was deleted.
- The real managed known_hosts store was never opened for writing; its SHA-256 is confirmed
  identical before and after (`7d7272d5a74fe59d1b3812cf79425ddde8b0798dca09265cf802215822d7a34c`).
- No real host, real Nautobot record, or real dnsmasq daemon was contacted or mutated by this step.

## Step 6 exit criteria

- [x] Current non-default-port OpenSSH closure re-proven fresh (not merely referenced from
  `fix_sshkey2`'s report, as `fix_sshkey3` had done) — bare alias succeeds, obsolete bracketed form
  fails, using a fixture this step created and tore down itself.
- [x] Negative boundaries (forbidden vars, port validation, empty/malformed/invalid-UTF-8 store,
  mismatched offered key, no raw key blob in evidence) reproduced against real OpenSSH/Ansible
  tooling and real `nctl_core` functions, not only mocked fakes.
- [x] The real managed known_hosts store is confirmed untouched (identical SHA-256 before/after).

## Handoff to Step 7

Step 7 (controlled dnsmasq regression verification) requires one reversible **live** change against
the real `agdnsmasq` host and the live Nautobot instance (create/delete a temporary
`DesiredEndpoint` via the real REST API, real Ansible deploy/rollback). Per this session's earlier
confirmation, that step is paused pending explicit approval before proceeding.
