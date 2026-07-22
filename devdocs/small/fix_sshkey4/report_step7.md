# Report — Step 7: controlled dnsmasq regression verification and documentation

Date: 2026-07-22
Scope: one reversible live change against the real `agdnsmasq` host, plus documentation.
Status: **complete**

Per this session's earlier explicit confirmation, this step's live, hard-to-reverse actions against
real infrastructure were run only after the user re-confirmed proceeding.

## Baseline (before any change)

- Desired render digest (`nctl render dnsmasq --json` `content_sha256`):
  `118dd7e667439774fc6b0dd1acd49513be4ebb8b6f15967e6edacd4e708445b3`.
- nodeutils-observed managed file: path `/etc/dnsmasq.d/nintent-records.conf`, `status: present`,
  same SHA-256, size 472.
- `dnsmasq.service`: `active`/`running`.
- `nctl drift --host agdnsmasq --json`: target `converged`, only the pre-existing
  `missing_actual_ip_address` warning (unrelated, non-goal per plan.md). `nctl drift --service
  dnsmasq --json`: target `converged`, zero diffs.
- Cluster-wide `nctl drift --json`: `agdnsmasq converged`, `agbach converged`, `agpc converged`,
  `dnsmasq converged`, `aghub unknown`, `agstudio unknown` — matching the plan's documented
  non-goal baseline exactly.
- Real managed SSH known_hosts store: SHA-256
  `7d7272d5a74fe59d1b3812cf79425ddde8b0798dca09265cf802215822d7a34c`, 3 lines — identical to the
  hash recorded at the end of Step 6.

## Metadata-owned destination confirmed

`nctl_core.reconcile.profiles.resolve_dnsmasq_records_spec` is the sole source read by
`dnsmasq_apply.build_dnsmasq_apply` (`src/nctl_core/dnsmasq_apply.py:190,294`), which passes it as
the structured `dnsmasq_records_config_file` extra var. `deploy_dnsmasq_records.yml` requires and
validates that variable as a non-empty absolute path (`is match('^/')`) with no default of its own
— confirmed by reading the playbook's `pre_tasks` assertions directly.

## Live verification

1. Created a temporary `DesiredEndpoint` through the normal nintent REST interface:
   `f01152a5-8cfa-410f-8cd7-826848c40f49`, name `nctl-fix-sshkey4-verify`, `endpoint_type: service`,
   `ip_policy: static`, `ip_address: 192.168.0.5` (the same address `fix_sshkey2`/`fix_sshkey3` used
   and confirmed free again via the IPAM/endpoint REST filters before creating), `dns_name
   nctl-fix-sshkey4-verify.home.arpa`, `generate_dnsmasq: true`.
2. `nctl reconcile agdnsmasq` (plan mode) produced operation `01KY4FJRGC806SBESZS1GG7EF2` with a
   plan containing exactly one `dnsmasq_config` action (`claimed_diff_codes:
   ["service_config_mismatch"]`, target `dnsmasq`, `host_slugs: ["agdnsmasq"]`) plus the unrelated,
   pre-existing `reconcile_ipam` job action — no sibling dnsmasq target.
3. `nctl reconcile agdnsmasq --yes` (operation `01KY4FKNFXQPAX53SRJDX3KZ25`) executed the plan:
   - Production SSH preflight (round 0, `phase: production_route`): generation
     `7364e51f-e42e-43f3-8e46-da071e16ece6`, route `192.168.0.2`, port `22`, alias
     `nctl-node-27818c12-fe15-4c9f-83d0-7949523f6c33`, status `ready`. Managed and offered
     fingerprints were identical:
     ```
     SHA256:AquqxjueGjr/jAUp+nxNlFMgTcnyfyyBMsPJmF/l+I8
     SHA256:f6quO49WOg6yr3LqCHoUWDEUFzPVV1STV+l5A6T1eYg
     SHA256:xHoZ1UNGMnqNm8xK45ijt8AstNNLZf2jDoRdvXUMvp4
     ```
   - The `dnsmasq_config` action's own inner `build_dnsmasq_apply` sub-operation
     (`01KY4FKSRARGW5AB1X8REXHMPP`) rendered a new artifact
     (`content_sha256 8d95a63c4cc744cf91fcd2d1ea0d179716cb9fc31756427842fc15269da8af92`),
     passed `dnsmasq_records_src`/`dnsmasq_records_config_file` as one structured extra-vars
     payload, ran both playbooks with `--limit agdnsmasq` (`target_hosts: ["agdnsmasq"]`, no
     sibling host touched), and recorded Ansible recap `ok=9 changed=2 unreachable=0 failed=0` for
     the deploy playbook (`ok=9 changed=0 skipped=1` for the idempotent setup playbook beforehand).
   - Post-actuation nodeutils collection/ingest (`ingest_outcome: updated`) then observed
     `/etc/dnsmasq.d/nintent-records.conf`, SHA-256
     `8d95a63c4cc744cf91fcd2d1ea0d179716cb9fc31756427842fc15269da8af92`, matching the freshly
     deployed digest and the same path.
   - Round 1 re-fetched drift with zero `service_config_*` diffs and planned no repeated
     `dnsmasq_config` action — only the unrelated `reconcile_ipam` job ran again. Final round drift
     (`round-01/drift-final.json`) reports the `dnsmasq` service target `converged` with zero diffs.
   - Overall run state: `non_converged` (exit 1), solely because of the pre-existing
     `missing_actual_ip_address`/repeated-IPAM finding still scheduling `reconcile_ipam` every
     round — an existing, independent, non-goal condition, not a dnsmasq content failure.
