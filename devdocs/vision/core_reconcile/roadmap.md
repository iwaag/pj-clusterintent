# core_reconcile Development Roadmap

## Premises

- **Breaking-change phase**: No backward compatibility is required. Schemas, CLI, and API may be broken freely at any phase.
- **Experimental system**: This is not a commercial product. Security only needs to be the bare minimum (LAN-only operation, no plaintext credentials that would actually cause harm, no Nautobot tokens committed to Git).
- Design satisfaction and future extensibility are prioritized over implementation cost.

## Vision

Treat the drift between the desired state held by `nintent` and the actual state held by `nodeutils` / Nautobot, as computed by a **Reconciliation Engine, as the single source of truth**, and distribute its output in three directions:

1. **Humans** — a dashboard that visualizes drift (a static HTML page for now, a 3D/voice UI in the future)
2. **AI** — reads structured JSON to diagnose issues and handle exceptions
3. **Automation** — a CLI, `nctl`, that deterministically executes standard workflows (e.g. generating dnsmasq config)

AI's role should be upgraded from "an executor that assembles steps every time" to "an exception handler that calls `nctl` and only reads the drift JSON when reconciliation fails to converge."

### Design conventions for a future UI (common across all phases)

To keep future frontends (a 3D scene rendered by a game engine, voice commands, etc.) as "just another subscriber of the reconciliation engine's output," follow these from the start:

1. **Separate the core library from a thin CLI** — put the implementation in a Python library (`nctl_core`); the CLI is a thin wrapper. In the future, the same core can be wrapped by an HTTP/WebSocket API.
2. **JSON schema for all output** — every command returns a stable schema via `--json`. Human-readable text is just a rendering of that JSON.
3. **Event logs for long-running operations** — long-running operations like reconcile get an operation ID and emit events (`started` / `step_completed` / `drift_resolved` / `failed`, etc.) as JSON Lines. For now the consumers are a log file and AI; in the future a realtime UI can attach to the same stream.

---

## Phase 0: Scaffolding

**Goal: establish the skeleton of `nctl` and the design conventions.**

- Create `nctl/` at the root of the parent repository (pj-clusterintent) (an `nctl_core` library plus a CLI entry point, managed with uv).
- Build shared layers for the Nautobot GraphQL client, reading nodeutils dumps, and configuration (`nctl.toml`: Nautobot URL/token reference, inventory path, etc.).
- Define the common JSON output format and event log format (JSON Lines + operation ID), and enforce it on every subsequent command.
- Implement `nctl status` (checks Nautobot connectivity and submodule state) as the first command, serving as the reference implementation of the conventions.

**Exit criteria**: `nctl status --json` works with a stable schema. The event log format is documented.

## Phase 0-EX1: Expose nintent models via Nautobot GraphQL

**Goal: make the desired state readable through the same GraphQL endpoint as the actual state, before any command starts consuming it.**

- Register GraphQL types for `nintent`'s models (desired nodes, endpoints, etc.) so they join Nautobot's standard `/api/graphql/` schema — no separate endpoint. This lets Phase 2 fetch desired + actual as a single joined query (e.g. a device with its interfaces, IPs, and desired endpoints) instead of stitching REST pagination results in `nctl`.
- Division of labor from here on: **reads = GraphQL** (unified, one client in `nctl_core`), **writes = REST** (Nautobot GraphQL is read-only; the existing intent-catalog ViewSets stay for writes such as the Phase 3 reconciliation status field).
- Switch `nctl status`'s intent-catalog probe from the REST endpoint to a GraphQL schema introspection check (do the intent types exist?).

**Exit criteria**: Desired endpoints are retrievable from `/api/graphql/` in one query alongside core DCIM/IPAM objects, and `nctl status` verifies their presence via the GraphQL schema.

## Phase 1: Bake in the dnsmasq workflow (move rendering into nctl, retire the Job-export path)

**Goal: turn the most frequent routine task into a single deterministic command, and fix the responsibility split while doing so — the ledger (`nintent`) stores and exposes desired state; the workflow layer (`nctl`) translates it into consumer formats; Ansible only actuates.**

Design decision: dnsmasq conf is an artifact of one specific actuation mechanism, so rendering it is `nctl`'s job, not the ledger's. Today it lives in `nintent`'s "Export dnsmasq Records" Nautobot Job, and `ansible_agdev` retrieves it through Job-run/poll/file-proxy plumbing. That entire path is replaced, not wrapped: keeping the Job would leave rendering coupled to Celery/file-proxy machinery that Phase 2's drift engine cannot reuse synchronously.

