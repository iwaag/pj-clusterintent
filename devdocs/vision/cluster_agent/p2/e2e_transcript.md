# Step 5b — agpc enrollment + live mTLS transcript

Real IDs/timestamps, redacting nothing (no secrets appear below — private
keys never left their host). Ran from the superproject root unless noted;
agpc-side commands ran via `ansible agpc -m shell -a '...'` from
`ansible_agdev/` (matching `ansible.cfg`'s SSH key/known-hosts config).

## 0. Pre-flight

```
$ ping -c2 agpc.local            # 192.168.0.110, reachable
$ ansible agpc -m ping           # -> "pong"
$ ansible agpc -m shell -a "openssl version"
OpenSSL 3.0.13 30 Jan 2024
```

Command node (`agstudio`, `192.168.0.100`/`agstudio.local`) is where
`cagent-api`/OpenCode run.

## 1. Local CA + server cert (command node)

```
$ uv run --project cagent cagent-ca init
CA created at .../.local/cagent-ca
  serial=1612f1c4fa0241fd6d320cd2452bf6d02a03e011 not_after=2031-08-01T19:26:54+00:00

$ uv run --project cagent cagent-ca sign-server \
    --out-key .local/cagent-ca/server_key.pem --out-cert .local/cagent-ca/server_cert.pem \
    --cn cagent-api --dns agstudio.local --ip 192.168.0.100
server cert written; serial=49ad1ed0426072151f61b98c73141639dc7eb07e not_after=2027-08-02T19:26:59+00:00
```

**Note**: the first `sign-server` invocation used a relative `--out-key`/
`--out-cert` path while `cwd` was `cagent/`, which wrote into a stray
`cagent/.local/cagent-ca/` instead of the repo-root `.local/cagent-ca/`
the default CA dir resolves to — caught immediately (`ls` didn't show the
expected files at the repo-root path), moved into place, stray directory
removed. No security impact (still under a `.local/` that's gitignored
either way), but worth recording as an operator gotcha: pass absolute
paths, or run from the repo root, for `--out-key`/`--out-cert`.

## 2. Pre-existing Phase 1 evidence broke `scan_and_load` on first live start

`cagent-api` crashed on startup with `KeyError: 'uuid'` — the real evidence
directory (`~/.local/state/cagent/evidence/`) still held 5 requests from
the Phase 1 Step 5 E2E run, in the old `{"class","name"}` identity shape.
Expected, given Phase 2 is a breaking change (README_DEV: "no compatibility
artifacts... maintenance window... preferable"); moved the old evidence
aside rather than deleting it:

```
$ mv ~/.local/state/cagent/evidence ~/.local/state/cagent/evidence-p1-archive
$ mkdir -p ~/.local/state/cagent/evidence
```

## 3. Start OpenCode + cagent-api (command node)

```
$ ./opencode/start.sh &                 # port 4097, loopback only, unchanged
opencode server listening on http://127.0.0.1:4097

$ CAGENT_API_HOST=0.0.0.0 CAGENT_API_PORT=8788 uv run --project cagent cagent-api &
cluster-agent API listening on https://0.0.0.0:8788 (mTLS required; ...)

$ curl -sv https://127.0.0.1:8788/requests --max-time 5
... TLS handshake, Request CERT ... SSL certificate problem: self signed certificate in certificate chain
```

Confirms mTLS is actually required: an unauthenticated `curl` (no client
cert, default trust store) is rejected at the handshake.

## 4. Generate key + CSR on agpc (private key never leaves the node)

```
$ ansible agpc -m shell -a "mkdir -p ~/.cagent && chmod 700 ~/.cagent && \
    openssl ecparam -genkey -name prime256v1 -noout -out ~/.cagent/node_key.pem && \
    chmod 600 ~/.cagent/node_key.pem && \
    openssl req -new -key ~/.cagent/node_key.pem -subj '/CN=agpc-node' -out ~/.cagent/node.csr"
agpc | CHANGED | rc=0 >> CSR_GENERATED
```

## 5. Fetch CSR, sign bound to agpc's real DesiredNode UUID, register

```
$ ansible agpc -m fetch -a "src=~/.cagent/node.csr dest=/tmp/agpc_enroll/ flat=yes"

$ uv run --project cagent cagent-ca sign-node \
    --csr /tmp/agpc_enroll/node.csr --uuid c82421c3-c42a-4bea-91ce-7468ae8a249c \
    --cn agpc --out /tmp/agpc_enroll/node_cert.pem
node cert written to /tmp/agpc_enroll/node_cert.pem
  uuid=c82421c3-c42a-4bea-91ce-7468ae8a249c
  serial=25a569df17443f944103ba1a3710aa5ff9353219
  fingerprint=acff6f5408843a86b7a5f8bad906ebf15ba7dd7ba70ef74b2bf290f6aa389ddc
  not_after=2027-08-02T19:28:24+00:00

$ uv run --project cagent cagent-ledger register \
    --uuid c82421c3-c42a-4bea-91ce-7468ae8a249c --serial 25a569df17443f944103ba1a3710aa5ff9353219 \
    --fingerprint acff6f5408843a86b7a5f8bad906ebf15ba7dd7ba70ef74b2bf290f6aa389ddc \
    --not-after 2027-08-02T19:28:24+00:00
registered serial=25a569df17443f944103ba1a3710aa5ff9353219 uuid=c82421c3-c42a-4bea-91ce-7468ae8a249c state=active
```

UUID `c82421c3-c42a-4bea-91ce-7468ae8a249c` is the DesiredNode UUID
Ansible/nctl already resolves for `agpc`
(`ansible_agdev/inventories/generated/production.yml`,
`nctl_ssh_host_key_alias: nctl-node-c82421c3-...`) — the operator-supplied
argument, not anything self-claimed by the CSR.

## 6. Place cert + CA cert on agpc (same SSH path)

```
$ ansible agpc -m copy -a "src=/tmp/agpc_enroll/node_cert.pem dest=~/.cagent/node_cert.pem mode=0644"
$ ansible agpc -m copy -a "src=/tmp/agpc_enroll/ca_cert.pem dest=~/.cagent/ca_cert.pem mode=0644"
```

## 7. Real request from agpc over mTLS

```
$ ansible agpc -m shell -a 'curl -sS --cacert ~/.cagent/ca_cert.pem --cert ~/.cagent/node_cert.pem \
    --key ~/.cagent/node_key.pem -X POST https://agstudio.local:8788/requests \
    --data @$HOME/.cagent/req1.json -H "Content-Type: application/json"'
{"request_id": "req_2de6d6b897fe4378981401c08527d722", "session_id": "ses_03c0c7f50ffe5PCnkcRZPHu6M9", "state": "queued"}
```

(`req1.json` contained `{"message": "I want S3-compatible storage - what
exists in this cluster?"}` — the same Phase 1 example question.)

Polled to completion (~221s — a real multi-step tool-calling turn, same
order of magnitude as Phase 1's observed real turns); final state fetched
**from agpc itself**:

```
$ ansible agpc -m shell -a 'curl -sS --cacert ... https://agstudio.local:8788/requests/req_2de6d6b897fe4378981401c08527d722'
{"request_id": "req_2de6d6b897fe4378981401c08527d722", ..., "state": "completed",
 "identity": {"class": "node", "uuid": "c82421c3-c42a-4bea-91ce-7468ae8a249c",
              "cert_serial": "25a569df17443f944103ba1a3710aa5ff9353219"},
 "response": "There is no S3-compatible object storage deployed in this cluster. ..."}
```

Correct, useful answer (cross-checkable against the same live `nctl
relations --json`/`drift --json` facts as Phase 1's equivalent check).

## 8. Revoke, confirm rejection

```
$ uv run --project cagent cagent-ledger revoke 25a569df17443f944103ba1a3710aa5ff9353219
revoked serial=25a569df17443f944103ba1a3710aa5ff9353219 uuid=c82421c3-c42a-4bea-91ce-7468ae8a249c state=revoked

$ ansible agpc -m shell -a 'curl -sS -o /tmp/revoked_response.json -w "%{http_code}" \
    --cacert ... -X POST https://agstudio.local:8788/requests --data @$HOME/.cagent/req1.json ...; cat /tmp/revoked_response.json'
403
{"error": {"code": "forbidden", "message": "certificate not registered or revoked", "request_id": null}}
```

Same TLS connection parameters, same cert — rejected immediately, no
server restart, no cert reissue. Confirms `contract.md`'s per-request
ledger check.

## 9. Reactivate, confirm it works again

```
$ uv run --project cagent cagent-ledger reactivate 25a569df17443f944103ba1a3710aa5ff9353219
reactivated serial=25a569df17443f944103ba1a3710aa5ff9353219 uuid=c82421c3-c42a-4bea-91ce-7468ae8a249c state=active

$ ansible agpc -m shell -a 'curl -sS --cacert ... -X POST https://agstudio.local:8788/requests --data @$HOME/.cagent/req2.json ...'
{"request_id": "req_d68188e969dd464187df8e4fa745257d", "session_id": "ses_03c07e097fferIfCWYqy7dzXaW", "state": "queued"}
```

(`req2.json`: `{"message": "confirm reactivation works"}`.) Polled to
`completed` (~18s this time — a short, non-tool-heavy turn); response
confirmed Nautobot reachability and submodule status, i.e. a real answer,
not a cached/stub one. Phase ends with agpc enrolled, active, and usable.

## 10. Evidence check

```
$ uv run --project cagent cagent-evidence list
req_2de6d6b897fe4378981401c08527d722  completed     node:c82421c3-c42a-4bea-91ce-7468ae8a249c  ses_03c0c7f50ffe5PCnkcRZPHu6M9
req_d68188e969dd464187df8e4fa745257d  completed     node:c82421c3-c42a-4bea-91ce-7468ae8a249c  ses_03c07e097fferIfCWYqy7dzXaW
```

Both requests' evidence carries the correct DesiredNode UUID and cert
serial (`25a569df...`) as the recorded identity — matching contract.md's
`{"class": "node", "uuid", "cert_serial"}` shape exactly.

## Real bug found and fixed during this step

`cagent-evidence list` (`evidence_cli.py:cmd_list`) still referenced the
deleted Phase 1 `identity["name"]` field, raising `KeyError: 'name'` the
first time it was run against real Phase 2 evidence — a spot Step 4's
identity-shape migration missed (only `store.py`/tests were updated then).
Fixed to read `identity["uuid"]`; added `tests/test_evidence_cli.py`
(2 tests, previously no coverage existed for this CLI at all) to lock it
in. Included in this step's commit since it was found here, matching the
Phase 1 Step 5 precedent for fixes discovered during live verification.

## Cleanup

- `cagent-api` and this step's OpenCode instance (port 4097) were stopped
  (`kill`) after verification; other pre-existing OpenCode instances on
  this machine (ports 4096/4907, unrelated node-agent sessions) were left
  untouched.
- Scratch request-body files and the CSR were removed from agpc
  (`~/.cagent/req1.json`, `req2.json`, `node.csr`); agpc's enrolled
  `node_key.pem`/`node_cert.pem`/`ca_cert.pem` were **kept** — the phase's
  own exit criterion is that agpc ends enrolled and usable, not that
  enrollment is undone.
- `/tmp/agpc_enroll/` (CSR/cert copies, response bodies) on the command
  node was removed.
- The Phase 1 evidence archive (`~/.local/state/cagent/evidence-p1-archive/`)
  was kept, not deleted — historical evidence, not scratch.
