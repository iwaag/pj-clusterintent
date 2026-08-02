# cluster_agent Development Roadmap

References: [refined_idea.txt](refined_idea.txt), [opinion.md](opinion.md)

## Premises

- **Experimental environment**: an experimental cluster with no production
  workload. Security only needs to be the bare minimum (VPN/LAN-only reach, no
  plaintext credentials that would actually cause harm, no secrets in Git or
  in binaries). No strict operational procedures or audit requirements are
  imposed.
- **Breaking-change phase**: no backward compatibility is required. API
  schemas, the authentication scheme, and the CLI may be broken freely at any
  phase.
- Detailed plans are written per phase as `pN/plan.md` when each phase starts.
  This document fixes only the overall skeleton and the useful information
  already known at planning time.

## Vision

Make the cluster-agent on the command node (an agent session whose working
directory is pj-clusterintent) reachable from two entrances:

1. Requests about cluster resources/services from nodes inside the cluster
   (node-agents or development-assist agents). Example: "I want S3-compatible
   storage" → the cluster-agent reads drift/relations and returns how to use
   an existing service.
2. Human conversation from a browser on a VPN-connected smartphone or similar.

There are four building blocks. refined_idea.txt is authoritative for the
detailed discussion.

- **cluster-agent API**: the only external entrance. HTTPS REST,
  asynchronous by default (returns a request ID). Owns authentication, node
  identification, session ownership, input limits, and auditing.
- **Dedicated OpenCode instance**: a cluster-agent-only process,
  configuration, and session storage area. Loopback-only, placed strictly
  behind the API.
- **Auth ledger**: owns "which public key of which DesiredNode is currently
  trusted". nintent keeps owning DesiredNode existence/validity (preserve the
  separation).
- **Distributed client**: the thin entry point each node uses to call the
  API. Grow it in the order curl → wrapper → (only if needed) Go CLI.

## The few rules common to all phases

Only these three prohibitions. Everything else is at the implementer's
discretion.

1. **No cluster mutation directly triggered by a node-originated request.**
   Initial responses are limited to reads (status/drift/relations/guidance)
   and plan presentation. Desired-state writes and `reconcile --yes` go
   through human approval. Before being a security requirement, this is the
   execution boundary against prompt injection.
2. **Never expose OpenCode directly to the VPN/LAN.** The external entrance
   is always the API only.
3. **No secrets (tokens, private keys) in Git, in binaries, or in request
   evidence.** Use public identifiers such as fingerprints in evidence.

## Phase 1: contract freeze + loopback MVP

**Goal: freeze the API contract in a short document and exercise the whole
contract on the command node's loopback only.**

- Contract document: resources (request / session / turn), state transitions,
  error shapes, identity classes (define only the node/human distinction;
  authentication comes later), and the initial authorization rule (reads +
  plans only). Freeze it before implementing.
- Stand up the dedicated OpenCode instance for the cluster-agent and drive
  session creation → follow-up turns → status retrieval → cancel through the
  API (a small HTTP server), using curl on the command node. No TLS and a
  stub for authentication are fine.
- Leave durable evidence per request/turn (same shape as `nctl ops`: an ID
  directory plus JSONL or JSON). Building it in the same shape from the start
  is cheaper than adding auditing later.

Hints:

- The first research item is OpenCode's server-mode/session API. The existing
  node-agent configuration (under ansible_agdev) is a proven sample.
- Serialize turns within one session. Turns involving reconcile can be
  globally serialized for now (agents share a single working directory).
- On process restart, an in-flight request should be reported as
  "interrupted", not "unknown" — keep request state on the evidence side.
- Implementation language for the API is free. Matching nctl (Python/uv)
  reuses the development environment, but do not build it into nctl itself
  (nctl serve was built once, went unused, and was deleted — see
  remove_unused_surfaces). The difference this time is that concrete
  consumers (node-agents, the smartphone) exist first.

**Exit criteria**: a frozen contract document exists; with curl alone, a new
request → response retrieval → session continuation → cancel all work; and
evidence remains on disk.

## Phase 2: node authentication (mTLS) + one real node

