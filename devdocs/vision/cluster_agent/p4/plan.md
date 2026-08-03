# cluster_agent Phase 4 Plan: the human (smartphone) entrance

References: [roadmap.md](../roadmap.md), [refined_idea.txt](../refined_idea.txt),
[p1/contract.md](../p1/contract.md), [p2/contract.md](../p2/contract.md),
[p3/report5.md](../p3/report5.md), [p3/e2e_transcript.md](../p3/e2e_transcript.md)

## Goal

A human can converse with the cluster-agent from a browser on a
VPN-connected smartphone: authenticate as the `human` identity class, start
a new request, read the response, and send follow-up turns in the same
session. The `human` class finally gets a real entrance (it has existed as
an enum value with no authentication path since Phase 2).

## Exit criteria (from the roadmap, restated)

1. From a browser on a VPN-connected smartphone, a new request works and
   the response is readable.
2. Follow-up turns in the same session work from that browser.
3. Evidence records which entrance/identity class each request came from —
   a human request and a node request are distinguishable in
   `cagent-evidence` output.

## Scope and freedom

Experimental cluster, breaking-change phase. Only the three roadmap-wide
prohibitions apply:

1. Reads + plan presentation only, for humans exactly as for nodes. The
   human entrance may *later* become the approval entrance (Phase 5), but
   this phase adds no mutation or approval path.
2. OpenCode stays on 127.0.0.1. The human entrance is a new surface of the
   cagent API process, never a proxy port to OpenCode itself.
3. No secrets in Git, binaries, or evidence. The human credential (token,
   password hash, or device cert — whatever is chosen) lives under
   `.local/` or `~/.local/state/cagent/`, both gitignored.

Everything else — the human authentication mechanism, whether the UI is
one HTML file or several, SSE vs. polling, the exact identity/evidence
shape — is the implementer's choice, recorded in the contract delta and
step reports. Breaking the p2 evidence/identity shape is allowed;
**breaking the node-facing API on :8788 is allowed but discouraged**,
because the wrapper is already distributed to agpc and any change there
costs another live Ansible round for zero Phase 4 value.

## Recommended shape (advice, not mandate)

The roadmap leaves human auth open (device cert / passkey / basic auth).
Planning-time investigation strongly favors **a second HTTPS listener with
server-only TLS + a single static bearer token/cookie**, because:

- The node entrance (`main.py:_build_ssl_context`) uses
  `verify_mode = CERT_REQUIRED` on its socket — there is no way to make
  one listener require a client cert for nodes but not for humans.
  Two listeners (e.g. :8788 mTLS for nodes, :8789 server-TLS for humans)
  keep the node path byte-identical and give the human path its own
  authenticator. `server.build_server()` already takes `authenticate` and
  `ssl_context` as parameters, so the second listener is a second
  `build_server()` call sharing the same `store`/`worker`/`opencode`
  objects, with the second `serve_forever()` on a plain `threading.Thread`.
  The `authenticate(handler) -> Identity` seam (`server.py:make_handler`)
  was built for exactly this: add a `TokenAuthenticator` next to
  `CertAuthenticator`, no handler changes needed for auth itself.
- Installing a client certificate on a smartphone browser is genuinely
  painful (iOS: config profile + Safari-only quirks; Android: per-session
  prompts) and buys nothing under the single-operator assumption. Passkeys
  (WebAuthn) need a stable trusted origin and far more code. A random
  token generated once on the command node, stored gitignored, and entered
  once on the phone (login form → cookie, or a bookmarkable `?token=` that
  the page immediately moves into localStorage/cookie) is proportionate.
- Serve the chat UI from the same human listener (`GET /` returns one
  static HTML file with inline JS). Same-origin means no CORS work at all.

If the implementer prefers a human device certificate instead, that is
in-scope — `cagent-ca` can sign it with a `urn:clusterintent:human:<name>`
SAN and the ledger can hold it — but record why the mobile-install cost is
worth it.

## Steps

House style: one step at a time, `p4/reportN.md` + one commit per step.
Steps 0–3 touch only the command node (local scratch — approval-free).
Step 4 needs the user personally (their phone + VPN), so it is a pause
point by nature; it still mutates nothing.

### Step 0 — Contract delta + reachability facts

Write `p4/contract.md` as a delta over p2 (same style p2 used over p1),
freezing before implementation:

- The human authentication mechanism and where its credential lives.
- The `Identity` shape for humans. Current
  `store.Identity` is `{class, uuid, cert_serial}` (`store.py:34`); humans
  have neither. Suggested: rework to a class-tagged shape, e.g.
  `{"class": "node", "uuid", "cert_serial"}` vs.
  `{"class": "human", "name": "<operator label>"}`. This changes evidence
  bytes — breaking, allowed, note it explicitly.
