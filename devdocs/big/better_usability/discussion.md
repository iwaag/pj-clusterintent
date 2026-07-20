# Better Usability — Problem Analysis and Guiding Principles

Status: discussion / design rationale (no implementation prescribed here — see `roadmap.md`
for the phased plan, and future `devdocs/small/*` docs for concrete implementation plans).

This document records a class of usability problems discovered while verifying scenarios 1–3
(`.local/scenario*.txt`) end to end against the live dev cluster on 2026-07-20, and the design
principles proposed to address them. The individual bugs found along the way (e.g. the
`observe_node` service-target batching bug, fixed in `devdocs/small/fix1/`) are out of scope
here; this is about the deeper structural issue they exposed.

## The core finding

**nintent is supposed to describe the state the user wants. In practice, fields that exist only
to satisfy the implementation (how Ansible connects, how the renderer classifies a host) sit at
the same level, with the same weight, as fields that express genuine user intent.** There is no
distinction — in the data model, in the UI, or in the documented workflow — between "information
only a human can decide" and "information the system needs but could derive or default."

The user wants: *"dnsmasq should run on agdnsmasq."* That is the whole intent. Everything about
*how* Ansible reaches the host, *what* OS it expects, *which* endpoint is the connection path —
these are mechanism, and the user does not (and should not need to) care about them until the
rare moment the automatic choice is wrong. Today the system forces all of it to be hand-entered,
up front, as a precondition for the intent to have any effect.

This matters especially because the stated target audience is a single person running a personal
cluster (see `roadmap.md` premises), where the person writing the intent is also the approver,
the operator, and the only stakeholder. Bureaucratic ceremony that might be justified in a large
organization with separated duties is pure friction here.

## Concrete examples observed

### Example 1 — placement `config` silently never applies (the dnsmasq loopback footgun)

`agdnsmasq` runs dnsmasq. We declared the service and placement exactly as the "add a basic
service" recipe (`nctl/docs/add-a-basic-service.md`) describes, with `config = {}`. The daemon
came up listening on `127.0.0.1` only (the role default in
`ansible_agdev/roles/dnsmasq_server/defaults/main.yml`), so the node — whose own
`/etc/resolv.conf` points at its LAN IP `192.168.0.2` — could not resolve any name against its
own dnsmasq. Every hostname-based operation on that host failed (`apt`, `uv` download, `ping
<name>`), which masqueraded as "the whole host has no network" until we traced it.

The fix required setting `config.listen_addresses = ["192.168.0.2"]`. But we then discovered that
**setting it in the ledger has no effect through the normal path**: placement `config` is only
mapped to Ansible variables by `nctl render production` (`nctl/src/nctl_core/production/
composer.py`), and that renderer only includes nodes whose `lifecycle` is `approved`/`active`
(`PRODUCTION_ELIGIBLE_LIFECYCLES`). `agdnsmasq` is `planned`. So the config value the user set
was silently ignored; only a manual `ansible-playbook … -e '{"dnsmasq_listen_addresses": …}'`
made it take effect. **User intent was recorded and then discarded with no error, no warning,
nowhere.**