**Goal: implement per-node keys + mTLS and pass a request from one real
node.**

- Enrollment follows the procedure in refined_idea.txt (generate the key on
  the node → collect the CSR over the SSH path → approve/sign bound to the
  DesiredNode UUID → place the certificate). A self-signed local CA on the
  command node is fine.
- Implement the auth ledger (UUID ↔ public key / certificate serial,
  revocation state). Its storage is the implementer's choice, but always
  attach a CLI surface a human can use to enumerate and inspect it (there is
  a precedent of leaving DesiredWorkspace without a GUI for phases).
- Connect-time checks: certificate valid + not revoked + registered in the
  ledger + the corresponding DesiredNode is currently allowed to make
  requests. A node whose UUID disappeared via `nctl prune` becomes invalid
  automatically — write one sentence in the contract stating that prune
  doubles as de-facto revocation.
- Prepare one conformance test using the real TLS stack (an mTLS analogue of
  `devtests/test_strategy/test_openssh_conformance.py`: real keys and a
  loopback server, verifying not-revoked / revoked / expired / unregistered /
  UUID-mismatch paths). Avoid mock-only mTLS tests (README_DEV lesson 2).

Hints:

- The first real node should be agpc (reachability confirmed;
  agbach/agdnsmasq being unresponsive is a known state).
- Never trust a node slug/ID in the request body as authentication
  information. Identity comes from the certificate only.
- From the curl stage on, pass bodies/tokens via `--data @file` and similar,
  not command-line arguments.

**Exit criteria**: an enrolled client on agpc sends a request over mTLS and
gets a response. A revoked certificate is rejected. The conformance test
passes.

## Phase 3: distribution + first use-case proof

**Goal: distribute the wrapper to all target nodes with Ansible and make the
"I want S3" style of request actually usable by a node-agent.**

- Distribute a curl wrapper (a thin shell script is enough) with the fixed
  URL and TLS settings via an Ansible role. Do not build the Go CLI yet.
- Keep the wrapper's command surface minimal: new request from stdin /
  continue with a session ID / get status. Minimize what the node-agent
  prompt has to be taught.
- Add how to call the cluster-agent to the node-agent instructions
  (prompt/AGENTS equivalent), and confirm that a real node-agent-originated
  request gets "guidance to an existing service" back. `nctl relations
  --json` can be used as-is as the material for that guidance (the
  service-binding graph plus the unreferenced-service list, computed fresh on
  every call).

**Exit criteria**: at least one node-agent sends a resource question through
the wrapper and receives useful guidance, with the example preserved as
evidence.

## Phase 4: the human (smartphone) entrance

**Goal: a human can converse with the cluster-agent from a browser over the
VPN.**

- Humans are a separate identity class from nodes. Simple authentication
  under a single-operator assumption is fine (one client certificate issued
  to the human device, or passkey/basic auth — implementer's choice). Always
  record in evidence which entrance/identity a request came from.
- The UI is a minimal chat screen (send request, show response, list
  sessions). Add SSE here, and only here, once progress display for long
  turns is actually wanted.
- The human entrance can become the entry point that holds approval authority
  (performing the "human approval" of common rule 1 through this entrance
  completes plan review → approval from outside the house). Implementing the
  approval flow itself is not required in this phase, though — conversation
  working comes first.

**Exit criteria**: from a browser on a VPN-connected smartphone, a new
request and follow-up turns work and the responses are readable.

## Phase 5 (only when needed): hardening and convenience

Start only after a concrete complaint appears. Candidates only:

- Go CLI (if the wrapper proves insufficient; no embedded URLs/secrets —
  resolve them from configuration)
- Mutation-approval flow from the human entrance (plan presentation →
  approval → execution as API)
- Per-node rate limits, session TTL/limits
- Workspace/project-level identity (connect with DesiredWorkspace; consider
  only together with a real separation mechanism such as Unix users)
- Attachment upload

## Out of scope (restated from refined_idea.txt)

Full remote terminal over WebSocket, WebRTC, storing conversation history in
the Nautobot ledger, unrestricted automatic cluster mutation from
node-agents, and a general-purpose agent-orchestration platform.
