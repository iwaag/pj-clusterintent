# Report — fix_sshkey3 Step 6: rollout and verification

Date: 2026-07-22

Status: automated verification and the reversible live dnsmasq-content
verification are complete. The scoped reconcile operations correctly report
`non_converged` after the content work because the pre-existing
`missing_actual_ip_address` finding keeps scheduling the IPAM Job; that is
separate from the dnsmasq content result. In every relevant final drift,
the `dnsmasq` service itself is `converged` with no content diff.

## Coordinated rollout

Deployed source revisions were:

- `nctl` `cea87b414ef473b0731ea8bacd7555209716f092`
- `nodeutils` `09d9227018711a9a78c7dea20e5f9c231ad41a50`
- `nauto` `617036d3b342c6a573e9d2a68a4140482540fc75`
- `ansible_agdev` `863b98d5d8dc702752af9ad00db9a5d5d9bc79ba`

The first `agdnsmasq` v2 collection exposed that the running Nautobot Job
still accepted only the old schema (`unsupported schema_version:
nodeutils.inventory.v2`). The Nautobot Git Repository `main` was then synced
through its normal REST sync operation. Job result
`ab319e6e-0238-4c27-9846-be3fd6f3563c` completed `SUCCESS`; the next v2
collection and `Ingest Nodeutils Inventory` job (`e631edb7-4bec-48a6-aa53-0f917ebf19f4`)
completed successfully. No v1/v2 dual reader was added.

## Automated verification

```text
uv run --project nctl pytest -q nctl/tests
914 passed, 1 warning

uv run --project nodeutils --with pytest pytest -q nodeutils/tests
20 passed

uv run --project nodeutils ruff check nodeutils
All checks passed

(cd nauto && python3 -m unittest discover -s tests -p 'test_*.py')
Ran 14 tests ... OK

(cd nauto && python3 -m py_compile jobs/*.py)
success

ansible-playbook --syntax-check ansible_agdev/playbooks/dnsmasq/deploy_dnsmasq_records.yml
ansible-playbook --syntax-check ansible_agdev/playbooks/nautobot/run_nodeutils_collect.yml
success
```

`pytest` is not declared in nodeutils' development dependency group, so the
explicit temporary `--with pytest` was required. `ruff` is declared and
passed. `nctl` does not declare `ruff` or `mypy`, so neither is reported as a
passing check. The shared `dnsmasq-v5-golden.conf` fixture is byte-identical in
the nctl and nodeutils test suites; both independently reproduce SHA-256
`c25e51c4efce07281e580dcfb1ecad73d666a70310f87cd28ad448241215e592`.

## Live verification B — reversible dnsmasq content convergence

Target: real `agdnsmasq`. The daemon was never stopped and no fabricated
nodeutils observation was written.

1. The initial v2 observation had no managed-file result, producing
   `service_config_observation_missing`. Reconcile operation
   `01KY3Z82RYZG02FY91W790P4EG` collected and ingested v2 facts, detected the
   legitimate first v5 byte-contract mismatch, deployed `dnsmasq_config`, and
   collected/ingested again. Its final service target had no diffs. The desired
   and observed digest was `118dd7e667439774fc6b0dd1acd49513be4ebb8b6f15967e6edacd4e708445b3`.
2. A temporary DesiredEndpoint was created through the normal nintent REST
   interface: `7ba6a96c-d1b0-45ed-b05c-c48f940586e0`, name
   `nctl-fix-sshkey3-verify`, DNS name
   `nctl-fix-sshkey3-verify.home.arpa`, static address `192.168.0.5`, and
   `generate_dnsmasq=true`.
3. Plan operation `01KY3ZB9FC3KC14B7GS5NJAJB6` contained both
   `service_config_mismatch` and a `dnsmasq_config` action for `agdnsmasq`.
   Apply operation `01KY3ZBNRTJFSQ6CTXG8QASJ8B` completed dnsmasq deployment
   (Ansible recap: `ok=8 changed=2 unreachable=0 failed=0`) followed by v2
   nodeutils collection and Nautobot ingest. The service final drift was
   converged; the deployed desired/observed digest was
   `d7fae9d50f3cd463fe3de047e7f224cc0531fc13fd0838fe644dea18355158ee`.
4. DNS lookup against the real server returned `192.168.0.5`.
5. The temporary endpoint was deleted through the same REST interface
   (`204`). Reverse plan operation `01KY3ZDYN2M9YMG7PMVY13ENRE` again contained
   `service_config_mismatch` and `dnsmasq_config`. Apply operation
   `01KY3ZE969DKEWA08RHBR0FH9H` deployed, re-observed, and re-ingested the
   removal. The DNS lookup returned no answer and the final service target had
   no diffs. The records-file digest returned to the original
   `118dd7e667439774fc6b0dd1acd49513be4ebb8b6f15967e6edacd4e708445b3`.

The successful add operation's production preflight proves the installed
generation binding: generation `0605c00f-7313-4b23-b73a-41036221b23a`, route
`192.168.0.2`, port `22`, alias
`nctl-node-27818c12-fe15-4c9f-83d0-7949523f6c33`, phase
`production_route`, and identical managed/offered public fingerprints:

```text
SHA256:AquqxjueGjr/jAUp+nxNlFMgTcnyfyyBMsPJmF/l+I8
SHA256:f6quO49WOg6yr3LqCHoUWDEUFzPVV1STV+l5A6T1eYg
SHA256:xHoZ1UNGMnqNm8xK45ijt8AstNNLZf2jDoRdvXUMvp4
```

Artifacts contain only those public fingerprints and digest metadata; no raw
SSH key blob or dnsmasq content was copied into Nautobot evidence.

## SSH closure and negative boundaries

The disposable non-default-port OpenSSH proof remains recorded verbatim in
`fix_sshkey2/report_verification.md` (Live verification A). This step adds
the allowlist/port/store-error cases to the nctl automated suite; the suite
also covers blocked mismatched-key service actuation and retained partial
round evidence. No disposable test wrote the real managed store, and the live
content test added no endpoint-keyed known_hosts entry.

The test DesiredEndpoint is deleted, its DNS response is removed, and the
original nctl-managed dnsmasq digest is restored. The remaining scoped
`missing_actual_ip_address`/repeated IPAM behavior is an existing independent
reconcile issue, documented here rather than being represented as a failed
content-convergence check.