- `nctl render dnsmasq` — fetch desired endpoints, IP ranges, and intent evaluations via GraphQL (the Phase 0-EX1 types) and render the conf deterministically in `nctl_core` as a pure function (ported from `nintent`'s `dnsmasq.py`, output-compatible). The same function becomes the "desired conf" side of Phase 2 drift.
- `nctl apply dnsmasq` — render, then run the deploy-only playbook in check+diff mode (dry-run by default); `--yes` applies for real. Long-running, so it gets an operation ID and JSON Lines events.
- **Cleanup of the old path**: delete `ExportDnsmasqRecords` and `dnsmasq.py` (+ its tests, after porting them) from `nintent`; reduce `ansible_agdev`'s `deploy_nintent_dnsmasq_records.yml` to a deploy-only playbook that takes a pre-rendered conf path (the Job-orchestration play and its file-proxy/polling plumbing are deleted).
- Define a thin Claude Code skill (`.claude/skills/`) so that "update dnsmasq" always resolves to the same command sequence.
- Recorded as follow-up debt, not Phase 1 scope: `Export Ansible Hosts Intent` (and the other export Jobs) should eventually migrate to `nctl` under the same "consumers render, the ledger stores" principle.

**Exit criteria**: Updating dnsmasq completes in two `nctl` commands, from either a human or AI, with a dry-run diff available for review beforehand. dnsmasq rendering exists in exactly one place (`nctl_core`), and no dnsmasq Job/file-proxy plumbing remains in `nintent` or `ansible_agdev`.

Detailed plan: [p1/plan.md](p1/plan.md)

## Phase 2: Reconciliation Engine (drift engine)

**Goal: consolidate desired-vs-actual drift computation into a single engine.**

- Cross-reference the three sources — `nintent` desired state, Nautobot actual state, and `nodeutils` dumps — and determine `converged / drifting / converging / unknown` status per node/service.
- Output the content of each difference (e.g. "desired has a DHCP reservation, but actual has no MAC registered") as a structured JSON list of diffs: `nctl drift [--host X] --json`.
- Turn `nintent`'s model definitions into a shared library to avoid duplicating the desired-state schema (since this is the breaking-change phase, don't hesitate to restructure `nintent` itself if needed).
- Make the judgment rules pluggable (a structure where comparators can be registered per resource type).

**Exit criteria**: `nctl drift --json` returns cluster-wide drift in a single run, and AI can read just that to explain the current state.

## Phase 3: Visualization dashboard

**Goal: let humans grasp the situation from a single screen without touring Nautobot.**

- `nctl dashboard` — generate static HTML from the drift JSON produced in Phase 2. Show the whole cluster as green/yellow/red, with drift details in prose on click.
- Regenerate on every reconcile/drift run. Hosting can be a local file or LAN-only static serving; no auth needed.
- On the Nautobot side, add only a reconciliation status field and a link to the dashboard to the `nintent` plugin (accept that Nautobot is the ledger and visualization lives outside it).

**Exit criteria**: The dashboard alone is enough to understand cluster health and drift details.

## Phase 4: Automatic convergence loop

**Goal: go from drift detection to resolution in one command. Make AI the exception handler.**

- `nctl reconcile [host]` — run drift detection → execute the necessary playbooks in the correct order → re-inspect via nodeutils → confirm convergence, all as a single operation. Record every step in the event log.
- Register other routine workflows besides dnsmasq (initial node setup, service placement, etc.) as reconcilers one by one.
- On failure or non-convergence, stop and leave behind the operation's event log and drift JSON. Establish an operational flow where AI reads these to diagnose (build out a diagnostic skill).
- Optional: periodic drift detection and notification via cron/scheduler.

**Exit criteria**: The happy path converges via `nctl reconcile` with no human or AI involvement; only failure cases go to AI diagnosis.

## Phase 5: Realtime API layer (groundwork for a future UI)

**Goal: make it possible for advanced UIs (3D, voice, etc.) to connect as "new subscribers."**

- `nctl serve` — an HTTP API wrapping `nctl_core` (state snapshot, drift fetch, reconcile trigger) plus a WebSocket for streaming events. Minimal auth (roughly a single token) is enough.
- Start firming up the event schema toward a freeze (from this phase onward, start caring about compatibility as UI development begins).
- As a reference implementation, build one live-updating browser dashboard (a dynamic version of Phase 3) that subscribes over WebSocket, to validate the subscriber API in practice.

**Exit criteria**: An external process can fetch current state, issue change requests, and subscribe to progress events, all via the API. A game-engine-built UI can be built on top of this API without any backend changes.

---

## Rationale for phase ordering

- Phase 1 comes before the drift engine because the dnsmasq workflow is where the payoff (token spend, reproducibility) shows up fastest.
- Phases 2–3 solve the "situational awareness" problem; Phase 4 generalizes and solves the "routine workflow" problem.
- Phase 5 doesn't need to start until the future UI plans are concrete, but if the Phase 0 design conventions are followed, the added cost will be limited to a thin API layer.
