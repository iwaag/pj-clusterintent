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

## Phase 1: Bake in the dnsmasq workflow

**Goal: turn the most frequent routine task into a single deterministic command, immediately eliminating AI token spend and non-reproducibility.**

- `nctl render dnsmasq` — fetch desired endpoints from `nintent` via GraphQL and render DHCP reservations / DNS mappings from a Jinja2 template.
- `nctl apply dnsmasq --diff` — show a diff against the current config (dry-run by default), then run the relevant playbook after approval. All Nautobot round-trips and playbook call ordering are hidden internally.
- Define a thin Claude Code skill (`.claude/skills/`) so that "update dnsmasq" always resolves to the same command sequence.

**Exit criteria**: Updating dnsmasq completes in two `nctl` commands, from either a human or AI, with a dry-run diff available for review beforehand.

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