4. DNS lookup against the real server (`dig +short nctl-fix-sshkey4-verify.home.arpa @192.168.0.2`)
   returned `192.168.0.5`.
5. Deleted the temporary endpoint through the same REST interface: `204`.
6. `nctl reconcile agdnsmasq` (plan mode, operation `01KY4G17R75SBGBWEG5GAM3QW0`) again produced a plan with exactly
   one `dnsmasq_config` action (`service_config_mismatch`, target `dnsmasq`, `host_slugs:
   ["agdnsmasq"]`) — the reverse content drift. `nctl reconcile agdnsmasq --yes` (operation
   `01KY4G1ECY07T2YK3XKQ4MPE67`) deployed it: same production-route preflight shape (generation
   `c9c5cce9-dfe9-42f2-b179-6d4cc29483c3`, route `192.168.0.2`, port `22`, identical matching
   fingerprint triple), re-observed, and re-ingested the removal. Round 1 again shows the `dnsmasq`
   service target `converged` with zero diffs; the run's overall state is again `non_converged` for
   the same pre-existing, unrelated IPAM reason only.
7. DNS lookup for `nctl-fix-sshkey4-verify.home.arpa @192.168.0.2` returned no answer. The
   nodeutils-observed managed file returned to path `/etc/dnsmasq.d/nintent-records.conf`, SHA-256
   `118dd7e667439774fc6b0dd1acd49513be4ebb8b6f15967e6edacd4e708445b3` — the exact original digest.
   `dnsmasq.service` was `active`/`running` in every observation throughout this step; it was never
   deliberately stopped.

## Cleanup confirmation

- `GET` on the deleted endpoint's URL returns `404 "No DesiredEndpoint matches the given query."`
  — the test endpoint is confirmed absent.
- The real managed SSH known_hosts store is confirmed byte-identical before and after: SHA-256
  `7d7272d5a74fe59d1b3812cf79425ddde8b0798dca09265cf802215822d7a34c`, still 3 lines, still only the
  one existing `nctl-node-27818c12-...` alias entry — no endpoint/IP-keyed entry was added by this
  step's SSH-requiring actions, consistent with `HostKeyAlias` being independent of the connection
  endpoint.
- `dnsmasq.service` was never deliberately stopped at any point (observed `active`/`running` in
  every nodeutils collection this step triggered).

## Documentation updates

- `ansible_agdev/README.md`: the `-e dnsmasq_records_src=...` example now also shows
  `dnsmasq_records_config_file`, and the playbook description now states neither variable has a
  playbook default and the destination is resolved once from `nctl`'s validated
  `deployment_profile_reconciliation` metadata (previously described the pre-fix_sshkey4-Step-3
  single-var, defaulted-destination shape).
- `ansible_agdev/README_DEV.md`: the "nctl dnsmasq Consumption" section now documents
  `dnsmasq_records_config_file` as a second required absolute-path variable with no default,
  alongside the already-accurate note that the path is resolved once from reconciliation metadata.
- `ansible_agdev/README_ADMIN.md`: already accurately described the SHA-256 content-verification
  model with no stale literal; left unchanged.
- `nodeutils/README.md`: contains no developer test-command documentation referencing the old
  `--with pytest` invocation (confirmed by `grep`); nothing to update, matching Step 4's report.
- `nctl/README.md`: added a paragraph under "SSH trust configuration" documenting the strict
  reader's `unenrolled`-vs-corruption distinction, the `ssh_store_read_failed` boundary contract,
  round/evidence retention on a post-mutation store failure, and obsolete `[alias]:port` residue
  handling (Step 1/Step 2, previously undocumented). Added a paragraph under `apply dnsmasq`
  documenting reconcile-only exact host-set targeting via `--limit`, the metadata-owned destination
  contract, and `service_config_observation_mismatch` (Step 3, previously undocumented).
- `devdocs/small/fix_sshkey3/report_verification.md`: added a superseding note at the top pointing
  to `fix_sshkey4` for the gaps that report's "complete" status did not actually close, without
  rewriting any of its historical evidence below the note.

## Step 7 exit criteria

- [x] The effective metadata destination passed to Ansible is
  `/etc/dnsmasq.d/nintent-records.conf` with no playbook default supplying it.
- [x] Plan contained `service_config_mismatch` + `dnsmasq_config`, exact target `agdnsmasq`, no
  sibling targets — for both the add and the reverse-removal plan.
- [x] Apply proved: same-generation production SSH preflight; matching managed/offered
  fingerprints; exact destination extra variable; Ansible limited to `agdnsmasq`; deployment
  success and post-actuation observation; matching desired/observed digest and path; successful DNS
  answer — for both the add and the removal.
- [x] Test endpoint deleted and confirmed absent; `dnsmasq.service` never deliberately stopped; real
  managed SSH store confirmed byte-identical before/after; no endpoint/IP-keyed known_hosts entry
  was added.
- [x] The overall reconcile envelope is `non_converged` solely because of the pre-existing,
  explicitly out-of-scope `missing_actual_ip_address`/repeated-IPAM finding; the `dnsmasq` service
  target itself is `converged` with zero diffs in every final round drift this step produced.
