# Step 3.1 — Freeze the live baseline, evidence policy, and case candidates

Status: complete.

## 1. Baseline

- Parent repository: `54b7aa2` (`p3 plan`).
- nctl: `d33c58e`; nintent: `aa5a052` (`0.9.0`, migration
  `0014_braindump_exchange_diary` already deployed).
- The Phase 2 nctl suite baseline remains 733 passing tests and one existing warning.
- Authenticated `nctl braindump list --json` returned zero rows before this phase's writes.
- The pre-write `nctl drift --json` result used schema `nctl.drift.v1`, with six targets,
  `converged: 2`, `unknown: 4`, and severity summary `error: 6`, `warning: 4`, `info: 5`.

## 2. Candidate/evidence inventory

- Three user-supplied, git-ignored sources were staged under
  `.local/braindump_workspace/sources/`: LAN/DNS policy, machine-placement preferences, and node
  onboarding policy.
- Desired IP ranges already matched the LAN document's three ranges: static infrastructure
  `192.168.0.2–9`, DHCP-reservable `192.168.0.10–199`, and dynamic DHCP `192.168.0.200–250`.
- Desired nodes already named `agdnsmasq`, `aghub`, `agpc`, `agstudio`, and `agbach`; the only
  desired service was `dnsmasq`.
- `agpc` and `agstudio` actual observations were from 2026-06-26. They were treated as stale
  evidence, not proof of the user-described hardware or current workloads.
- Stale service inventory named `prometheus` on `agpc`, and `hatchet`, `nautobot`, `postgres`, and
  `redis` on `agstudio`. None qualified as the Phase 3 unexplained-service case without refresh.

## 3. Evidence handling

- The Nautobot token was resolved only through local configuration/environment handling and was never
  printed in commands, artifacts, or this report.
- Full user prose and full review prose remain in Nautobot and git-ignored local files only. This
  report records IDs, state transitions, and redacted evidence rather than private text.
- No Braindump, desired-state, reconcile, or host write occurred before the baseline was captured.

## Discrepancies

None for Step 3.1.
