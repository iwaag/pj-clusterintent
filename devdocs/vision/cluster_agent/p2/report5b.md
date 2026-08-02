# Step 5b report — Enroll agpc and pass a real request (LIVE)

## What was done

Full transcript with real IDs/timestamps: [`e2e_transcript.md`](e2e_transcript.md).
User approval was obtained (AskUserQuestion) before the first SSH/Ansible
action against agpc, per the plan's pause point.

1. Initialized the local CA (`cagent-ca init`) and signed the API server's
   own TLS cert (`cagent-ca sign-server`, SANs `agstudio.local` +
   `192.168.0.100` — the address Step 0 identified agpc actually dials).
2. Discovered and fixed a real startup crash: real Phase 1 evidence (5
   requests, old `{"class","name"}` identity shape) broke
   `scan_and_load`'s new `record["identity"]["uuid"]` read. Moved that
   evidence aside to `~/.local/state/cagent/evidence-p1-archive/`
   (preserved, not deleted) rather than deleting or patching around it —
   Phase 2 is a declared breaking change, and this is exactly the
   "maintenance window, not dual readers" case README_DEV asks for.
3. Started the Step-2 OpenCode instance (loopback, unchanged) and
   `cagent-api` with `CAGENT_API_HOST=0.0.0.0`. Confirmed via a bare
   `curl` from the command node itself that an unauthenticated TLS
   connection is rejected at the handshake (`SSL certificate problem:
   self signed certificate in certificate chain` — no client cert offered)
   — mTLS is actually enforced, not just configured.
4. Enrolled agpc following refined_idea.txt's procedure over the existing
   Ansible ad-hoc SSH path (`ansible_agdev/`, `ansible.cfg`'s pinned SSH
   key): generated an EC P-256 key + CSR **on agpc** with `openssl`
   (present as OpenSSL 3.0.13 — confirms Step 0's mechanics work against a
   different OpenSSL than the command node's LibreSSL 3.3.6, and confirms
   `cagent-ca sign-node` interoperates with a non-`cryptography`-generated
   CSR, same as the earlier scratch check in Step 2); fetched the CSR;
   signed it bound to agpc's real DesiredNode UUID
   (`c82421c3-c42a-4bea-91ce-7468ae8a249c`, the UUID Ansible/nctl already
   resolves for that host — never a self-claimed slug); registered in the
   ledger; placed the cert + CA cert back on agpc over the same path. The
   private key never left agpc.
5. From agpc, `curl --cacert --cert --key --data @file` (never inline)
   sent the Phase 1 example question ("I want S3-compatible storage - what
   exists in this cluster?"). `202 queued`; polled to `completed`
   (~221s, a real multi-step tool-calling turn); the answer was correct
   and useful (no S3-compatible storage present, correctly distinguished
   from Proxmox `local-lvm`), fetched **from agpc's own vantage point**,
   not just checked on the command node.
6. Revoked the serial via `cagent-ledger revoke`; the identical request
   from agpc was rejected `403 forbidden` immediately — no restart, no
   cert reissue. Reactivated via `cagent-ledger reactivate`; a fresh
   request from agpc succeeded again (`202` → `completed` in ~18s).
   Phase ends with agpc enrolled, active, and usable, per the plan.
7. Confirmed evidence (`cagent-evidence list`/`show`) records the correct
   DesiredNode UUID and cert serial as identity for both completed
   requests, matching `p2/contract.md`'s evidence shape exactly.

## Real bug found and fixed during this step

`evidence_cli.py`'s `cmd_list` still read the deleted Phase 1
`identity["name"]` field — `KeyError: 'name'` the moment it was run
against real Phase 2 evidence, since Step 4 only updated `store.py` and its
own tests, not this CLI. Fixed (`identity["uuid"]`); added
`tests/test_evidence_cli.py` (2 tests — this CLI previously had zero
coverage). Included in this step's commit, matching the Phase 1 Step 5
precedent of folding a live-discovered fix into the E2E step that found it.

## Deviations from the plan

None functionally. One operator-error deviation self-corrected immediately
and recorded for the record: the first `cagent-ca sign-server` invocation
used a relative output path from the wrong `cwd` and wrote into a stray
`cagent/.local/cagent-ca/` instead of the intended repo-root
`.local/cagent-ca/`; caught by the next `ls`, moved into place, stray
directory removed. No security impact (both locations are gitignored).

## Exit criteria (from `p2/plan.md`, restated)

1. **An enrolled client on agpc sends a request over mTLS and gets a
   response.** ✅ — Step 5 of the transcript, twice (once before, once
   after the revoke/reactivate cycle).
2. **A revoked certificate is rejected.** ✅ — Step 8 of the transcript,
   `403 forbidden`, immediate.
3. **A real-TLS-stack conformance test passes**, covering valid, revoked,
   expired, unregistered, and UUID-mismatch. ✅ — Step 5a,
   `devtests/test_strategy/test_mtls_conformance.py`, 6/6 passing.

All three Phase 2 exit criteria are met.

## State

`uv run pytest -q` in `cagent/`: **65 passed** (was 63 at end of Step 5a;
+2 `test_evidence_cli.py`). `cagent-api` and this step's OpenCode instance
were stopped after verification. agpc retains its enrolled key/cert/CA
material (intentional — the phase's exit state). The Phase 1 evidence
archive and this phase's two new evidence entries remain under
`~/.local/state/cagent/`. No submodule/root push was performed (per
`.local/localenv_memo.md`, pushing is the user's own step).

## Phase 2 status

All six steps (0, 1, 2, 3, 4, 5a, 5b) and all three roadmap exit criteria
are complete. `cluster_agent` Phase 2 (node authentication / mTLS + one
real node) is done. Phase 3 (distribution + first use-case proof via
Ansible-distributed curl wrapper) is the next roadmap phase, not started.