(We added a defensive `127.0.0.1`-always-included fix to the role template so this specific
footgun can't recur, but that treats the symptom, not the structural cause.)

### Example 2 — `lifecycle` defaults to `planned`, with no promotion path

`DesiredNode.lifecycle` (`nintent/nautobot_intent_catalog/models.py:296`) defaults to `planned`.
Nothing in the entire system ever promotes it — there is no `nctl` command, no nintent UI
affordance, no automatic bump on first successful reconcile. In the live dev cluster, **all 5
nodes are `planned`; not one has ever been promoted.** The `planned → approved → active`
progression is documented as intentional (`devdocs/functions/service_placement/plan.md:189-192`:
"planned nodes remain eligible for bootstrap discovery but do not enter the production
inventory") but the *promotion* half of that workflow was never built.

The result is a designed gate that, in practice, everything is stuck behind. Its only live
consequence is Example 1: config never applies because no node is `active`. For a single
operator who is their own approver, a mandatory `plan → approve` step is time and effort spent
for no benefit — the approval decision was already made when they typed the intent.

### Example 3 — `DesiredNodeOperationalConfig`: required, undefaulted, unautomated, uncreated

This is the sharpest instance of the core finding. `DesiredNodeOperationalConfig`
(`nintent/nautobot_intent_catalog/models.py:605-707`) is a separate 1:1 model holding *pure
mechanism*:

- `actual_state_policy` (required, no default) — whether to observe the host for real
- `connection_path` (required, no default) — `local` vs `tailscale`
- `expected_host_os` / `declared_host_os` — OS classification, cross-validated by `clean()` and a
  DB `CheckConstraint`
- `local_endpoint` / `tailscale_endpoint` — which `DesiredEndpoint` to connect through
- `ansible_port`, `power_control`, `is_laptop` — these *do* have sensible defaults, and are the
  model done right

`composer.py` reads these directly to build `ansible_host`, OS group membership, WoL vars, etc.
None of it is user intent — it is "how the automation reaches and treats this box."

Three compounding problems:

1. **No creation path.** No recipe creates it alongside the node; no `nctl` command creates it;
   it exists only as a Django-admin/shell hand-INSERT. In the live cluster there are **0 rows** —
   for any node. Nobody has ever created one.
2. **No defaults where it matters.** `actual_state_policy` and `connection_path` are required
   with no default, so the model can't be trivially auto-created — yet both are almost always
   derivable: a node with exactly one endpoint has an obvious connection path; a node observed by
   nodeutils has a known OS.
3. **Its absence is a global landmine.** If a node *is* production-eligible (`active`/`approved`)
   but has no operational config, `composer.py:185` raises `ContractError`, which
   `production_render.py` turns into a whole-envelope failure — **`nctl render production` fails
   for the entire cluster, not just that node**, and the previous `production.yml` is left
   untouched. Today `lifecycle=planned` accidentally hides this by keeping nodes out of scope; the
   moment we default `lifecycle` to `active` (Example 2's fix), forgetting the operational config
   turns from a silent no-op into a cluster-wide render outage.

So the one piece of information that is *most* purely mechanism is also the one that is *most*
demanded of the user, *least* helped by tooling, and *most* destructive when omitted.

## Guiding principles

### Principle 1 — Classify every field into three tiers, and treat them differently

1. **Intent** — only a human can decide it. *"This node exists."* *"dnsmasq runs here."* These
   are the reason nintent exists. Keep them required, keep them front-and-center.
2. **Derived** — the system can compute it safely from information it already has. Connection
   path from the node's single endpoint; OS from the last nodeutils observation; production
   eligibility from "the user asked for this, and it's a real host." These should be **computed,
   not demanded** — absent explicit input, derive them; never block on them.
3. **Override** — the system *cannot* safely guess, but the case is rare. Non-standard SSH port,
   Wake-on-LAN, forcing a specific OS the observation contradicts. These should have **safe
   defaults** and be touched only when the exception actually applies. `ansible_port`,
   `power_control`, `is_laptop` already work this way — the goal is to bring every mechanism field
   up to this standard.

The test for which tier a field belongs to: *"If the user never thought about this, is there a
right answer the system could pick?"* If yes, it is Derived or Override, never Intent.

### Principle 2 — Mechanism should be derived or defaulted, surfaced only on genuine need

The `DesiredNodeOperationalConfig` fields are the canonical example. The target end-state: a user
declares a node and a placement, and the system fills in connection/OS/policy automatically from
the endpoint and from observed state — creating the operational config (or making it unnecessary
as a separate required row) without the user ever seeing it, unless they deliberately override.

### Principle 3 — Never discard recorded intent silently

Example 1's worst property was not that the config didn't apply — it's that it *looked like it
should have* and there was no signal anywhere that it hadn't. Any time the system ignores,
overrides, or defers a value the user recorded, that must be visible: in `nctl drift`, in the
render report, in `nctl status` — somewhere the user (or their AI agent) will see it. Derived
values should be *labeled as derived* ("OS inferred from observation; not explicitly set") so a
wrong guess is discoverable rather than mysterious.

### Principle 4 — Fail locally, not globally

A single node's missing/invalid mechanism data must skip that one node with a structured reason
(the existing `_host_actual_skip_reasons` pattern in `composer.py`), never abort the whole render
via `ContractError`. Global-failure blast radius (Example 3) is itself a usability defect: one
half-configured host should not be able to take down everyone else's inventory. This is a
prerequisite for safely defaulting `lifecycle` to `active`.

### Principle 5 — The single-operator case is the primary case; secure/multi-role is a future main route, not a current tax

Defaulting to "planned, awaiting approval" implements a separation-of-duties model
(author ≠ approver) that only pays off when those are different people with different
permissions — which would require a substantial build (distinct edit vs. approve permissions,
per-user authz, an audit trail). That is a legitimate *future* direction and the state machine
(`planned/approved/active/deprecated/retired`) is worth keeping as the skeleton for it. But it
must not tax the person using this today. Default to "the moment I express intent, the system
acts on it"; keep `planned` as a formal state that only gains teeth once real
approval/permission machinery is built. Do not make today's single user pay the ceremony cost of
a multi-user feature that does not yet exist.

## Non-goal / caveat: don't over-rotate into invisible automation

Full auto-derivation carries the mirror-image risk of Example 1: instead of "the system didn't
do what I said," you get "the system did something I never said." The loopback bug was partly a
*missing* override; blanket inference can equally produce surprises the user can't see coming.
The reconciliationary answer, consistent with the core_reconcile vision
(`devdocs/vision/core_reconcile/roadmap.md`), is Principle 3: derive aggressively, but make every
derived choice legible in the drift/status output so a wrong inference is always discoverable.
For the single-operator, LAN-only context this trade — convenience now, with visible derivations
— is the right one; a stricter posture can come with the future secure/multi-user route.