- Session visibility/ownership for humans. Node rule stays: a node sees
  only its own sessions. Suggested human rule (single operator): the human
  may **list and read all sessions** (useful now for inspection, later for
  approval review) but may only **continue** sessions the human class
  created. Whatever is chosen, state it — the current per-UUID filter in
  `_list_sessions`/`_get_request` is where it lands.
- Which listener serves what: UI routes (`GET /`, static assets if any)
  exist only on the human listener; `/requests`, `/sessions/...` exist on
  both listeners with the entrance's own authenticator.
- SSE: per the roadmap, add it only here and only if actually wanted.
  Recommended: **start with polling** — the wrapper already proved
  poll-until-terminal works over minutes-long turns; a 2–3 s poll from a
  phone is fine. If the chat feels bad in Step 2, add one
  `GET /requests/{id}/events` SSE endpoint then, and record it in the
  contract; do not build it speculatively.

Also pin down the one live fact this phase hangs on: **the URL the phone
dials.** The VPN is Tailscale with MagicDNS: every enrolled machine,
including the phone, reaches the command node as bare `agstudio` (no
domain suffix needed). So the expected human URL is
`https://agstudio:8789`. The server cert's SANs are currently
`agstudio.local` + `192.168.0.100` (p3/plan.md) — **bare `agstudio` is not
among them**, so plan a `cagent-ca sign-server` re-issue adding
`--dns agstudio` (keep the existing SANs so agpc's LAN dial stays valid).
This is non-destructive: it just writes new
`server_cert.pem`/`server_key.pem`; nodes trust the CA, not the leaf, so
agpc's wrapper is unaffected. Verify in Step 0 that `agstudio` actually
resolves from a Tailscale peer (e.g. from agpc or the phone) and note the
tailnet IP in the report; adding it as an `--ip` SAN too is harmless
insurance.

Deliverable: `p4/contract.md` frozen + report0 with the confirmed URL.

### Step 1 — Human entrance in cagent-api

- `TokenAuthenticator` (or the chosen mechanism) in `auth.py`, returning
  the new human `Identity`. Constant-time comparison
  (`hmac.compare_digest`), token read from a file path env var
  (suggested: `CAGENT_HUMAN_TOKEN_FILE`, default
  `~/.local/state/cagent/human_token`), refuse to start the human listener
  if the file is missing/empty — mirror `start.sh`'s refuse-don't-fallback
  pattern for the OpenAI key.
- Second listener in `main.py` (suggested `CAGENT_HUMAN_PORT`, default
  8789) with server-only TLS reusing the same server cert/key, sharing
  store/worker/opencode. Log both entrances at startup.
- `Identity` rework in `store.py` + evidence, per the frozen contract.
  Update `CertAuthenticator` accordingly. No compatibility shim for the
  old evidence identity shape (README_DEV breaking-change rule); old
  evidence directories on disk stay readable as history — do not migrate
  them, just make the startup scan tolerant enough not to crash on them
  (or note that pre-p4 evidence is read with the old shape).
- Ownership/visibility rules from the contract in `server.py`.
- Unit tests via the existing fake-authenticate seam (`tests/fakes.py`):
  token accepted/rejected/missing-file, human identity recorded in
  evidence, human vs. node session visibility, human cannot continue a
  node session (and vice versa). `uv run pytest` in `cagent/` green.

### Step 2 — Minimal chat UI

One static HTML file (inline CSS/JS, no framework, no build step) served
by the human listener:

- Login/token entry once, then: textarea + send (`POST /requests`),
  response area polling `GET /requests/{id}` every ~2–3 s until terminal,
  follow-up sends to `POST /sessions/{sid}/requests`, and a session list
  from `GET /sessions` to reopen past conversations
  (`GET /sessions/{sid}/requests` renders the history).
- Show the request state while waiting — turns take 18 s (trivial) to
  ~221 s (tool-heavy, p2 measurement); a phone screen with no feedback for
  three minutes reads as broken. Render `queued/running` explicitly and
  keep the poll going; `interrupted` and `failed` must be readable, not
  blank.
- Keep it phone-first: viewport meta, big tap targets, response text in a
  scrollable `<pre>`/markdown-ish block. Nothing else.
- Local proof: run the stack on the command node, open the UI in a desktop
  browser against `https://localhost:8789` (self-signed warning is fine
  locally), do one full ask → poll → answer → follow-up round. Save the
  browser exchange in report2.

### Step 3 — Conformance test + gates

- Extend `devtests/test_strategy/test_mtls_conformance.py` (or add a
  sibling module reusing its throwaway CA/server fixture): real TLS,
  both listeners up in one process, asserting at minimum — node mTLS path
  still works unchanged; human listener accepts the good token and
  rejects a bad/absent one; a client cert is *not* required on the human
  listener; the node listener still refuses cert-less connections; human
  and node identities land in evidence in their contract shapes; the
  cross-class ownership rule holds. This is the README_DEV lesson-2 test
  (real stack, not mock TLS) for the new surface.
- Update the README_DEV command-matrix row (new case count, or new gate
  file row if it became one) and `cagent/README.md` (new env vars, start
  order, the two entrances, token setup).

### Step 4 — Smartphone proof over VPN (needs the user)

The exit-criteria run. Nothing here mutates the cluster; the pause is
because only the user has the phone and the VPN profile.

1. Generate the human token file; re-issue the server cert with the
   `agstudio` SAN added (expected from Step 0, since the current cert
   only carries `agstudio.local` + `192.168.0.100`).
2. Start the stack (`./cagent/opencode/start.sh`, then `cagent-api` — now
   with both listeners).
3. User, on the VPN-connected smartphone browser: open the human URL,
   accept/install the CA or click through the self-signed warning
   (experimental env — click-through is acceptable; installing
   `ca_cert.pem` on the device is nicer and the cert is public, but iOS
   full-trust toggling is fiddly and **optional**), enter the token, ask
   one real resource question, read the answer, send one follow-up turn.
4. On the command node: `cagent-evidence list/show` must show those
   requests with the human identity, alongside older node-identity
   requests from p2/p3. Save the exchange (question, answer, evidence IDs,
   a phone screenshot if convenient) as `p4/e2e_transcript.md`.
5. Stop the manually started processes (house pattern). Exit state: code +
   UI committed, token file and any re-issued server cert remain on the
   command node.

## Useful facts collected at planning time

- **The auth seam already exists**: `server.make_handler(store, opencode,
  worker, authenticate)` treats authentication as an injected callable
  returning `store.Identity`; `build_server(...)` takes `ssl_context` per
  listener. The human entrance is mostly wiring, not surgery. The only
  genuinely shared mutable objects are `Store` (already lock-guarded) and
  the single `Worker` queue — global turn serialization across both
  entrances comes for free, which is desired (one OpenCode, one workdir).
- **Do not touch the node entrance if avoidable**: agpc's wrapper +
  `client.conf` dial `https://agstudio.local:8788` with the p2 cert
  material. Keeping :8788 semantics frozen means Phase 4 needs zero
  Ansible/SSH and zero re-enrollment.
- **VPN reachability is Tailscale + MagicDNS**: enrolled machines
  (agstudio, the nodes, the phone) reach each other by bare hostname —
  the phone dials `https://agstudio:8789`. No mDNS/`.local` dependency
  and no IP memorization on the phone.
- **Server cert re-issue is cheap and node-safe**: `cagent-ca sign-server
  --dns/--ip` writes a new leaf; clients validate against `ca_cert.pem`.
  Only the SAN-vs-dialed-URL match matters per client — the phone dialing
  `agstudio` and agpc dialing `agstudio.local` can be different SANs of
  the same cert, so issue one cert carrying all three
  (`agstudio`, `agstudio.local`, `192.168.0.100`).
- **`http.server` + SSE don't mix well**: each SSE stream would pin a
  thread in `ThreadingHTTPServer` and complicate shutdown. This is a real
  reason to prefer polling in Step 2, and if SSE is truly wanted later,
  to consider it the moment to leave stdlib HTTP — not this phase.
- **Turn latency**: ~18 s trivial, ~221 s tool-heavy (p2), ~80 s for the
  p3 real question. Poll loops and any client-side timeouts must think in
  minutes.
- **OpenAI key precondition**: the OpenCode instance now requires
  `OPENAI_API_KEY` or `.local/cagent/openai_api_key` (`start.sh` refuses
  otherwise) — the Step 2/4 stack start needs it present.
- **Evidence CLI**: `cagent-evidence list/show` is the inspection surface;
  Step 4's identity check uses it as-is.
- **Known cluster state**: agstudio is the command node; agpc reachable
  and enrolled (UUID `c82421c3-...`); agbach/agdnsmasq unresponsive is
  long-standing and expected; none of them participate in this phase.
- **Roadmap note on approval authority**: the human entrance is the
  designated future holder of mutation approval (Phase 5 candidate).
  Nothing to build now, but when choosing the identity shape and session
  visibility in Step 0, avoid choices that would make "human reviews a
  plan produced in a node's session" impossible later — the suggested
  read-all/continue-own rule keeps that door open.

## Out of scope for Phase 4

Mutation/approval flow (Phase 5), Go CLI, per-node rate limits, session
TTL/limits, workspace-level identity, attachment upload, WebSocket/remote
terminal, storing conversation history in Nautobot, multi-operator user
management, and SSE unless Step 2 concretely demands it.
